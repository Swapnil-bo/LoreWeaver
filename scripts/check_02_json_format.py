import httpx, json, asyncio

DM_SCHEMA = {
    "type": "object",
    "properties": {
        "narrative": {"type": "string"},
        "choices": {
            "type": "array", "minItems": 2, "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "text":               {"type": "string"},
                    "order_chaos_shift":  {"type": "number", "minimum": -20, "maximum": 20},
                    "harm_harmony_shift": {"type": "number", "minimum": -20, "maximum": 20}
                },
                "required": ["text", "order_chaos_shift", "harm_harmony_shift"]
            }
        },
        "npc_updates": {"type": "array"},
        "world_event": {"type": ["string", "null"]}
    },
    "required": ["narrative", "choices"]
}

async def test_json_format(n: int = 20):
    failures = 0
    for i in range(n):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "mistral:7b-instruct",
                          "prompt": "You are a dungeon master. Describe a mysterious forest and give 2 choices.",
                          "stream": False, "format": DM_SCHEMA}
                )
            result = json.loads(r.json()["response"])
            assert "narrative" in result and "choices" in result
            assert len(result["choices"]) >= 2
            print(f"  [{i+1}/{n}] Valid JSON — {len(result['choices'])} choices")
        except Exception as e:
            failures += 1
            print(f"  [{i+1}/{n}] FAIL: {e}")
    print(f"\nResult: {n-failures}/{n} passed.")

asyncio.run(test_json_format())
