import httpx, json, asyncio, time

async def test_live_stream():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model":  "mistral:7b-instruct",
        "prompt": "Describe a dark fantasy tavern in 3 sentences.",
        "stream": True,
        "format": {
            "type": "object",
            "properties": {
                "narrative": {"type": "string"},
                "choices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text":               {"type": "string"},
                            "order_chaos_shift":  {"type": "number"},
                            "harm_harmony_shift": {"type": "number"}
                        },
                        "required": ["text", "order_chaos_shift", "harm_harmony_shift"]
                    },
                    "minItems": 2,
                    "maxItems": 3
                }
            },
            "required": ["narrative", "choices"]
        }
    }

    token_count = 0
    first_token_time = None
    start = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    if first_token_time is None:
                        first_token_time = time.time() - start
                    token_count += 1
                    print(token, end="", flush=True)
                if chunk.get("done"):
                    total = time.time() - start
                    tps = token_count / total
                    print(f"\n\nFirst token: {first_token_time:.2f}s")
                    print(f"Total: {total:.2f}s | Tokens: {token_count} | Speed: {tps:.1f} tok/s")
                    if tps < 10:
                        print("SLOW — likely running on CPU. Check `ollama ps`.")
                    break

asyncio.run(test_live_stream())
