import asyncio

import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")
_write_queue: asyncio.Queue = asyncio.Queue()


async def chroma_write_worker():
    """
    Single worker: serializes all ChromaDB writes.
    asyncio.to_thread() offloads each blocking call to thread pool.
    Event loop stays free — WebSockets never drop during writes.
    """
    while True:
        collection_name, operation, kwargs = await _write_queue.get()
        try:
            col = chroma_client.get_collection(collection_name, embedding_function=None)
            await asyncio.to_thread(getattr(col, operation), **kwargs)
        except Exception as e:
            print(f"[ChromaDB] {collection_name}.{operation}: {e}")
        finally:
            _write_queue.task_done()


async def queue_write(collection: str, operation: str, **kwargs) -> None:
    """Fire-and-forget: enqueue write, return immediately."""
    await _write_queue.put((collection, operation, kwargs))
