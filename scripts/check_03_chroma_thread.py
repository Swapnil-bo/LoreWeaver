import asyncio, chromadb, time


async def test_chroma_nonblocking():
    client = chromadb.PersistentClient(path="./test_chroma")
    col    = client.get_or_create_collection("test", embedding_function=None)

    async def timed_write(i):
        fake_vec = [float(i) / 5.0] * 384  # same dim as all-MiniLM-L6-v2
        start = time.time()
        await asyncio.to_thread(col.add,
            embeddings=[fake_vec],
            documents=[f"Test document {i}"],
            ids=[f"test_{i}_{time.time()}"]
        )
        return time.time() - start

    times = await asyncio.gather(*[timed_write(i) for i in range(5)])
    print(f"Write times: {[f'{t:.3f}s' for t in times]}")
    max_t = max(times)
    print("Non-blocking confirmed" if max_t < 2.0 else f"Blocking detected ({max_t:.2f}s)")


asyncio.run(test_chroma_nonblocking())
