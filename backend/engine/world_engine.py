import time

import aiosqlite

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from db.sqlite_store import DB_PATH
from engine.alignment_engine import apply_alignment_shift, get_effective_disposition
from engine.combat_engine import summarize_and_clear_combat_log
from models.narrative import DMResponse
from rag.collections import queue_write

# Re-export so other modules can import from world_engine (matches verify command)
__all__ = ["summarize_and_clear_combat_log", "process_world_event", "process_turn_result"]

NARRATIVE_SUMMARY_INTERVAL = 5


async def process_world_event(
    world_event: str,
    session_id: str,
    region_id: str,
    ws_manager,
):
    """
    Flaw #28 fix: world_event chain — SQLite -> ChromaDB -> WS broadcast.
    Called when DMResponse.world_event is not None.
    """
    # Store in ChromaDB for semantic retrieval
    await queue_write("world_lore", "add",
        documents=[world_event],
        ids=[f"event_{session_id}_{int(time.time())}"],
        metadatas=[{"session_id": session_id, "region_id": region_id, "type": "world_event"}],
    )

    # Store in SQLite for recency
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO narrative_summaries (session_id, summary, created_at) VALUES (?,?,?)",
            (session_id, f"[WORLD EVENT] {world_event}", time.time()),
        )
        await db.commit()

    # Broadcast map update so frontend can reflect the change
    await ws_manager.broadcast(session_id, {
        "type":      "map_update",
        "region_id": region_id,
        "event":     world_event,
    })


async def process_npc_updates(npc_updates: list, session_id: str):
    """Store NPC mood changes and memories in ChromaDB."""
    for update in npc_updates:
        await queue_write("npc_memory", "add",
            documents=[update.new_memory],
            ids=[f"npc_{update.npc_id}_{session_id}_{int(time.time())}"],
            metadatas=[{
                "npc_id":     update.npc_id,
                "session_id": session_id,
                "mood_change": update.mood_change,
                "turn":       int(time.time()),
            }],
        )


async def maybe_summarize_narrative(
    session,
    narrative_text: str,
    ws_manager,
):
    """Every N turns, summarize recent narrative into ChromaDB + SQLite."""
    session.current_scene.turn_count += 1
    if session.current_scene.turn_count % NARRATIVE_SUMMARY_INTERVAL != 0:
        return

    # Store the narrative chunk as a summary
    await queue_write("session_narrative", "add",
        documents=[narrative_text[:1500]],
        ids=[f"narr_{session.session_id}_{session.current_scene.turn_count}"],
        metadatas=[{
            "session_id":    session.session_id,
            "turn":          session.current_scene.turn_count,
            "summary_level": "periodic",
        }],
    )

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO narrative_summaries (session_id, summary, created_at) VALUES (?,?,?)",
            (session.session_id, narrative_text[:500], time.time()),
        )
        await db.commit()


async def process_turn_result(
    dm_response: DMResponse,
    chosen_shift: dict,
    session,
    ws_manager,
):
    """
    Full post-turn pipeline:
    1. Apply alignment shift (dampened)
    2. Process NPC updates -> ChromaDB
    3. Handle world_event if present -> SQLite + ChromaDB + broadcast
    4. Periodic narrative summary every 5 turns
    """
    # 1. Alignment shift
    session.world_state = apply_alignment_shift(session.world_state, chosen_shift)

    # 2. NPC updates
    if dm_response.npc_updates:
        await process_npc_updates(dm_response.npc_updates, session.session_id)

    # 3. World event chain
    if dm_response.world_event:
        await process_world_event(
            dm_response.world_event,
            session.session_id,
            session.current_scene.region_id,
            ws_manager,
        )

    # 4. Periodic narrative summary
    await maybe_summarize_narrative(session, dm_response.narrative, ws_manager)
