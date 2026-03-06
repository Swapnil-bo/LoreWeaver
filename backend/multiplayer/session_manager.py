import asyncio
import time
import uuid

from fastapi import WebSocket
from pydantic import BaseModel

from db.sqlite_store import (
    DB_PATH,
    get_last_narrative_sqlite,
    load_session_from_sqlite,
    serialize_session_to_sqlite,
)


class PlayerIdentity(BaseModel):
    player_id:       str
    reconnect_token: str
    display_name:    str
    session_id:      str | None = None


# ── In-memory registries ──────────────────────────────────────────────────────
_active_sessions:    dict[str, "GameSession"] = {}
_reconnect_registry: dict[str, PlayerIdentity] = {}
_last_activity:      dict[str, float] = {}
SESSION_TTL = 15 * 60  # 15 minutes


def touch_session(session_id: str):
    _last_activity[session_id] = time.time()


def get_session(session_id: str):
    return _active_sessions.get(session_id)


def set_session(session_id: str, session):
    _active_sessions[session_id] = session
    touch_session(session_id)


async def send_json(ws: WebSocket, data: dict):
    await ws.send_json(data)


# ── 10.2: Player Identity + Reconnection ─────────────────────────────────────

async def handle_connect(ws: WebSocket, token: str | None):
    if token and token in _reconnect_registry:
        identity = _reconnect_registry[token]
        await resume_player_session(ws, identity)
    else:
        identity = PlayerIdentity(
            player_id       = str(uuid.uuid4()),
            reconnect_token = str(uuid.uuid4()),
            display_name    = "Unnamed Hero",
        )
        _reconnect_registry[identity.reconnect_token] = identity
        await send_json(ws, {"type": "identity_issued", "identity": identity.model_dump()})
    return identity


async def resume_player_session(ws: WebSocket, identity: PlayerIdentity):
    """
    v4 FIX: Full state sync on reconnect — player never loads blank UI.
    v5 addition: active_vote includes deadline_ts so countdown resumes correctly.
    """
    session = _active_sessions.get(identity.session_id)
    if not session:
        session = await load_session_from_sqlite(identity.session_id)
        if not session:
            await send_json(ws, {"type": "session_expired"})
            return
        _active_sessions[identity.session_id] = session

    if identity.player_id in session.players:
        session.players[identity.player_id].is_connected = True

    # Import here to avoid circular dep — vote_system references session_manager
    from multiplayer.vote_system import get_active_vote

    active_vote = get_active_vote(session.session_id)

    await send_json(ws, {
        "type":            "full_state_sync",
        "world_alignment": session.world_state.model_dump(),
        "quadrant":        session.world_state.quadrant,
        "players":         {pid: p.model_dump() for pid, p in session.players.items()},
        "current_phase":   session.phase.value,
        "last_narrative":  await get_last_narrative_sqlite(session.session_id),
        "active_vote":     {**active_vote.model_dump(),
                            "deadline_ts": active_vote.deadline} if active_vote else None,
    })
    touch_session(session.session_id)


# ── 10.3: Session Memory Pruner (v5 Fix) ─────────────────────────────────────

async def session_pruner():
    """
    v5 FIX: Background task — prevents infinite RAM bleed on long sessions.
    Inactive sessions serialized to SQLite and deleted from memory dict.
    Reloaded from SQLite on next player message.
    Runs every 5 minutes.
    """
    while True:
        await asyncio.sleep(300)
        now     = time.time()
        expired = [sid for sid, last in _last_activity.items()
                   if now - last > SESSION_TTL]
        for sid in expired:
            session = _active_sessions.get(sid)
            if session:
                await serialize_session_to_sqlite(session)
                del _active_sessions[sid]
                del _last_activity[sid]
                print(f"[Session] Pruned {sid} to SQLite — freed memory")
