import asyncio

import httpx
from pydantic import BaseModel

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from engine.dm_engine import _ollama_lock, stream_dm_response
from multiplayer.ws_manager import WebSocketManager
from rag.collections import queue_write

# Module-level manager instance — set by main.py at startup
ws_manager = WebSocketManager()

# ── Vote registries ───────────────────────────────────────────────────────────
_active_votes: dict[str, "VoteSession"] = {}


class VoteSession(BaseModel):
    vote_id:         str
    session_id:      str
    choices:         list[str]
    votes:           dict[str, int] = {}
    deadline:        float
    resolved:        bool = False
    party_leader_id: str


class VoteResult(BaseModel):
    winning_index:  int
    vote_counts:    dict[int, int]
    dissenters:     list[str]
    was_tie_broken: bool


def get_vote(vote_id: str) -> VoteSession | None:
    return _active_votes.get(vote_id)


def get_active_vote(session_id: str) -> VoteSession | None:
    for v in _active_votes.values():
        if v.session_id == session_id and not v.resolved:
            return v
    return None


def register_vote(vote: VoteSession):
    _active_votes[vote.vote_id] = vote


async def resolve_vote(vote: VoteSession, session) -> VoteResult:
    connected = {pid for pid, p in session.players.items() if p.is_connected}
    valid     = {pid: idx for pid, idx in vote.votes.items() if pid in connected}
    if not valid:
        return VoteResult(winning_index=0, vote_counts={}, dissenters=[], was_tie_broken=True)

    tally: dict[int, int] = {}
    for idx in valid.values():
        tally[idx] = tally.get(idx, 0) + 1

    max_v   = max(tally.values())
    winners = [i for i, c in tally.items() if c == max_v]
    tie     = len(winners) > 1
    winning = valid.get(vote.party_leader_id, winners[0]) if tie else winners[0]

    return VoteResult(
        winning_index  = winning,
        vote_counts    = tally,
        dissenters     = [pid for pid, i in valid.items() if i != winning],
        was_tie_broken = tie,
    )


# ── Constraint #13: finalize_vote MUST call stream_dm_response at the end ─────

async def finalize_vote(vote_id: str, result: VoteResult, session):
    vote         = get_vote(vote_id)
    winning_text = vote.choices[result.winning_index]
    vote.resolved = True

    # Log winning action in ChromaDB
    await queue_write("player_history", "add",
        documents=[f"Party chose: {winning_text}"],
        ids=[f"vote_{vote_id}_win"],
        metadatas=[{"player_id": "party", "turn": session.current_turn,
                    "region": session.current_scene.region_id,
                    "moral_tag": "collective_choice", "session_id": session.session_id}])

    # v4 FIX: Log dissent per dissenting player — DM remembers forever
    for player_id in result.dissenters:
        name = session.players[player_id].display_name
        await queue_write("player_history", "add",
            documents=[f"{name} dissented and felt conflicted about '{winning_text}'. Complied reluctantly."],
            ids=[f"vote_{vote_id}_dissent_{player_id}"],
            metadatas=[{"player_id": player_id, "turn": session.current_turn,
                        "region": session.current_scene.region_id,
                        "moral_tag": "dissent", "session_id": session.session_id}])

    await ws_manager.broadcast(session.session_id, {
        "type": "vote_result",
        "winning_index": result.winning_index,
        "vote_counts": result.vote_counts,
    })
    await send_dissenter_narratives(result.dissenters, winning_text, session.session_id)

    # v6 FIX (Constraint #13): Trigger DM narration after vote.
    # Without this the game halts forever — players see the vote result
    # but the DM never narrates the outcome.
    if not session.is_generating:
        session.is_generating = True
        try:
            synthetic_action = f"The party collectively decided to: {winning_text}"
            context = await build_game_context(session, synthetic_action)
            await stream_dm_response(context, ws_manager, session.session_id)
        finally:
            session.is_generating = False


async def start_vote_timer(vote_id: str, session_id: str, timeout: float = 30.0):
    await asyncio.sleep(timeout)
    vote = get_vote(vote_id)
    if vote and not vote.resolved:
        from multiplayer.session_manager import get_session
        session = get_session(session_id)
        if session:
            result = await resolve_vote(vote, session)
            await finalize_vote(vote_id, result, session)


async def send_dissenter_narratives(dissenters: list[str], chosen_text: str, session_id: str):
    if not dissenters:
        return
    prompt = (
        f'The party chose: "{chosen_text}". '
        f"Write one sentence of inner conflict for a dissenting player."
    )
    # Constraint #4: all Ollama calls through _ollama_lock
    async with _ollama_lock:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    text = r.json().get("response", "You follow reluctantly.").strip()
    for player_id in dissenters:
        await ws_manager.send_to_player(session_id, player_id,
            {"type": "inner_conflict", "text": text})


async def build_game_context(session, action: str) -> dict:
    """Minimal context builder for vote-triggered DM response."""
    from rag.retriever import assemble_context
    rag = await assemble_context(session.session_id, action, session.current_scene.region_id)
    return {
        "world":         session.world_state,
        "region":        session.current_scene,
        "player_action": action,
        "rag":           rag,
    }
