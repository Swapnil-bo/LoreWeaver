import asyncio
import random
import re
import time

import aiosqlite
import httpx

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from engine.dm_engine import _ollama_lock, get_combat_narration
from models.combat import CombatState, EnemyBehavior, EnemyState
from rag.collections import queue_write

# ── Section 9.2: Sliding window — only last 5 log entries go into the prompt ──
COMBAT_LOG_WINDOW = 5


def get_combat_context_for_prompt(combat_state: CombatState) -> str:
    """
    Only last 5 entries injected into LLM prompt.
    Sliding window keeps token cost constant regardless of combat length.
    """
    return "\n".join(combat_state.log[-COMBAT_LOG_WINDOW:])


# ── Section 9.3: Server-authoritative dice (Constraint #14) ──────────────────
# Client NEVER generates random numbers for game logic.
# Server rolls -> sends dice_result -> frontend animates to server value.

def roll_dice(expression: str) -> tuple[int, list[int]]:
    match = re.fullmatch(r"(\d*)d(\d+)([+-]\d+)?", expression.strip().lower())
    if not match:
        raise ValueError(f"Invalid dice expression: {expression}")
    count    = int(match.group(1) or 1)
    sides    = int(match.group(2))
    modifier = int(match.group(3) or 0)
    rolls    = [random.randint(1, sides) for _ in range(count)]
    return max(0, sum(rolls) + modifier), rolls


def roll_attack(modifier: int, target_ac: int) -> tuple[bool, int, bool]:
    roll, _ = roll_dice("1d20")
    is_crit = roll == 20
    hit     = is_crit or (roll != 1 and (roll + modifier) >= target_ac)
    return hit, roll, is_crit


def enemy_ai_turn(enemy: EnemyState, players: list, world) -> dict:
    alive = [p for p in players if p.hp > 0]
    if not alive:
        return {"action": "idle"}

    behavior = enemy.behavior
    if world.order_chaos > 50:
        behavior = EnemyBehavior.tactical
    elif world.order_chaos < -50:
        behavior = EnemyBehavior.reckless
    if world.harm_harmony > 60 and random.random() < 0.15:
        return {"action": "surrender", "enemy_id": enemy.enemy_id}

    target = {
        EnemyBehavior.reckless:  random.choice(alive),
        EnemyBehavior.tactical:  min(alive, key=lambda p: p.hp),
        EnemyBehavior.defensive: min(alive, key=lambda p: p.hp),
        EnemyBehavior.erratic:   random.choice(alive),
    }[behavior]

    hit, roll, is_crit = roll_attack(2, target.stats.ac)
    damage, _ = roll_dice(enemy.damage_dice) if hit else (0, [])
    if is_crit:
        damage *= 2

    return {
        "action": "attack",
        "enemy_id": enemy.enemy_id,
        "target_player_id": target.player_id,
        "hit": hit,
        "damage": damage,
        "roll": roll,
        "is_crit": is_crit,
    }


# ── Section 9.2: Post-combat summary ─────────────────────────────────────────

async def summarize_and_clear_combat_log(combat_state: CombatState, session_id: str):
    """
    Called when combat ends, before returning to exploration.
    Stores summary in BOTH ChromaDB (semantic) AND SQLite (recency).
    Clears log from memory.
    """
    if not combat_state.log:
        return

    prompt = (
        "Summarize this combat in exactly 2 sentences, "
        f"preserving outcomes and dramatic moments:\n{chr(10).join(combat_state.log)}"
    )
    # Constraint #4: all Ollama calls go through _ollama_lock
    async with _ollama_lock:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    summary = r.json().get("response", "A battle was fought.").strip()

    # Store in ChromaDB for semantic search
    await queue_write("session_narrative", "add",
        documents=[summary],
        ids=[f"combat_{combat_state.combat_id}"],
        metadatas=[{"session_id": session_id, "summary_level": "combat"}]
    )

    # Store in SQLite for recency fetch
    async with aiosqlite.connect("loreweaver.db") as db:
        await db.execute(
            "INSERT INTO narrative_summaries (session_id, summary, created_at) VALUES (?,?,?)",
            (session_id, summary, time.time())
        )
        await db.commit()

    combat_state.log.clear()


# ── Section 9.3: Server-authoritative combat action processing ────────────────

async def process_combat_action(
    acting_player_id: str,
    action: dict,
    combat_state: CombatState,
    session,
    ws_manager,
):
    """
    Server-authoritative dice sequence:
    1. Roll on server (source of truth)
    2. Send dice_result to ALL players immediately
    3. Short delay so frontend animation plays (~1.5s CSS transition)
    4. Stream combat narration AFTER animation resolves
    """
    # Step 1: server rolls
    hit, roll, is_crit = roll_attack(modifier=2, target_ac=8)
    damage_rolls = []
    damage       = 0
    if hit:
        damage, damage_rolls = roll_dice(
            combat_state.enemies[0].damage_dice if combat_state.enemies else "1d6"
        )
        if is_crit:
            damage *= 2

    action_result = {
        "actor":   acting_player_id,
        "hit":     hit,
        "roll":    roll,
        "is_crit": is_crit,
        "damage":  damage,
    }

    # Step 2: broadcast dice result first — frontend starts animation immediately
    await ws_manager.broadcast(session.session_id, {
        "type":         "dice_result",
        "player_id":    acting_player_id,
        "d20":          roll,
        "damage_rolls": damage_rolls,
        "is_crit":      is_crit,
        "hit":          hit,
    })

    # Step 3: wait for dice animation to complete
    await asyncio.sleep(1.5)

    # Step 4: stream narration AFTER animation resolves
    narration = await get_combat_narration(action_result, session.world_state)
    combat_state.log.append(narration)

    await ws_manager.broadcast(session.session_id, {
        "type":      "combat_update",
        "actor":     acting_player_id,
        "result":    action_result,
        "narration": narration,
    })
