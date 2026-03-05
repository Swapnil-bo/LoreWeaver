import asyncio
import json
import re

import httpx
from json_repair import repair_json

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from models.narrative import DM_RESPONSE_SCHEMA, DMResponse, MoralChoice

# Constraint #4: Global Ollama serialization lock — one LLM request at a time.
# Prevents VRAM OOM on RTX 3050 from concurrent KV cache duplication.
_ollama_lock = asyncio.Lock()

DM_SYSTEM_PROMPT = """
You are LoreWeaver, a masterful Dungeon Master running a living fantasy world.

WORLD STATE:
- Alignment: {mood_descriptor}
- Order/Chaos: {order_chaos:.0f} | Harmony/Harm: {harm_harmony:.0f}
- Current Region: {region_name} — {region_description}
- Let "{mood_descriptor}" flavor EVERY description.

ACTIVE NPCs:
{npc_list_with_dispositions}

WORLD LORE (relevant):
{lore_chunks}

PLAYER HISTORY (includes dissent records):
{player_history_chunks}

NPC MEMORIES:
{npc_memory_chunks}

RECENT NARRATIVE (last 2 turns — always current):
{recent_narrative}

OLDER NARRATIVE CONTEXT:
{old_narrative}

RULES:
1. 2-3 vivid atmospheric paragraphs. Max 350 words.
2. Exactly 2-3 choices with real moral weight.
3. alignment shifts: numbers -20 to 20. Never strings.
4. NPCs remember their histories.
5. RECENT NARRATIVE is authoritative — if it says building is on fire, it is on fire.
6. Reference past dissent when dramatically appropriate.
7. No markdown fences. JSON only.
"""


def build_prompt(context: dict) -> str:
    rag = context.get("rag", {})
    world = context["world"]
    region = context["region"]
    npcs = context.get("npc_dispositions", "None present")

    return DM_SYSTEM_PROMPT.format(
        mood_descriptor=world.mood_descriptor,
        order_chaos=world.order_chaos,
        harm_harmony=world.harm_harmony,
        region_name=region.name,
        region_description=region.description,
        npc_list_with_dispositions=npcs,
        lore_chunks="\n".join(rag.get("lore", [])) or "None available",
        player_history_chunks="\n".join(rag.get("history", [])) or "None available",
        npc_memory_chunks="\n".join(rag.get("npc_memories", [])) or "None available",
        recent_narrative="\n".join(rag.get("recent_narrative", [])) or "None yet",
        old_narrative="\n".join(rag.get("old_narrative", [])) or "None yet",
    ) + f"\n\nPlayer action: {context['player_action']}"


async def stream_dm_response(
    context: dict,
    ws_manager: "WebSocketManager",
    session_id: str,
) -> DMResponse:
    prompt       = build_prompt(context)
    full_buffer  = ""
    in_narrative = False
    narr_done    = False

    async with _ollama_lock:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/generate", json={
                "model":   OLLAMA_MODEL,
                "prompt":  prompt,
                "stream":  True,
                "format":  DM_RESPONSE_SCHEMA,
                "options": {"num_ctx": 3200, "temperature": 0.8, "top_p": 0.9}
            }) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    full_buffer += token

                    if not in_narrative and '"narrative"' in full_buffer:
                        in_narrative = True

                    if in_narrative and not narr_done:
                        if token and token not in ['{', '}', '"narrative"', ':"']:
                            await ws_manager.broadcast(session_id, {
                                "type": "narrative_stream",
                                "chunk": token, "done": False
                            })

                    if in_narrative and not narr_done and '"choices"' in full_buffer:
                        narr_done = True
                        await ws_manager.broadcast(session_id, {
                            "type": "narrative_stream", "chunk": "", "done": True
                        })

                    if chunk.get("done"):
                        break

    return validate_dm_response(full_buffer)


def validate_dm_response(raw: str) -> DMResponse:
    """Three-tier fallback — game never crashes."""
    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        return DMResponse.model_validate(json.loads(cleaned))
    except (json.JSONDecodeError, Exception):
        pass

    try:
        return DMResponse.model_validate(json.loads(repair_json(cleaned)))
    except Exception:
        pass

    narrative_match = re.search(r'"narrative"\s*:\s*"(.+?)"', cleaned, re.DOTALL)
    return DMResponse(
        narrative   = narrative_match.group(1) if narrative_match else "The world holds its breath...",
        choices     = [
            MoralChoice(text="Press forward cautiously.",   order_chaos_shift=0,   harm_harmony_shift=5),
            MoralChoice(text="Fall back and reassess.",     order_chaos_shift=5,   harm_harmony_shift=0),
            MoralChoice(text="Act boldly, cost be damned.", order_chaos_shift=-10, harm_harmony_shift=-5),
        ],
        npc_updates = [],
        world_event = None,
    )


async def get_combat_narration(action_result: dict, world: "WorldAlignment") -> str:
    """Short non-streaming call. Uses same _ollama_lock — serialized with DM stream."""
    prompt = (
        f"World: {world.mood_descriptor}. "
        f"Combat result: {json.dumps(action_result)}. "
        f"Write exactly 1-2 sentences narrating this. Respond with ONLY the narration text."
    )
    async with _ollama_lock:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    return r.json().get("response", "The blow lands with a thud.").strip()
