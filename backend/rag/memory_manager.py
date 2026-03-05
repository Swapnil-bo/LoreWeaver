import asyncio

from rag.collections import chroma_client


async def enforce_npc_memory_limit(npc_id: str, max_docs: int = 20):
    col     = chroma_client.get_collection("npc_memory", embedding_function=None)
    results = await asyncio.to_thread(col.get,
        where={"npc_id": npc_id}, include=["metadatas"])
    if len(results["ids"]) > max_docs:
        sorted_ids = sorted(zip(results["ids"], results["metadatas"]),
                            key=lambda x: x[1].get("turn", 0))
        to_delete  = [id_ for id_, _ in sorted_ids[:len(results["ids"]) - max_docs]]
        await asyncio.to_thread(col.delete, ids=to_delete)
