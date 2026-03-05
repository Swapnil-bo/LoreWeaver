import asyncio, httpx, time

async def test_ollama_lock():
    """Verify that 3 concurrent requests are serialized (not parallel)."""
    url = "http://localhost:11434/api/generate"
    lock = asyncio.Lock()
    timings = []

    async def locked_request(i):
        async with lock:
            start = time.time()
            async with httpx.AsyncClient(timeout=60.0) as client:
                await client.post(url, json={
                    "model": "mistral:7b-instruct",
                    "prompt": f"Say the number {i}.",
                    "stream": False
                })
            elapsed = time.time() - start
            timings.append((i, elapsed))
            print(f"  Request {i}: {elapsed:.2f}s")

    start = time.time()
    await asyncio.gather(
        locked_request(1),
        locked_request(2),
        locked_request(3),
    )
    total = time.time() - start

    sum_individual = sum(t for _, t in timings)
    print(f"\nTotal wall time: {total:.2f}s")
    print(f"Sum of individual: {sum_individual:.2f}s")
    print("lock serializes requests" if total > sum_individual * 0.8 else "WARN: requests may be parallel")

asyncio.run(test_ollama_lock())
