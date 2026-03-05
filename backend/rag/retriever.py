import asyncio

import aiosqlite

from rag.embedder import embed
from rag.collections import chroma_client

CHARS_PER_TOKEN = 3.5


def truncate_chunks(query_result: dict, max_tokens: int) -> list[str]:
    max_chars = int(max_tokens * CHARS_PER_TOKEN)
    docs      = query_result.get("documents", [[]])[0]
    result    = []
    total     = 0
    for doc in docs:
        if total + len(doc) > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                result.append(doc[:remaining])
            break
        result.append(doc)
        total += len(doc)
    return result


def expand_query(player_action: str, region: "Region",
                 active_npcs: list["NPC"], world: "WorldAlignment") -> str:
    npc_names = ", ".join(n.name for n in active_npcs) or "none"
    return (f"Region: {region.name}. NPCs present: {npc_names}. "
            f"World alignment: {world.mood_descriptor}. "
            f"Player action: {player_action}")


async def get_recent_narrative_from_sqlite(session_id: str, n: int = 2) -> list[str]:
    async with aiosqlite.connect("loreweaver.db") as db:
        rows = await db.execute_fetchall(
            """SELECT summary FROM narrative_summaries
               WHERE session_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, n)
        )
    return [row[0] for row in rows]


async def assemble_context(
    player_action: str, region: "Region", active_npcs: list["NPC"],
    world: "WorldAlignment", active_player_ids: list[str], session_id: str,
) -> dict:
    query     = expand_query(player_action, region, active_npcs, world)
    query_vec = await embed(query)
    npc_ids   = [n.npc_id for n in active_npcs]

    col_lore      = chroma_client.get_collection("world_lore", embedding_function=None)
    col_history   = chroma_client.get_collection("player_history", embedding_function=None)
    col_npc       = chroma_client.get_collection("npc_memory", embedding_function=None)
    col_narrative = chroma_client.get_collection("session_narrative", embedding_function=None)

    # Constraint #5: asyncio.gather — all queries concurrent
    lore, history, memories, old_narrative, recent_narrative = await asyncio.gather(
        asyncio.to_thread(col_lore.query,
            query_embeddings=[query_vec], n_results=3,
            where={"region": {"$in": [region.region_id, "world"]}}),
        asyncio.to_thread(col_history.query,
            query_embeddings=[query_vec], n_results=3,
            where={"player_id": {"$in": active_player_ids}}),
        asyncio.to_thread(col_npc.query,
            query_embeddings=[query_vec], n_results=2,
            where={"npc_id": {"$in": npc_ids}})
            if npc_ids else asyncio.sleep(0, result={"documents": [[]]}),
        asyncio.to_thread(col_narrative.query,
            query_embeddings=[query_vec], n_results=2,
            where={"session_id": session_id}),
        get_recent_narrative_from_sqlite(session_id, n=2),
    )

    return {
        "lore":             truncate_chunks(lore,          max_tokens=600),
        "history":          truncate_chunks(history,       max_tokens=600),
        "npc_memories":     truncate_chunks(memories,      max_tokens=300),
        "recent_narrative": recent_narrative,
        "old_narrative":    truncate_chunks(old_narrative,  max_tokens=200),
    }
