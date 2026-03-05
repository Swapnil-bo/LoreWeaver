# LoreWeaver — Bulletproof Architectural Blueprint v6 (THE ABSOLUTE FINAL ONE)
> Hardware: RTX 3050 6GB VRAM + 8GB DDR4 RAM — Single Windows Desktop
> 46 flaws identified and resolved across 6 iterations. Lock it. Build it.
> Model confirmed: `mistral:7b-instruct-q3_K_S` · 100% GPU · 4.0 GB VRAM

---

## Complete Changelog (v1 → v5)

| Version | Flaws Fixed |
|---|---|
| v1 → v2 | 22 flaws: missing EnemyState, seed data timing, VRAM budget, fake streaming, React Flow + D3 sync, ChromaDB write corruption, vote edge cases, alignment dampening, character creation, world_event chain, WAL mode, query expansion, NPC eviction, wsStore dispatcher, reconnection protocol, Three.js dice, particle framerate, variable naming, outlines incompatibility, player identity, alignment axis labels, fallback parser |
| v2 → v3 | 5 flaws: live token streaming, outlines→Ollama format param, ChromaDB event loop block, RAM death by IDE, D3 useViewport lag |
| v3 → v4 | 8 flaws: Windows SQLite crash, reconnection state void, CLAUDE.md structure, React render thrash, combat log explosion, sequential RAG queries, ghost dissenter memory wipe, single-machine config |
| v4 → v5 | 8 flaws: exploration race condition, SQLite event loop block, RAG recency blindness, embed() freeze, Ollama concurrency VRAM crash, React Flow node flashing, infinite session RAM bleed, Vite HMR zombie WebSockets |
| v5 → v6 | 4 flaws: client-server dice desync, silent vote (DM never speaks after vote), hanging broadcaster blocks all players, tokenizer freeze in truncate_chunks |

---

## Table of Contents
1. [System Architecture Overview](#1-system-architecture-overview)
2. [Hardware Setup](#2-hardware-setup)
3. [Models to Download](#3-models-to-download)
4. [Pre-Build Checklist — Week 0](#4-pre-build-checklist--week-0)
5. [Seed Data — Built First](#5-seed-data--built-first)
6. [Moral Alignment Axis](#6-moral-alignment-axis)
7. [RAG Pipeline](#7-rag-pipeline)
8. [DM Engine](#8-dm-engine)
9. [Combat Engine](#9-combat-engine)
10. [Multiplayer Architecture](#10-multiplayer-architecture)
11. [Session Memory Management](#11-session-memory-management)
12. [Living World Map Frontend](#12-living-world-map-frontend)
13. [Data Models Reference](#13-data-models-reference)
14. [CLAUDE.md — Vibe Coding Master Prompt](#14-claudemd--vibe-coding-master-prompt)
15. [Folder Structure](#15-folder-structure)
16. [requirements.txt](#16-requirementstxt)
17. [Phase Plan — 15 Days](#17-phase-plan--15-days)
18. [Risk Register — All 42 Flaws](#18-risk-register--all-42-flaws)

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (Windows)                          │
│                                                                      │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │  World Map  │  │  Story Console   │  │  Party + Combat Panel │  │
│  │ (React Flow │  │ (live token      │  │  (HP · inventory ·    │  │
│  │  + D3 canvas│  │  stream via      │  │   turn indicator ·    │  │
│  │  useStoreApi│  │  useRef + rAF    │  │   character creation) │  │
│  │  sync)      │  │  throttle)       │  │                       │  │
│  └──────┬──────┘  └───────┬──────────┘  └──────────┬────────────┘  │
│         └─────────────────┼─────────────────────────┘              │
│                           │  WebSocket                              │
│         ┌─────────────────┴──────────────────────────┐            │
│         │    wsStore.js — MESSAGE_HANDLERS dispatcher  │            │
│         │    ws message → action → gameStore.js        │            │
│         └─────────────────┬──────────────────────────┘            │
└───────────────────────────┼──────────────────────────────────────────┘
                            │ WebSocket (localhost:8000)
┌───────────────────────────┼──────────────────────────────────────────┐
│                   FASTAPI BACKEND (Windows)                          │
│                           │                                          │
│  ┌────────────────────────▼─────────────────────────────────────┐  │
│  │                  Game Session Manager                         │  │
│  │  WebSocket hub · turn order · player registry                │  │
│  │  reconnect tokens · vote timer tasks · full_state_sync       │  │
│  └──────┬───────────┬────────────────┬───────────────────────┘  │  │
│         │           │                │                            │  │
│  ┌──────▼──────┐ ┌──▼─────────┐ ┌───▼──────────────────────┐  │  │
│  │  DM Engine  │ │  Combat    │ │  World State Manager      │  │  │
│  │  (streams   │ │  Engine    │ │  alignment · NPC moods    │  │  │
│  │  tokens     │ │  dice ·    │ │  region states ·          │  │  │
│  │  live via   │ │  turn loop │ │  world_event chain        │  │  │
│  │  Ollama SSE)│ │  enemy AI  │ │  combat log summarizer    │  │  │
│  └──────┬──────┘ └────────────┘ └───────────────────────────┘  │  │
│         │ HTTP SSE (localhost:11434)                             │  │
│  ┌──────▼────────────────────────────────────────────────────┐  │  │
│  │  RAG Pipeline                                              │  │  │
│  │  ChromaDB (asyncio.Queue + asyncio.to_thread)             │  │  │
│  │  4 queries via asyncio.gather() — concurrent, not serial  │  │  │
│  │  sentence-transformers all-MiniLM-L6-v2 (CPU)             │  │  │
│  │  Context Assembler (expand_query + retrieval)             │  │  │
│  └───────────────────────────────────────────────────────────┘  │  │
│                                                                   │  │
│  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  SQLite WAL mode — game saves · sessions · player state    │  │  │
│  └────────────────────────────────────────────────────────────┘  │  │
└──────────────────────────────────────────────────────────────────────┘
                            │ HTTP (localhost:11434)
┌───────────────────────────┼──────────────────────────────────────────┐
│              OLLAMA SERVER (Windows — uses RTX 3050 CUDA)            │
│                                                                      │
│   ollama serve                                                       │
│   └── mistral:7b-instruct (q3_K_S)                                  │
│       ~3.5 GB VRAM  ←  lives entirely in RTX 3050 VRAM              │
│       Does NOT touch DDR4 RAM                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Hardware Setup — Single Windows Machine

### Memory Pool Separation (Why RTX 3050 Wins)

```
RTX 3050 VRAM (6GB) — dedicated:        DDR4 RAM (8GB) — separate:
┌──────────────────────────┐             ┌──────────────────────────┐
│ mistral:7b q3_K_S  3.5GB│             │ Windows OS         3.0GB │
│ KV cache (3200 ctx) 0.6GB│             │ Cursor + IDE       1.5GB │
│ CUDA overhead       0.3GB│             │ Chrome DevTools    1.2GB │
│                          │             │ Vite dev server    0.4GB │
│ Headroom:          1.6GB │             │ FastAPI + Python   0.5GB │
│ ✅ Comfortable           │             │ ChromaDB + embeds  0.7GB │
└──────────────────────────┘             │ ─────────────────────── │
                                         │ Total:             7.3GB │
                                         │ ⚠️ Tight — follow rules  │
                                         └──────────────────────────┘

KEY INSIGHT: LLM lives entirely in VRAM. DDR4 never sees it.
On M1 MacBook, LLM and dev stack fight over the SAME 8GB — constant pressure.
```

### RAM Discipline Rules (Single Machine)

```
Rule 1: Max 3 Chrome tabs while full stack is running
Rule 2: Disable Cursor AI autocomplete during play-testing sessions
Rule 3: Kill Vite dev server when running LLM stress tests
Rule 4: Monitor RAM — alert at >85% usage
```

**RAM monitor (run in a spare terminal):**
```powershell
while ($true) {
    $mem   = Get-CimInstance Win32_OperatingSystem
    $used  = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory)/1MB, 1)
    $total = [math]::Round($mem.TotalVisibleMemorySize/1MB, 1)
    $pct   = [math]::Round(($used/$total)*100)
    $flag  = if ($pct -gt 85) { "⚠️  CLOSE SOMETHING" } else { "✅" }
    Write-Host "RAM: $used GB / $total GB ($pct%) $flag"
    Start-Sleep 3
}
```

---

## 3. Models to Download

**Only 2 models. Nothing else.**

### Model 1 — `mistral:7b-instruct` (Ollama, uses RTX 3050)
```bash
# Install Ollama from https://ollama.com/download/windows
ollama pull mistral:7b-instruct
# Size: ~4.1GB download → ~3.5GB in VRAM at runtime

# Verify GPU is being used (critical)
ollama run mistral:7b-instruct "Say hello."
# In another terminal:
ollama ps
# Must show: PROCESSOR = 100% GPU
# If it shows CPU — CUDA setup is broken, fix before proceeding
```

### Model 2 — `all-MiniLM-L6-v2` (sentence-transformers, uses CPU)
```bash
pip install sentence-transformers

# Auto-downloads ~80MB on first run
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
# Lives in DDR4 RAM on CPU — never touches VRAM
```

### What You Do NOT Need
| Model | Why you might think you need it | Why you don't |
|---|---|---|
| `nomic-embed-text` via Ollama | v1 blueprint used it | Replaced by sentence-transformers |
| `llama3`, `phi3`, `gemma` | Curiosity | Scope creep — ship first |
| Any vision/multimodal model | Might seem cool | Not in scope |

---

## 4. Pre-Build Checklist (Week 0)

**All 6 checkpoints must pass before writing application code.**

### ✅ Checkpoint 1 — Ollama GPU Streaming Verified
```python
# scripts/check_01_streaming.py
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
                    print(f"\n\n✅ First token: {first_token_time:.2f}s")
                    print(f"✅ Total: {total:.2f}s | Tokens: {token_count} | Speed: {tps:.1f} tok/s")
                    if tps < 10:
                        print("⚠️  SLOW — likely running on CPU. Check `ollama ps`.")
                    break

asyncio.run(test_live_stream())
# Target: first token < 2s, speed > 20 tok/s (GPU confirmed)
```

### ✅ Checkpoint 2 — Ollama Native JSON Format (20-call reliability)
```python
# scripts/check_02_json_format.py
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
            print(f"  [{i+1}/{n}] ✅ Valid JSON — {len(result['choices'])} choices")
        except Exception as e:
            failures += 1
            print(f"  [{i+1}/{n}] ❌ FAIL: {e}")
    print(f"\nResult: {n-failures}/{n} passed.")
    print("✅ READY TO BUILD" if failures == 0 else "❌ DO NOT PROCEED — fix JSON issues first")

asyncio.run(test_json_format())
```

### ✅ Checkpoint 3 — ChromaDB Thread Isolation (Non-Blocking)
```python
# scripts/check_03_chroma_thread.py
import asyncio, chromadb, time

async def test_chroma_nonblocking():
    # ── v4 FIX: pysqlite3 override ──────────────────────────────
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    # ─────────────────────────────────────────────────────────────

    client = chromadb.PersistentClient(path="./test_chroma")
    col    = client.get_or_create_collection("test")

    async def timed_write(i):
        start = time.time()
        await asyncio.to_thread(col.add,
            documents=[f"Test document {i}"],
            ids=[f"test_{i}_{time.time()}"]
        )
        return time.time() - start

    times = await asyncio.gather(*[timed_write(i) for i in range(5)])
    print(f"Write times: {[f'{t:.3f}s' for t in times]}")
    max_t = max(times)
    print("✅ Event loop not blocked" if max_t < 2.0 else f"❌ Blocking detected ({max_t:.2f}s)")

asyncio.run(test_chroma_nonblocking())
```

### ✅ Checkpoint 4 — CPU Embedding Speed
```python
# scripts/check_04_embeddings.py
from sentence_transformers import SentenceTransformer
import time

model = SentenceTransformer("all-MiniLM-L6-v2")
queries = [
    "Region: Ironhold. NPCs: Captain Varek. World: mildly tyrannical. Player: I bribe the guard.",
    "Region: Ashenvale. NPCs: Sylara. World: somewhat merciful. Player: I search for herbs.",
    "Region: Whispermarsh. NPCs: One-Eye Mags. World: deeply anarchic. Player: I attack the bandit.",
    "Region: Ironhold. NPCs: Merchant Theron. World: justice. Player: I ask about recent events.",
]

start = time.time()
embeddings = model.encode(queries)
elapsed = time.time() - start
per_query = elapsed / len(queries) * 1000

print(f"✅ {len(queries)} queries embedded in {elapsed:.3f}s ({per_query:.0f}ms each)")
print("✅ FAST ENOUGH" if per_query < 200 else "⚠️  SLOW — check CPU load")
```

### ✅ Checkpoint 5 — Windows SQLite Version
```python
# scripts/check_05_sqlite_version.py
# Run BEFORE installing pysqlite3-binary to confirm the problem exists
import sqlite3
version = tuple(int(x) for x in sqlite3.sqlite_version.split("."))
print(f"sqlite3 version: {sqlite3.sqlite_version}")
if version < (3, 35, 0):
    print("❌ TOO OLD — ChromaDB will crash. Add pysqlite3-binary to requirements.txt")
else:
    print("✅ Version OK — pysqlite3 override still recommended as safety net")
```

### ✅ Checkpoint 6 — Write seed_world.json
See Section 5. Must exist before Day 4.

---

## 5. Seed Data — Built First

> **Non-negotiable. Must exist before Phase 2 (Day 4).**
> Write this during Week 0, not Day 13.

```json
{
  "regions": [
    {
      "region_id": "ironhold",
      "name": "Ironhold",
      "description": "A fortress city of grey stone and iron gates. Law is absolute here. Soldiers patrol every corner, and informants lurk in every tavern.",
      "base_mood": "oppressive",
      "connections": ["ashenvale", "stormgate"],
      "danger_level": 3,
      "map_position": {"x": 150, "y": 200},
      "alignment_modifiers": {"order_bias": 20, "harmony_bias": -10}
    },
    {
      "region_id": "ashenvale",
      "name": "Ashenvale",
      "description": "Ancient forest with silver-barked trees that hum at night. The druids distrust outsiders but protect all living things with fierce devotion.",
      "base_mood": "mysterious",
      "connections": ["ironhold", "whispermarsh"],
      "danger_level": 5,
      "map_position": {"x": 400, "y": 150},
      "alignment_modifiers": {"order_bias": -15, "harmony_bias": 25}
    },
    {
      "region_id": "whispermarsh",
      "name": "Whispermarsh",
      "description": "A fog-choked swampland where bandits and outcasts make their home. No law survives here. Even the wildlife seems angry.",
      "base_mood": "hostile",
      "connections": ["ashenvale", "dawnreach"],
      "danger_level": 8,
      "map_position": {"x": 600, "y": 350},
      "alignment_modifiers": {"order_bias": -30, "harmony_bias": -20}
    }
  ],
  "npcs": [
    {
      "npc_id": "captain_varek",
      "name": "Captain Varek",
      "role": "guard_captain",
      "region": "ironhold",
      "base_disposition": -0.2,
      "personality_tags": ["rigid", "duty-bound", "secretly-conflicted"],
      "backstory": "Varek has enforced Ironhold's laws for 20 years. He once let a child thief go free and has regretted his mercy ever since — or so he tells himself.",
      "alignment_sensitivity": {"order_chaos": 0.8, "harm_harmony": 0.3}
    },
    {
      "npc_id": "sylara",
      "name": "Sylara",
      "role": "druid_elder",
      "region": "ashenvale",
      "base_disposition": 0.1,
      "personality_tags": ["wise", "patient", "tests-outsiders"],
      "backstory": "Sylara has watched three kingdoms rise and fall from her grove. She speaks in riddles not to confuse, but because the truth is always complicated.",
      "alignment_sensitivity": {"order_chaos": 0.2, "harm_harmony": 0.9}
    },
    {
      "npc_id": "mags",
      "name": "One-Eye Mags",
      "role": "bandit_fence",
      "region": "whispermarsh",
      "base_disposition": -0.5,
      "personality_tags": ["cunning", "self-serving", "respects-strength"],
      "backstory": "Mags runs the only safe house in the Marsh. She'll sell your secrets to anyone with coin — unless you've proven you're worth more alive as an ally.",
      "alignment_sensitivity": {"order_chaos": -0.5, "harm_harmony": -0.4}
    },
    {
      "npc_id": "theron",
      "name": "Merchant Theron",
      "role": "traveling_merchant",
      "region": "ironhold",
      "base_disposition": 0.6,
      "personality_tags": ["jovial", "greedy", "information-broker"],
      "backstory": "Theron travels all three regions selling 'exotic goods' (mostly stolen). He knows everyone's secrets and sells them for slightly less than they're worth.",
      "alignment_sensitivity": {"order_chaos": 0.1, "harm_harmony": 0.6}
    }
  ],
  "lore_entries": [
    {
      "lore_id": "the_sundering",
      "title": "The Sundering War",
      "content": "Three hundred years ago, the Sundering War split the realm into its current factions. Ironhold rose from ashes of the old empire. Ashenvale's druids sealed their borders. Whispermarsh became a refuge for those who refused either side.",
      "tags": ["history", "factions", "world"]
    },
    {
      "lore_id": "moral_tide",
      "title": "The Moral Tide",
      "content": "Old scholars speak of an invisible current that flows through the realm, shaped by the collective will of its people. When enough blood is spilled for order, ravens gather on every rooftop. When mercy wins out, wildflowers push through cobblestones overnight.",
      "tags": ["lore", "alignment", "world"]
    }
  ],
  "encounter_templates": [
    {
      "template_id": "road_ambush",
      "name": "Bandit Ambush",
      "regions": ["whispermarsh"],
      "enemies": [
        {
          "enemy_id": "bandit_grunt",
          "name": "Bandit Grunt",
          "hp": 18, "max_hp": 18, "ac": 12,
          "damage_dice": "1d6+2",
          "behavior": "reckless"
        }
      ],
      "intro": "Three figures step from the shadows, blades drawn.",
      "alignment_flavor": {
        "anarchy":  "They snarl like wild animals — no coordination, pure hunger.",
        "tyranny":  "They move in practiced formation. Someone has been training them.",
        "mercy":    "One hesitates, meeting your eye with something like shame.",
        "justice":  "They surrender before the fight begins. 'We're starving,' one admits."
      }
    }
  ]
}
```

---

## 6. Moral Alignment Axis

### 6.1 Unified Naming Convention

```
                ORDER (+100)
                    │
    TYRANNY         │         JUSTICE
  order+ · harm-   │       order+ · harmony+
                    │
HARM ───────────────┼─────────────────── HARMONY
(-100)              │                   (+100)
                    │
    ANARCHY         │         MERCY
  order- · harm-   │       order- · harmony+
                    │
               CHAOS (-100)

Variables — used everywhere, no exceptions:
  order_chaos:  +100 = MAX ORDER    -100 = MAX CHAOS
  harm_harmony: +100 = MAX HARMONY  -100 = MAX HARM/DISCORD
```

```python
# models/alignment.py
from pydantic import BaseModel, Field, computed_field

class WorldAlignment(BaseModel):
    order_chaos:  float = Field(default=0.0, ge=-100.0, le=100.0)
    harm_harmony: float = Field(default=0.0, ge=-100.0, le=100.0)

    @computed_field
    @property
    def quadrant(self) -> str:
        if self.order_chaos >= 0 and self.harm_harmony >= 0:   return "justice"
        elif self.order_chaos >= 0 and self.harm_harmony < 0:  return "tyranny"
        elif self.order_chaos < 0  and self.harm_harmony >= 0: return "mercy"
        else:                                                   return "anarchy"

    @computed_field
    @property
    def intensity(self) -> float:
        return min(100.0, (self.order_chaos**2 + self.harm_harmony**2) ** 0.5)

    @computed_field
    @property
    def mood_descriptor(self) -> str:
        prefix = "deeply " if self.intensity > 70 else "somewhat " if self.intensity > 35 else "mildly "
        return f"{prefix}{self.quadrant}"
```

### 6.2 Capped + Dampened Shift

```python
# engine/alignment_engine.py
MAX_SHIFT_PER_ACTION = 20.0

def apply_alignment_shift(current: WorldAlignment, shift: dict) -> WorldAlignment:
    def dampen(val: float, delta: float) -> float:
        delta      = max(-MAX_SHIFT_PER_ACTION, min(MAX_SHIFT_PER_ACTION, delta))
        resistance = abs(val) / 100.0
        effective  = delta * (1.0 - 0.5 * resistance)
        return max(-100.0, min(100.0, val + effective))

    return WorldAlignment(
        order_chaos  = dampen(current.order_chaos,  shift.get("order_chaos_shift",  0)),
        harm_harmony = dampen(current.harm_harmony, shift.get("harm_harmony_shift", 0)),
    )

def get_effective_disposition(npc: "NPC", world: WorldAlignment) -> float:
    order_inf   = (world.order_chaos  / 100.0) * npc.alignment_sensitivity.get("order_chaos",  0)
    harmony_inf = (world.harm_harmony / 100.0) * npc.alignment_sensitivity.get("harm_harmony", 0)
    raw = npc.base_disposition + (order_inf * 0.3) + (harmony_inf * 0.3)
    return max(-1.0, min(1.0, raw))
```

### 6.3 World Consequence Table

| State | NPC Behavior | Map Visual | Events |
|---|---|---|---|
| **Justice** (order+, harmony+) | Trusting, offer quests freely, warn of danger | Gold light, banners, lush terrain | Festivals, trade caravans, alliances |
| **Tyranny** (order+, harm-) | Fearful, obedient, will inform on players | Grey sky, watchtowers, iron walls | Curfews, inspections, rebellions brewing |
| **Mercy** (chaos-, harmony+) | Free-spirited, chaotic-good, barter over coin | Wild overgrowth, colorful, scattered | Wandering healers, unexpected gifts |
| **Anarchy** (chaos-, harm-) | Hostile, self-serving, ambush-prone | Red fog, ruins, fires, broken roads | Bandit raids, plagues, betrayals |

---

## 7. RAG Pipeline

### 7.1 Embedding — Async Threaded (v5 Fix)

```python
# rag/embedder.py
# v5 FIX: embed() is now fully async.
# SentenceTransformer.encode() is a heavy CPU-bound matrix multiply.
# On an i3: 100-200ms of synchronous execution = event loop frozen.
# During that freeze: no WebSocket pings, no streaming tokens, server appears dead.
# Fix: offload to thread pool via asyncio.to_thread on every call.

from sentence_transformers import SentenceTransformer
import asyncio

_model: SentenceTransformer | None = None

def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def _embed_sync(text: str) -> list[float]:
    """Synchronous inner — never call directly in async context."""
    return get_embedder().encode(text, normalize_embeddings=True).tolist()

async def embed(text: str) -> list[float]:
    """
    Async embed — always use this in FastAPI/WebSocket routes.
    Offloads CPU-bound matrix multiply to thread pool.
    Event loop stays free during the 100-200ms computation.
    """
    return await asyncio.to_thread(_embed_sync, text)
```

### 7.2 ChromaDB Write Queue — Thread-Isolated

```python
# rag/collections.py
# pysqlite3 override happens in main.py BEFORE this file is imported
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
            col = chroma_client.get_collection(collection_name)
            await asyncio.to_thread(getattr(col, operation), **kwargs)
        except Exception as e:
            print(f"[ChromaDB] {collection_name}.{operation}: {e}")
        finally:
            _write_queue.task_done()

async def queue_write(collection: str, operation: str, **kwargs) -> None:
    """Fire-and-forget: enqueue write, return immediately."""
    await _write_queue.put((collection, operation, kwargs))
```

### 7.3 truncate_chunks — Character Ratio (v6 Fix)

```python
# rag/retriever.py
# v6 FIX: NEVER use a real LLM tokenizer in this function.
# Importing transformers tokenizer for Mistral = synchronous CPU-bound
# init + encode = 100-300ms event loop freeze on every player action.
# Same class of bug as embed() before v5 fixed it.
#
# Fix: character ratio. English prose averages ~3.5 chars per token.
# Used in production at major AI labs. Off by 50 tokens on a 600-token
# budget = irrelevant. Blocking the event loop = catastrophic.

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
```

### 7.4 Query Expansion

```python
# rag/retriever.py
def expand_query(player_action: str, region: "Region",
                 active_npcs: list["NPC"], world: "WorldAlignment") -> str:
    """
    Expands short queries before embedding.
    'I attack' → 'Region: Whispermarsh. NPCs: Mags. World: deeply anarchic. Player: I attack'
    Short queries produce poor embeddings — context expansion dramatically improves retrieval.
    """
    npc_names = ", ".join(n.name for n in active_npcs) or "none"
    return (f"Region: {region.name}. NPCs present: {npc_names}. "
            f"World alignment: {world.mood_descriptor}. "
            f"Player action: {player_action}")
```

### 7.4 Context Assembler — Parallel + Hybrid Recency (v5 Fix)

```python
# rag/retriever.py
import asyncio, aiosqlite
from rag.embedder import embed   # ← async version
from rag.collections import chroma_client

async def get_recent_narrative_from_sqlite(session_id: str, n: int = 2) -> list[str]:
    """
    v5 FIX: Pull last N narrative summaries by TIMESTAMP — not by semantic similarity.

    The bug: ChromaDB retrieves by MEANING not TIME.
    'I open the wooden door' on Turn 50 pulls the Turn 2 door scene
    instead of Turn 49 'the building is actively on fire'.
    DM suffers short-term memory loss — narrates calm when everything is burning.

    Fix: Bypass ChromaDB entirely for recent context.
    Pull last 2 summaries by created_at from SQLite.
    Only use ChromaDB for older historical narrative (Turn 10+).
    """
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
    query_vec = await embed(query)    # ← async — event loop free during embed
    npc_ids   = [n.npc_id for n in active_npcs]

    col_lore      = chroma_client.get_collection("world_lore")
    col_history   = chroma_client.get_collection("player_history")
    col_npc       = chroma_client.get_collection("npc_memory")
    col_narrative = chroma_client.get_collection("session_narrative")

    # v4 FIX: asyncio.gather — all 4 ChromaDB queries concurrent (~100ms total vs ~400ms)
    # v5 FIX: 5th task added — hybrid recency fetch from SQLite
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
        asyncio.to_thread(col_narrative.query,    # older historical context only
            query_embeddings=[query_vec], n_results=2,
            where={"session_id": session_id}),
        get_recent_narrative_from_sqlite(session_id, n=2),  # ← always temporally accurate
    )

    return {
        "lore":             truncate_chunks(lore,           max_tokens=600),
        "history":          truncate_chunks(history,        max_tokens=600),
        "npc_memories":     truncate_chunks(memories,       max_tokens=300),
        "recent_narrative": recent_narrative,            # always current — from SQLite
        "old_narrative":    truncate_chunks(old_narrative, max_tokens=200),
    }
```

### 7.5 Memory Lifecycle

```
Player Action
     │
     ├─ IMMEDIATE:       queue_write("player_history", "add", ...)
     │
     ├─ POST RESPONSE:   queue_write("npc_memory", "add", ...)
     │                   enforce_npc_memory_limit(npc_id, max=20)
     │
     ├─ EVERY 5 TURNS:   LLM summarizes →
     │                   queue_write("session_narrative", "add", ...)  [ChromaDB]
     │                   INSERT INTO narrative_summaries (SQLite)      [recency store]
     │
     ├─ ON world_event:  queue_write("world_lore", "add", ...)
     │                   update_region_in_sqlite()
     │                   broadcast("map_update")
     │
     └─ ON dissent:      queue_write("player_history", "add", dissent per player)
```

### 7.6 NPC Memory Eviction

```python
async def enforce_npc_memory_limit(npc_id: str, max_docs: int = 20):
    col     = chroma_client.get_collection("npc_memory")
    results = await asyncio.to_thread(col.get,
        where={"npc_id": npc_id}, include=["metadatas"])
    if len(results["ids"]) > max_docs:
        sorted_ids = sorted(zip(results["ids"], results["metadatas"]),
                            key=lambda x: x[1].get("turn", 0))
        to_delete  = [id_ for id_, _ in sorted_ids[:len(results["ids"]) - max_docs]]
        await asyncio.to_thread(col.delete, ids=to_delete)
```

---

## 8. DM Engine

### 8.1 Ollama Lock — Prevents VRAM Explosion (v5 Fix)

```python
# engine/dm_engine.py
import asyncio, httpx, json, re
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

# v5 FIX: Global Ollama serialization lock
#
# The bug: combat narration (short, ~2s) fires while DM stream is running (~10s).
# FastAPI sends 2nd HTTP request to Ollama port 11434.
# Ollama either:
#   A) Queues it → 10s extra delay for combat narration
#   B) PARALLEL_REQUESTS=2 → duplicates KV cache for 3200 token context
#      → 2× KV cache = ~1.2GB extra VRAM → total ~5.6GB → OOM crash on 6GB card
#
# Fix: ONE asyncio.Lock() for ALL Ollama HTTP calls across the entire backend.
# Only ever one active LLM request. VRAM stays flat at ~4.4GB permanently.
# Second request waits in asyncio queue — never touches the GPU until first finishes.

_ollama_lock = asyncio.Lock()
```

## 8.2 Ollama JSON Schema

```python
# models/narrative.py
DM_RESPONSE_SCHEMA = {
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
        "npc_updates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "npc_id":      {"type": "string"},
                    "mood_change": {"type": "string"},
                    "new_memory":  {"type": "string"}
                },
                "required": ["npc_id", "mood_change", "new_memory"]
            }
        },
        "world_event": {"type": ["string", "null"]}
    },
    "required": ["narrative", "choices"]
}
```

### 8.3 Live Streaming + Lock

```python
async def stream_dm_response(
    context: "GameContext",
    ws_manager: "WebSocketManager",
    session_id: str,
) -> "DMResponse":
    prompt       = build_prompt(context)
    full_buffer  = ""
    in_narrative = False
    narr_done    = False

    # ── v5 FIX: _ollama_lock — only one LLM request runs at a time ──────────
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
                    if not line: continue
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


def validate_dm_response(raw: str) -> "DMResponse":
    """Three-tier fallback — game never crashes."""
    from json_repair import repair_json
    from pydantic import ValidationError

    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        return DMResponse.model_validate(json.loads(cleaned))
    except (json.JSONDecodeError, ValidationError):
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
```

### 8.4 Combat Narration — Also Locked

```python
async def get_combat_narration(action_result: dict, world: "WorldAlignment") -> str:
    """Short non-streaming call. Uses same _ollama_lock — serialized with DM stream."""
    prompt = (
        f"World: {world.mood_descriptor}. "
        f"Combat result: {json.dumps(action_result)}. "
        f"Write exactly 1–2 sentences narrating this. Respond with ONLY the narration text."
    )
    async with _ollama_lock:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    return r.json().get("response", "The blow lands with a thud.").strip()
```

### 8.5 System Prompt

```python
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
1. 2–3 vivid atmospheric paragraphs. Max 350 words.
2. Exactly 2–3 choices with real moral weight.
3. alignment shifts: numbers -20 to 20. Never strings.
4. NPCs remember their histories.
5. RECENT NARRATIVE is authoritative — if it says building is on fire, it is on fire.
6. Reference past dissent when dramatically appropriate.
7. No markdown fences. JSON only.
"""
```

---

## 9. Combat Engine

### 9.1 Data Models

```python
# models/combat.py
from enum import Enum
from pydantic import BaseModel, Field

class EnemyBehavior(str, Enum):
    reckless  = "reckless"
    tactical  = "tactical"
    defensive = "defensive"
    erratic   = "erratic"

class EnemyState(BaseModel):
    enemy_id:       str
    name:           str
    hp:             int
    max_hp:         int
    ac:             int = Field(ge=5, le=25)
    damage_dice:    str
    behavior:       EnemyBehavior = EnemyBehavior.reckless
    status_effects: list[str] = []
    is_alive:       bool = True

class CombatState(BaseModel):
    combat_id:          str
    enemies:            list[EnemyState]
    initiative_order:   list[str]
    current_turn_index: int = 0
    round_number:       int = 1
    log:                list[str] = []

    @property
    def current_actor(self) -> str:
        return self.initiative_order[self.current_turn_index % len(self.initiative_order)]

    @property
    def all_enemies_dead(self) -> bool:
        return all(not e.is_alive for e in self.enemies)
```

### 9.2 Sliding Window + Post-Combat Summary

```python
# engine/combat_engine.py
COMBAT_LOG_WINDOW = 5

def get_combat_context_for_prompt(combat_state: CombatState) -> str:
    """
    Only last 5 entries injected into LLM prompt.
    4 players × 4 enemies × 5 rounds = 40 entries × ~40 tokens = 1,600 tokens.
    Sliding window keeps it at exactly 5 × 40 = 200 tokens always.
    """
    return "\n".join(combat_state.log[-COMBAT_LOG_WINDOW:])


async def summarize_and_clear_combat_log(combat_state: CombatState, session_id: str):
    """
    Called immediately when combat ends, before returning to exploration.
    Stores summary in BOTH ChromaDB (semantic) AND SQLite (recency).
    Clears log from memory.
    """
    if not combat_state.log:
        return

    prompt = (
        "Summarize this combat in exactly 2 sentences, "
        f"preserving outcomes and dramatic moments:\n{chr(10).join(combat_state.log)}"
    )
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
```

### 9.3 Server-Authoritative Dice (v6 Fix)

```python
# engine/combat_engine.py
# v6 FIX: Server calculates dice result FIRST, broadcasts it to frontend,
# frontend animates to that EXACT value, THEN narration streams.
#
# The bug: frontend DiceRoller used Math.random() for the visual roll.
# Backend used Python random.randint() for actual game logic.
# Two completely independent RNGs — completely unrelated results.
# Player watches a Nat 20 animation while DM narrates them tripping.
# Destroys player trust in one round.
#
# Fix: client NEVER generates random numbers for game logic.
# Server rolls → sends dice_result → frontend animates to server value.

import random, re

def roll_dice(expression: str) -> tuple[int, list[int]]:
    match = re.fullmatch(r"(\d*)d(\d+)([+-]\d+)?", expression.strip().lower())
    if not match: raise ValueError(f"Invalid: {expression}")
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

def enemy_ai_turn(enemy: EnemyState, players: list["PlayerState"],
                  world: "WorldAlignment") -> dict:
    alive = [p for p in players if p.hp > 0]
    if not alive: return {"action": "idle"}

    behavior = enemy.behavior
    if world.order_chaos > 50:    behavior = EnemyBehavior.tactical
    elif world.order_chaos < -50: behavior = EnemyBehavior.reckless
    if world.harm_harmony > 60 and random.random() < 0.15:
        return {"action": "surrender", "enemy_id": enemy.enemy_id}

    target = {
        EnemyBehavior.reckless:  random.choice(alive),
        EnemyBehavior.tactical:  min(alive, key=lambda p: p.hp),
        EnemyBehavior.defensive: min(alive, key=lambda p: p.hp),
        EnemyBehavior.erratic:   random.choice(alive),
    }[behavior]

    hit, roll, is_crit = roll_attack(2, target.stats.ac)
    damage, _          = roll_dice(enemy.damage_dice) if hit else (0, [])
    if is_crit: damage *= 2

    return {"action": "attack", "enemy_id": enemy.enemy_id,
            "target_player_id": target.player_id, "hit": hit,
            "damage": damage, "roll": roll, "is_crit": is_crit}


async def process_combat_action(
    acting_player_id: str, action: dict,
    combat_state: "CombatState", session: "GameSession",
    ws_manager: "WebSocketManager",
):
    """
    Correct combat action sequence — server-authoritative dice.

    Step 1: Roll on server (source of truth)
    Step 2: Send dice_result to ALL players immediately
    Step 3: Short delay so frontend animation plays
    Step 4: THEN stream combat narration

    Frontend DiceRoller animates to the server-dictated value.
    Math.random() in the frontend is only for spin speed/flourish — NEVER for value.
    """
    hit, roll, is_crit = roll_attack(modifier=2, target_ac=8)
    damage_rolls        = []
    damage              = 0
    if hit:
        damage, damage_rolls = roll_dice(combat_state.enemies[0].damage_dice
                                          if combat_state.enemies else "1d6")
        if is_crit: damage *= 2

    action_result = {
        "actor":  acting_player_id,
        "hit":    hit,
        "roll":   roll,
        "is_crit": is_crit,
        "damage": damage,
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

    # Step 3: wait for dice animation to complete (~1.5s CSS transition)
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
```

---

## 10. Multiplayer Architecture

### 10.1 Exploration Race Condition Lock (v5 Fix)

```python
# models/session.py — add to GameSession
class GameSession(BaseModel):
    session_id:     str
    players:        dict[str, "PlayerState"]
    world_state:    WorldAlignment
    current_scene:  "SceneState"
    turn_order:     list[str]
    current_turn:   int = 0
    party_leader:   str
    phase:          "ScenePhase" = "exploration"
    created_at:     float
    is_generating:  bool = False    # ← v5 FIX: per-session generation lock


# multiplayer/ws_manager.py — handle incoming player_action
async def handle_player_action(session: GameSession, player_id: str, action: str,
                                ws_manager: "WebSocketManager"):
    # ── v5 FIX: Exploration race condition guard ─────────────────────────────
    # Combat has initiative_order. Exploration had nothing.
    # Two simultaneous actions = two parallel stream_dm_response coroutines
    # = two streams interleaving on frontend = garbled mess.
    # is_generating is per-session so Session 1 never blocks Session 2.
    # ─────────────────────────────────────────────────────────────────────────
    if session.is_generating:
        await ws_manager.send_to_player(session.session_id, player_id, {
            "type":   "action_rejected",
            "reason": "The DM is speaking... wait for the story to unfold."
        })
        return

    session.is_generating = True
    touch_session(session.session_id)
    try:
        context = await build_game_context(session, action)
        await stream_dm_response(context, ws_manager, session.session_id)
    finally:
        session.is_generating = False  # always release — even on exception
```

### 10.2 Player Identity + Reconnection + Full State Sync

```python
# multiplayer/session_manager.py
import asyncio, uuid, time, aiosqlite
from pydantic import BaseModel

class PlayerIdentity(BaseModel):
    player_id:       str
    reconnect_token: str
    display_name:    str
    session_id:      str | None = None

_active_sessions:   dict[str, "GameSession"] = {}
_reconnect_registry: dict[str, PlayerIdentity] = {}
_last_activity:     dict[str, float] = {}
SESSION_TTL = 15 * 60  # 15 minutes

def touch_session(session_id: str):
    _last_activity[session_id] = time.time()

async def handle_connect(ws: "WebSocket", token: str | None):
    if token and token in _reconnect_registry:
        identity = _reconnect_registry[token]
        await resume_player_session(ws, identity)
    else:
        identity = PlayerIdentity(
            player_id       = str(uuid.uuid4()),
            reconnect_token = str(uuid.uuid4()),
            display_name    = "Unnamed Hero",
        )
        _reconnect_registry[identity.reconnect_token] = identity
        await send_json(ws, {"type": "identity_issued", "identity": identity.model_dump()})


async def resume_player_session(ws: "WebSocket", identity: PlayerIdentity):
    """
    v4 FIX: Full state sync on reconnect — player never loads blank UI.
    v5 addition: active_vote includes deadline_ts so countdown resumes correctly.
    """
    session = _active_sessions.get(identity.session_id)
    if not session:
        # Session was pruned to SQLite — reload it
        session = await load_session_from_sqlite(identity.session_id)
        if not session:
            await send_json(ws, {"type": "session_expired"})
            return
        _active_sessions[identity.session_id] = session

    if identity.player_id in session.players:
        session.players[identity.player_id].is_connected = True

    active_vote = get_active_vote(session.session_id)

    await send_json(ws, {
        "type":            "full_state_sync",
        "world_alignment": session.world_state.model_dump(),
        "quadrant":        session.world_state.quadrant,
        "regions":         [r.model_dump() for r in get_all_regions(session)],
        "players":         {pid: p.model_dump() for pid, p in session.players.items()},
        "current_phase":   session.phase,
        "last_narrative":  await get_last_narrative_sqlite(session.session_id),
        "last_choices":    await get_last_choices_sqlite(session.session_id),
        "active_vote":     {**active_vote.model_dump(),
                            "deadline_ts": active_vote.deadline} if active_vote else None,
    })
    touch_session(session.session_id)
```

### 10.3 Session Memory Pruner (v5 Fix)

```python
async def session_pruner():
    """
    v5 FIX: Background task — prevents infinite RAM bleed on long sessions.
    Inactive sessions serialized to SQLite and deleted from memory dict.
    Reloaded from SQLite on next player message.
    Runs every 5 minutes.
    """
    while True:
        await asyncio.sleep(300)
        now     = time.time()
        expired = [sid for sid, last in _last_activity.items()
                   if now - last > SESSION_TTL]
        for sid in expired:
            session = _active_sessions.get(sid)
            if session:
                await serialize_session_to_sqlite(session)
                del _active_sessions[sid]
                del _last_activity[sid]
                print(f"[Session] Pruned {sid} to SQLite — freed memory")

# Start in FastAPI lifespan alongside chroma_write_worker
```

### 10.4 Vote System

```python
# multiplayer/vote_system.py
class VoteSession(BaseModel):
    vote_id:         str
    session_id:      str
    choices:         list[str]
    votes:           dict[str, int] = {}
    deadline:        float
    resolved:        bool = False
    party_leader_id: str

class VoteResult(BaseModel):
    winning_index:  int
    vote_counts:    dict[int, int]
    dissenters:     list[str]
    was_tie_broken: bool

async def resolve_vote(vote: VoteSession, session: "GameSession") -> VoteResult:
    connected  = {p.player_id for p in session.players.values() if p.is_connected}
    valid      = {pid: idx for pid, idx in vote.votes.items() if pid in connected}
    if not valid:
        return VoteResult(winning_index=0, vote_counts={}, dissenters=[], was_tie_broken=True)

    tally: dict[int, int] = {}
    for idx in valid.values():
        tally[idx] = tally.get(idx, 0) + 1

    max_v    = max(tally.values())
    winners  = [i for i, c in tally.items() if c == max_v]
    tie      = len(winners) > 1
    winning  = valid.get(vote.party_leader_id, winners[0]) if tie else winners[0]

    return VoteResult(winning_index=winning, vote_counts=tally,
                      dissenters=[pid for pid, i in valid.items() if i != winning],
                      was_tie_broken=tie)

async def finalize_vote(vote_id: str, result: VoteResult, session: "GameSession"):
    vote         = get_vote(vote_id)
    winning_text = vote.choices[result.winning_index]
    vote.resolved = True

    # Log winning action
    await queue_write("player_history", "add",
        documents=[f"Party chose: {winning_text}"],
        ids=[f"vote_{vote_id}_win"],
        metadatas=[{"player_id": "party", "turn": session.current_turn,
                    "region": session.current_scene.region_id,
                    "moral_tag": "collective_choice", "session_id": session.session_id}])

    # v4 FIX: Log dissent per dissenting player — DM remembers forever
    for player_id in result.dissenters:
        name = session.players[player_id].display_name
        await queue_write("player_history", "add",
            documents=[f"{name} dissented and felt conflicted about '{winning_text}'. Complied reluctantly."],
            ids=[f"vote_{vote_id}_dissent_{player_id}"],
            metadatas=[{"player_id": player_id, "turn": session.current_turn,
                        "region": session.current_scene.region_id,
                        "moral_tag": "dissent", "session_id": session.session_id}])

    await ws_manager.broadcast(session.session_id, {
        "type": "vote_result", "winning_index": result.winning_index,
        "vote_counts": result.vote_counts,
    })
    await send_dissenter_narratives(result.dissenters, winning_text, session.session_id)

    # v6 FIX: Trigger DM narration — without this the game halts forever after a vote.
    # The bug: finalize_vote() logs, broadcasts, sends inner_conflict — then ENDS.
    # Players see "The party chose: Kick down the door" and then nothing.
    # The DM never narrates the outcome. Gameplay loop is permanently broken.
    #
    # Fix: construct a synthetic action from winning_text and fire stream_dm_response.
    # The is_generating lock is set so no race condition possible.
    if not session.is_generating:
        session.is_generating = True
        try:
            synthetic_action = f"The party collectively decided to: {winning_text}"
            context = await build_game_context(session, synthetic_action)
            await stream_dm_response(context, ws_manager, session.session_id)
        finally:
            session.is_generating = False

async def start_vote_timer(vote_id: str, session_id: str, timeout: float = 30.0):
    await asyncio.sleep(timeout)
    vote = get_vote(vote_id)
    if not vote.resolved:
        session = _active_sessions[session_id]
        result  = await resolve_vote(vote, session)
        await finalize_vote(vote_id, result, session)

async def send_dissenter_narratives(dissenters: list[str], chosen_text: str, session_id: str):
    if not dissenters: return
    prompt = (f'The party chose: "{chosen_text}". '
              f"Write one sentence of inner conflict for a dissenting player.")
    async with _ollama_lock:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    text = r.json().get("response", "You follow reluctantly.").strip()
    for player_id in dissenters:
        await ws_manager.send_to_player(session_id, player_id,
            {"type": "inner_conflict", "text": text})
```

### 10.5 WebSocket Manager — Concurrent Broadcast (v6 Fix)

```python
# multiplayer/ws_manager.py
import asyncio
from fastapi import WebSocket

_session_connections: dict[str, list[WebSocket]] = {}

def get_session_connections(session_id: str) -> list[WebSocket]:
    return list(_session_connections.get(session_id, []))

async def add_connection(session_id: str, ws: WebSocket):
    _session_connections.setdefault(session_id, []).append(ws)

async def remove_connection(session_id: str, ws: WebSocket):
    conns = _session_connections.get(session_id, [])
    if ws in conns:
        conns.remove(ws)

async def _safe_send(ws: WebSocket, message: dict):
    """Single send — raises on failure so gather can catch it."""
    await ws.send_json(message)

async def broadcast(session_id: str, message: dict):
    """
    v6 FIX: asyncio.gather with return_exceptions=True.

    The bug: sequential `for ws in connections: await ws.send_json(msg)`
    A player's laptop goes to sleep → TCP socket half-open for MINUTES.
    Server awaits acknowledgment from dead socket → entire loop hangs.
    All live players stop receiving tokens until OS TCP timeout (2-4 min).

    Fix: fire all sends concurrently. Dead socket fails in isolation.
    Other players never wait for it. Narrative stream never pauses.
    """
    connections = get_session_connections(session_id)
    if not connections:
        return

    results = await asyncio.gather(
        *[_safe_send(ws, message) for ws in connections],
        return_exceptions=True
    )

    # Prune dead connections immediately
    dead = [ws for ws, r in zip(connections, results) if isinstance(r, Exception)]
    for ws in dead:
        await remove_connection(session_id, ws)

async def send_to_player(session_id: str, player_id: str, message: dict):
    """Single-player send — still wrapped safely."""
    conns = get_session_connections(session_id)
    # Match by player_id stored on ws state
    for ws in conns:
        if getattr(ws.state, 'player_id', None) == player_id:
            try:
                await ws.send_json(message)
            except Exception:
                await remove_connection(session_id, ws)
            return
```

### 10.6 WebSocket Protocol

**Client → Server:**
```json
{ "type": "player_action",  "action": "I inspect the altar", "player_id": "..." }
{ "type": "combat_action",  "action": "attack", "target": "goblin_3", "player_id": "..." }
{ "type": "vote_choice",    "choice_index": 1,  "player_id": "..." }
{ "type": "reconnect",      "reconnect_token": "..." }
{ "type": "ping" }
```

**Server → Client:**
```json
{ "type": "action_rejected",   "reason": "The DM is speaking..." }
{ "type": "narrative_stream",  "chunk": "The fog thickens...", "done": false }
{ "type": "narrative_stream",  "chunk": "", "done": true }
{ "type": "turn_complete",     "choices": [...], "npc_updates": [...], "world_event": null }
{ "type": "combat_update",     "actor": "...", "result": {...}, "hp_map": {...}, "narration": "..." }
{ "type": "world_shift",       "alignment": {...}, "quadrant": "tyranny" }
{ "type": "map_update",        "regions": [...] }
{ "type": "vote_started",      "vote_id": "...", "choices": [...], "deadline_ts": 1234567890 }
{ "type": "vote_result",       "winning_index": 1, "vote_counts": {"0": 1, "1": 2} }
{ "type": "inner_conflict",    "text": "You follow reluctantly..." }
{ "type": "full_state_sync",   "world_alignment": {...}, "regions": [...], "players": {...}, "active_vote": null }
{ "type": "identity_issued",   "identity": {...} }
{ "type": "session_expired" }
{ "type": "pong" }
```

### 10.6 Frontend Dispatcher

```javascript
// stores/wsStore.js
import { create } from 'zustand'
import { useGameStore } from './gameStore'

const MESSAGE_HANDLERS = {
  narrative_stream:  (d) => useGameStore.getState().appendNarrativeChunk(d.chunk, d.done),
  turn_complete:     (d) => useGameStore.getState().setChoices(d.choices),
  combat_update:     (d) => useGameStore.getState().applyCombatUpdate(d),
  world_shift:       (d) => useGameStore.getState().updateAlignment(d.alignment),
  map_update:        (d) => useGameStore.getState().updateRegions(d.regions),
  vote_started:      (d) => useGameStore.getState().startVote(d),
  vote_result:       (d) => useGameStore.getState().resolveVote(d),
  inner_conflict:    (d) => useGameStore.getState().showInnerConflict(d.text),
  action_rejected:   (d) => useGameStore.getState().showToast(d.reason),
  full_state_sync:   (d) => {
    const s = useGameStore.getState()
    s.updateAlignment(d.world_alignment)
    s.updateRegions(d.regions)
    s.syncPlayers(d.players)
    s.setPhase(d.current_phase)
    s.setLastNarrative(d.last_narrative)
    s.setChoices(d.last_choices)
    if (d.active_vote) {
      const remainingMs = (d.active_vote.deadline_ts * 1000) - Date.now()
      if (remainingMs > 0) s.startVote({ ...d.active_vote, remainingMs })
    }
  },
  player_joined:   (d) => useGameStore.getState().addPlayer(d.player),
  player_left:     (d) => useGameStore.getState().removePlayer(d.player_id),
  turn_indicator:  (d) => useGameStore.getState().setActiveTurn(d.active_player),
  session_expired: ()  => useGameStore.getState().handleSessionExpired(),
  identity_issued: (d) => {
    localStorage.setItem('lw_player_id',       d.identity.player_id)
    localStorage.setItem('lw_reconnect_token', d.identity.reconnect_token)
    useGameStore.getState().setLocalPlayer(d.identity)
  },
}

export const useWsStore = create((set, get) => ({
  socket: null, connected: false, _reconnectAttempts: 0,

  connect: (sessionId) => {
    const token = localStorage.getItem('lw_reconnect_token')
    const ws    = new WebSocket(`ws://localhost:8000/ws/${sessionId}?token=${token ?? ''}`)

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      const handler = MESSAGE_HANDLERS[data.type]
      if (handler) handler(data)
      else console.warn('[WS] Unhandled:', data.type)
    }
    ws.onclose = () => {
      set({ connected: false })
      const delay = Math.min(1000 * 2 ** get()._reconnectAttempts, 30000)
      set(s => ({ _reconnectAttempts: s._reconnectAttempts + 1 }))
      setTimeout(() => get().connect(sessionId), delay)
    }
    ws.onopen = () => {
      set({ connected: true, _reconnectAttempts: 0 })
      const token = localStorage.getItem('lw_reconnect_token')
      if (token) get().send({ type: 'reconnect', reconnect_token: token })
    }
    set({ socket: ws })
  },

  // v5 FIX: explicit disconnect — prevents Vite HMR zombie connections
  disconnect: () => {
    const { socket } = get()
    if (socket) {
      socket.onclose = null          // prevent auto-reconnect on intentional close
      socket.close(1000, 'HMR cleanup')
      set({ socket: null, connected: false })
    }
  },

  send: (msg) => {
    const { socket } = get()
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(msg))
  },
}))
```

---

## 11. Session Memory Management

### 11.1 SQLite — aiosqlite Everywhere (v5 Fix)

```python
# db/sqlite_store.py
# ── v5 FIX: All SQLite calls use aiosqlite ──────────────────────────────────
# Plain sqlite3 is synchronous. Calling it in a FastAPI WebSocket route
# blocks the event loop — same bug as ChromaDB without to_thread.
# aiosqlite is a proper async wrapper — zero event loop blocking.
# ────────────────────────────────────────────────────────────────────────────
import aiosqlite, time

DB_PATH = "loreweaver.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                data       TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS players (
                player_id  TEXT,
                session_id TEXT,
                hp         INTEGER,
                data       TEXT,
                PRIMARY KEY (player_id, session_id)
            );
            CREATE TABLE IF NOT EXISTS narrative_summaries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                summary    TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_narrative_session
                ON narrative_summaries(session_id, created_at DESC);
        """)
        await db.commit()

async def update_player_hp(session_id: str, player_id: str, new_hp: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE players SET hp=? WHERE session_id=? AND player_id=?",
            (new_hp, session_id, player_id))
        await db.commit()

async def serialize_session_to_sqlite(session: "GameSession"):
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO sessions (session_id, data, updated_at) VALUES (?,?,?)",
            (session.session_id, session.model_dump_json(), time.time()))
        await db.commit()

async def load_session_from_sqlite(session_id: str) -> "GameSession | None":
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        row = await db.execute_fetchall(
            "SELECT data FROM sessions WHERE session_id=?", (session_id,))
    if not row: return None
    from models.session import GameSession
    return GameSession.model_validate_json(row[0][0])

async def get_last_narrative_sqlite(session_id: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT summary FROM narrative_summaries WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
            (session_id,))
    return rows[0][0] if rows else ""
```

### 11.2 main.py — Complete Startup

```python
# backend/main.py
# ── MUST BE FIRST — Windows SQLite version fix ───────────────────────────────
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
import asyncio

from db.sqlite_store import init_db
from rag.collections import chroma_write_worker
from multiplayer.session_manager import session_pruner
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
import httpx

async def verify_ollama():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            models = [m["name"] for m in r.json().get("models", [])]
            assert any(OLLAMA_MODEL in m for m in models)
            print(f"✅ Ollama connected — {OLLAMA_MODEL} ready")
    except Exception as e:
        raise RuntimeError(f"❌ Ollama not reachable: {e}\nRun: ollama serve")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await verify_ollama()
    asyncio.create_task(chroma_write_worker())  # ChromaDB write serializer
    asyncio.create_task(session_pruner())        # 15-min session TTL pruner
    yield

app = FastAPI(lifespan=lifespan)
```

---

## 12. Living World Map Frontend

### 12.1 NarrativeBlock — useRef + rAF Throttle

```jsx
// components/StoryConsole/NarrativeBlock.jsx
// v4 FIX: tokens arrive every 20–50ms.
// useState = 20–50 re-renders/sec = browser main thread chokes.
// useRef + requestAnimationFrame = zero re-renders during stream.
// One re-render when generation completes.

import { useRef, useEffect, useState } from 'react'
import { useGameStore } from '../../stores/gameStore'

export function NarrativeBlock() {
  const containerRef = useRef(null)
  const bufferRef    = useRef('')
  const rafRef       = useRef(null)
  const [isDone, setIsDone] = useState(false)

  useEffect(() => {
    const unsub = useGameStore.subscribe(
      s => s._latestChunk,
      ({ chunk, done }) => {
        if (!chunk && !done) return
        bufferRef.current += chunk

        if (!rafRef.current) {
          rafRef.current = requestAnimationFrame(() => {
            if (containerRef.current)
              containerRef.current.textContent = bufferRef.current
            rafRef.current = null
          })
        }

        if (done) {
          setIsDone(true)
          bufferRef.current = ''
        }
      }
    )
    return () => {
      unsub()
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return <p ref={containerRef} className={`narrative-text ${isDone ? 'done' : 'streaming'}`} />
}
```

```javascript
// stores/gameStore.js
appendNarrativeChunk: (chunk, done) => set(s => ({
  _latestChunk:     { chunk, done },
  currentNarrative: done ? s._narrativeBuffer + chunk : s.currentNarrative,
  _narrativeBuffer: done ? '' : s._narrativeBuffer + chunk,
  narrativeStreaming: !done,
})),
```

### 12.2 AlignmentOverlay — useStoreApi() Sync

```jsx
// components/WorldMap/AlignmentOverlay.jsx
// useStoreApi() reads React Flow's Zustand store synchronously every frame.
// Canvas transform ALWAYS matches React Flow SVG — zero lag at any pan speed.
// Supports world-spanning effects (fog, storms) — per-node approach rejected.

import { useEffect, useRef } from 'react'
import { useStoreApi }       from 'reactflow'

const MAX_PARTICLES = 60
const CONFIGS = {
  justice: { color: '#ffd700', speed: 0.5 },
  tyranny: { color: '#ff4444', speed: 1.2 },
  mercy:   { color: '#90ee90', speed: 0.3 },
  anarchy: { color: '#ff6600', speed: 0.8 },
}

export function AlignmentOverlay({ quadrant, intensity, regionPositions }) {
  const canvasRef    = useRef(null)
  const store        = useStoreApi()
  const particlesRef = useRef([])

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx    = canvas.getContext('2d')
    const config = CONFIGS[quadrant] ?? CONFIGS.justice
    const count  = Math.floor((intensity / 100) * MAX_PARTICLES)

    particlesRef.current = Array.from({ length: count }, (_, i) => {
      const r = regionPositions[i % regionPositions.length] ?? { x: 300, y: 300 }
      return { x: r.x + (Math.random()-.5)*200, y: r.y + (Math.random()-.5)*200,
               vx: (Math.random()-.5)*config.speed, vy: (Math.random()-.5)*config.speed,
               alpha: Math.random(), size: Math.random()*3+1, life: Math.random() }
    })

    let animId
    function frame() {
      const { transform } = store.getState()  // ← synchronous read, zero lag
      const [x, y, zoom]  = transform
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width; canvas.height = rect.height
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.save(); ctx.translate(x, y); ctx.scale(zoom, zoom)

      particlesRef.current.forEach(p => {
        p.x += p.vx; p.y += p.vy; p.life += 0.005
        p.alpha = Math.sin(p.life * Math.PI)
        if (p.life >= 1) {
          const r = regionPositions[Math.floor(Math.random()*regionPositions.length)]
          p.x = r.x+(Math.random()-.5)*150; p.y = r.y+(Math.random()-.5)*150
          p.life = 0; p.vx=(Math.random()-.5)*config.speed; p.vy=(Math.random()-.5)*config.speed
        }
        ctx.globalAlpha = Math.max(0, p.alpha)*0.7
        ctx.fillStyle   = config.color
        ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI*2); ctx.fill()
      })

      ctx.restore(); ctx.globalAlpha = 1
      animId = requestAnimationFrame(frame)
    }
    animId = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(animId)
  }, [quadrant, intensity])

  return <canvas ref={canvasRef} style={{
    position:'absolute', top:0, left:0, width:'100%', height:'100%',
    pointerEvents:'none', zIndex:10
  }} />
}
```

### 12.3 React Flow Node Update — Data Mutation Only (v5 Fix)

```javascript
// stores/gameStore.js
updateRegions: (updatedRegions) => set(state => ({
  // v5 FIX: mutate only .data — preserve top-level node reference.
  // Replacing the entire nodes array causes React Flow to unmount
  // every node and snap viewport to (0,0). Never do full replacement.
  mapNodes: state.mapNodes.map(node => {
    const updated = updatedRegions.find(r => r.region_id === node.id)
    if (!updated) return node   // same reference — React Flow ignores it
    return {
      ...node,                  // same id, position, type
      data: {                   // only data changes
        ...node.data,
        mood:        updated.base_mood,
        dangerLevel: updated.danger_level,
        explored:    updated.explored,
        alignment:   updated.alignment_modifiers,
      }
    }
  })
})),
```

### 12.4 App.jsx — Zombie WebSocket Cleanup (v5 Fix)

```jsx
// App.jsx
import { useEffect } from 'react'
import { useWsStore } from './stores/wsStore'

export default function App() {
  const { connect, disconnect } = useWsStore()

  useEffect(() => {
    const sessionId = localStorage.getItem('lw_session_id')
    if (sessionId) connect(sessionId)

    // v5 FIX: cleanup runs on unmount AND on every Vite HMR reload.
    // Without this: every Ctrl+S = 1 zombie WebSocket.
    // After 50 saves: FastAPI broadcasting to 50 dead sockets → crash.
    return () => disconnect()
  }, [])

  return ( /* ... rest of component tree ... */ )
}
```

### 12.5 DiceRoller — Server-Dictated Animation (v6 Fix)

```jsx
// components/Combat/DiceRoller.jsx
// v6 FIX: DiceRoller NEVER calls Math.random() for game values.
// Receives exact dice result from server → animates CSS 3D die to that face.
// Math.random() is ONLY used for pre-roll spin duration (pure visual flourish).

import { useEffect, useRef } from 'react'
import { useGameStore } from '../../stores/gameStore'

// Maps d20 value (1-20) to CSS transform for each face
const D20_FACE_ROTATIONS = {
  1:  'rotateX(0deg)   rotateY(0deg)',
  2:  'rotateX(180deg) rotateY(0deg)',
  20: 'rotateX(0deg)   rotateY(180deg)',
  // ... full map for all 20 faces
}

export function DiceRoller() {
  const diceRef    = useRef(null)
  const spinningRef = useRef(false)

  useEffect(() => {
    // Subscribe to server dice results — NOT to Math.random()
    const unsub = useGameStore.subscribe(
      s => s.pendingDiceResult,
      (result) => {
        if (!result || spinningRef.current) return
        spinningRef.current = true
        animateDiceTo(result.d20, result.is_crit)
      }
    )
    return () => unsub()
  }, [])

  function animateDiceTo(targetValue, isCrit) {
    const el = diceRef.current
    if (!el) return

    // Random spin duration for visual variety (does NOT affect outcome)
    const spinDuration = 800 + Math.random() * 400   // 800-1200ms

    // Phase 1: fast random spin (pure visual)
    el.style.transition = `transform ${spinDuration}ms ease-in`
    el.style.transform  = `rotateX(${720 + Math.random()*360}deg) rotateY(${720 + Math.random()*360}deg)`

    // Phase 2: snap to server-dictated face
    setTimeout(() => {
      const finalRotation = D20_FACE_ROTATIONS[targetValue] ?? D20_FACE_ROTATIONS[1]
      el.style.transition = 'transform 400ms cubic-bezier(0.17, 0.67, 0.35, 1.0)'
      el.style.transform  = finalRotation

      if (isCrit) el.classList.add('crit-glow')

      setTimeout(() => {
        spinningRef.current = false
        useGameStore.getState().clearDiceResult()
      }, 450)
    }, spinDuration + 50)
  }

  return (
    <div className="dice-container">
      <div ref={diceRef} className="dice-d20">
        {/* CSS 3D faces */}
      </div>
    </div>
  )
}
```

```javascript
// stores/gameStore.js — dice result state
// gameStore receives dice_result from wsStore dispatcher
setDiceResult:   (result) => set({ pendingDiceResult: result }),
clearDiceResult: ()       => set({ pendingDiceResult: null }),
```

```javascript
// stores/wsStore.js — MESSAGE_HANDLERS addition
dice_result: (d) => useGameStore.getState().setDiceResult(d),
```

### 12.6 Visual Theme System

```javascript
// utils/themeEngine.js
export const ALIGNMENT_THEMES = {
  justice: { '--world-bg-start':'#1a1a2e','--world-bg-end':'#16213e','--world-accent':'#e2b714','--node-border':'#ffd700','--node-glow':'rgba(255,215,0,0.3)','--map-filter':'brightness(1.1) saturate(1.2)' },
  tyranny: { '--world-bg-start':'#0d0d0d','--world-bg-end':'#1a0a0a','--world-accent':'#8b0000','--node-border':'#cc0000','--node-glow':'rgba(139,0,0,0.4)','--map-filter':'contrast(1.3) saturate(0.6)' },
  mercy:   { '--world-bg-start':'#0a1a0a','--world-bg-end':'#1a2e1a','--world-accent':'#7ecf8e','--node-border':'#90ee90','--node-glow':'rgba(144,238,144,0.3)','--map-filter':'brightness(1.0) hue-rotate(10deg)' },
  anarchy: { '--world-bg-start':'#1a0a00','--world-bg-end':'#2e1a0a','--world-accent':'#ff6600','--node-border':'#ff4500','--node-glow':'rgba(255,69,0,0.4)','--map-filter':'contrast(1.2) saturate(1.4) brightness(0.9)' },
}
export function applyTheme(quadrant) {
  Object.entries(ALIGNMENT_THEMES[quadrant] ?? ALIGNMENT_THEMES.justice)
    .forEach(([k,v]) => document.documentElement.style.setProperty(k,v))
}
```

### 12.6 Component Tree

```
<App>  ← useEffect: connect() on mount, disconnect() on unmount/HMR
└── <GameProvider>
    ├── <WorldMap>
    │   ├── <ReactFlow>
    │   │   ├── <RegionNode × N>       (data mutation only — no remounts)
    │   │   └── <PlayerMarker>
    │   ├── <AlignmentOverlay>         (useStoreApi — synchronous pan sync)
    │   └── <FogOfWar>                 (SVG mask)
    ├── <StoryConsole>
    │   ├── <NarrativeBlock>           (useRef + rAF — zero re-renders during stream)
    │   ├── <ChoicePanel>              (disabled while is_generating=true)
    │   └── <VoteTracker>              (30s countdown)
    ├── <PartyPanel>
    │   ├── <CharacterCard × N>
    │   └── <TurnIndicator>
    ├── <CombatOverlay>
    │   ├── <InitiativeTracker>
    │   ├── <DiceRoller>               (CSS 3D)
    │   └── <CombatLog>                (last 5 entries — sliding window)
    ├── <AlignmentCompass>
    └── <CharacterCreation>
```

---

## 13. Data Models Reference

```python
# ── Alignment ──
class WorldAlignment(BaseModel):
    order_chaos:  float = Field(default=0.0, ge=-100.0, le=100.0)
    harm_harmony: float = Field(default=0.0, ge=-100.0, le=100.0)
    # computed: quadrant · intensity · mood_descriptor

# ── Characters ──
class CharacterClass(str, Enum):
    warrior="warrior"; rogue="rogue"; mage="mage"; cleric="cleric"; ranger="ranger"

class CharacterStats(BaseModel):
    strength:int=10; dexterity:int=10; constitution:int=10
    intelligence:int=10; wisdom:int=10; charisma:int=10
    @property
    def dex_mod(self): return (self.dexterity-10)//2
    @property
    def ac(self):      return 10+self.dex_mod

CLASS_STAT_TEMPLATES = {
    CharacterClass.warrior: CharacterStats(strength=16,dexterity=12,constitution=15,intelligence=8, wisdom=10,charisma=10),
    CharacterClass.rogue:   CharacterStats(strength=10,dexterity=17,constitution=12,intelligence=13,wisdom=12,charisma=14),
    CharacterClass.mage:    CharacterStats(strength=6, dexterity=12,constitution=10,intelligence=18,wisdom=14,charisma=12),
    CharacterClass.cleric:  CharacterStats(strength=12,dexterity=10,constitution=13,intelligence=12,wisdom=17,charisma=14),
    CharacterClass.ranger:  CharacterStats(strength=13,dexterity=16,constitution=13,intelligence=12,wisdom=14,charisma=10),
}
CLASS_HP = {CharacterClass.warrior:28, CharacterClass.rogue:20,
            CharacterClass.mage:14,    CharacterClass.cleric:22, CharacterClass.ranger:22}

class Item(BaseModel):
    item_id:str; name:str; item_type:Literal["weapon","armor","potion","quest","misc"]
    damage_dice:str|None=None; properties:dict={}

class PlayerState(BaseModel):
    player_id:str; display_name:str; character_class:CharacterClass
    stats:CharacterStats; inventory:list[Item]=[]; hp:int; max_hp:int
    position:str; is_connected:bool=True; reconnect_token:str

# ── Enemies ──
class EnemyBehavior(str,Enum):
    reckless="reckless"; tactical="tactical"; defensive="defensive"; erratic="erratic"

class EnemyState(BaseModel):
    enemy_id:str; name:str; hp:int; max_hp:int
    ac:int=Field(ge=5,le=25); damage_dice:str
    behavior:EnemyBehavior=EnemyBehavior.reckless
    status_effects:list[str]=[]; is_alive:bool=True

# ── Regions + NPCs ──
class Region(BaseModel):
    region_id:str; name:str; description:str; base_mood:str
    connections:list[str]; npcs:list[str]
    danger_level:int=Field(default=1,ge=1,le=10)
    explored:bool=False; alignment_modifiers:dict={}; map_position:dict={}

class NPC(BaseModel):
    npc_id:str; name:str; role:str; region:str
    base_disposition:float=Field(default=0.0,ge=-1.0,le=1.0)
    alignment_sensitivity:dict={}; personality_tags:list[str]; backstory:str

# ── Sessions ──
class ScenePhase(str,Enum):
    exploration="exploration"; combat="combat"; dialogue="dialogue"; cutscene="cutscene"

class CombatState(BaseModel):
    combat_id:str; enemies:list[EnemyState]; initiative_order:list[str]
    current_turn_index:int=0; round_number:int=1; log:list[str]=[]

class SceneState(BaseModel):
    scene_id:str; region_id:str; description:str; active_npcs:list[str]
    turn_count:int=0; phase:ScenePhase=ScenePhase.exploration
    combat_state:CombatState|None=None

class GameSession(BaseModel):
    session_id:str; players:dict[str,PlayerState]; world_state:WorldAlignment
    current_scene:SceneState; turn_order:list[str]; current_turn:int=0
    party_leader:str; phase:ScenePhase=ScenePhase.exploration
    created_at:float; is_generating:bool=False   # ← v5 race condition lock

# ── Narrative ──
class MoralChoice(BaseModel):
    text:str
    order_chaos_shift:float=Field(default=0.0,ge=-20.0,le=20.0)
    harm_harmony_shift:float=Field(default=0.0,ge=-20.0,le=20.0)

class NPCUpdate(BaseModel):
    npc_id:str; mood_change:str; new_memory:str

class DMResponse(BaseModel):
    narrative:str=Field(max_length=2000)
    choices:list[MoralChoice]=Field(min_length=2,max_length=3)
    npc_updates:list[NPCUpdate]=[]
    world_event:str|None=None
```

---

## 14. CLAUDE.md — Vibe Coding Master Prompt

```markdown
# CLAUDE.md — LoreWeaver Build Guide

## PRIME DIRECTIVE
ONE file per response. Stop after each file. Wait for my verification.
Do not proceed until I confirm the test passed.

## 10 CONSTRAINTS — NEVER VIOLATE
1. main.py: pysqlite3 override is LITERALLY the first 3 lines before any import
2. embed() is ASYNC — uses asyncio.to_thread internally (Section 7.1)
3. ALL SQLite calls use aiosqlite — never raw sqlite3 in async context (Section 11.1)
4. ALL Ollama calls wrapped in `async with _ollama_lock` (Section 8.1)
5. asyncio.gather() for RAG queries — NOT sequential awaits (Section 7.4)
6. useStoreApi() for D3 canvas — NOT useViewport() (Section 12.2)
7. useRef + requestAnimationFrame for NarrativeBlock — NOT useState (Section 12.1)
8. updateRegions() mutates node.data only — never replaces full nodes array (Section 12.3)
9. is_generating flag on GameSession — checked before every exploration action (Section 10.1)
10. disconnect() returned from App.jsx useEffect cleanup — prevents HMR zombies (Section 12.4)
11. truncate_chunks() uses CHARS_PER_TOKEN = 3.5 ratio — NEVER import transformers tokenizer (Section 7.3)
12. broadcast() uses asyncio.gather(return_exceptions=True) — NEVER sequential for-loop (Section 10.5)
13. finalize_vote() calls stream_dm_response() at the end — NEVER let vote resolution be a dead end (Section 10.4)
14. DiceRoller NEVER calls Math.random() for game values — always animates to server dice_result (Section 12.5)

## BUILD ORDER
 1. config.py
    verify: python -c "from config import OLLAMA_BASE_URL; print(OLLAMA_BASE_URL)"
 2. models/alignment.py
    verify: python -c "from models.alignment import WorldAlignment; print(WorldAlignment().quadrant)"
 3. models/characters.py
    verify: python -c "from models.characters import CLASS_STAT_TEMPLATES, CharacterClass; print(CLASS_STAT_TEMPLATES[CharacterClass.warrior].ac)"
 4. models/combat.py
    verify: python -c "from models.combat import EnemyState; print('ok')"
 5. models/narrative.py
    verify: python -c "from models.narrative import DM_RESPONSE_SCHEMA; assert 'narrative' in DM_RESPONSE_SCHEMA['properties']"
 6. models/region.py
    verify: python -c "from models.region import Region, NPC; print('ok')"
 7. models/session.py
    verify: python -c "from models.session import GameSession; g=GameSession.__fields__; assert 'is_generating' in g"
 8. db/sqlite_store.py
    verify: python -c "import asyncio; from db.sqlite_store import init_db; asyncio.run(init_db()); print('WAL ready')"
 9. rag/embedder.py
    verify: python scripts/check_04_embeddings.py
10. rag/collections.py
    verify: python scripts/check_03_chroma_thread.py
11. rag/retriever.py
    verify: python -c "import inspect,asyncio; from rag.retriever import assemble_context; assert asyncio.iscoroutinefunction(assemble_context)"
12. rag/memory_manager.py
    verify: python -c "from rag.memory_manager import enforce_npc_memory_limit; print('ok')"
13. engine/alignment_engine.py
    verify: python -c "from engine.alignment_engine import apply_alignment_shift; from models.alignment import WorldAlignment; w=apply_alignment_shift(WorldAlignment(),{'order_chaos_shift':25}); assert w.order_chaos==20.0"
14. engine/dm_engine.py
    verify: python scripts/check_01_streaming.py && python scripts/check_02_json_format.py && python scripts/check_06_ollama_lock.py
15. engine/combat_engine.py
    verify: python -c "from engine.combat_engine import roll_dice; r,_=roll_dice('2d6+3'); assert 5<=r<=15"
16. engine/world_engine.py
    verify: python -c "from engine.world_engine import summarize_and_clear_combat_log; print('ok')"
17. multiplayer/ws_manager.py
    verify: python -c "from multiplayer.ws_manager import WebSocketManager; print('ok')"
18. multiplayer/session_manager.py
    verify: python -c "from multiplayer.session_manager import handle_connect, session_pruner; print('ok')"
19. multiplayer/vote_system.py
    verify: python -c "from multiplayer.vote_system import resolve_vote; print('ok')"
20. main.py
    verify: uvicorn main:app --reload
    expected: "✅ Ollama connected — mistral:7b-instruct-q3_K_S ready" printed, no import errors

## REFERENCE
Full blueprint: LoreWeaver_Blueprint_v5_Final.md
When uncertain → re-read the relevant section before writing code.
If your instinct conflicts with a constraint above → follow the constraint.
```

---

## 15. Folder Structure

```
loreweaver/
├── backend/
│   ├── main.py                       # pysqlite3 FIRST, FastAPI, lifespan
│   ├── config.py                     # OLLAMA_BASE_URL=localhost, model
│   ├── models/
│   │   ├── alignment.py
│   │   ├── characters.py
│   │   ├── combat.py
│   │   ├── narrative.py              # DM_RESPONSE_SCHEMA
│   │   ├── region.py
│   │   └── session.py                # GameSession.is_generating
│   ├── engine/
│   │   ├── dm_engine.py              # _ollama_lock, stream_dm_response, validate
│   │   ├── combat_engine.py          # roll_dice, sliding window, summarizer
│   │   ├── alignment_engine.py       # dampened shift, disposition
│   │   └── world_engine.py           # world_event chain
│   ├── rag/
│   │   ├── collections.py            # chroma_write_worker (asyncio.to_thread)
│   │   ├── embedder.py               # async embed() — to_thread internally
│   │   ├── retriever.py              # gather() + hybrid recency
│   │   └── memory_manager.py         # lifecycle + NPC eviction
│   ├── multiplayer/
│   │   ├── ws_manager.py             # hub, broadcast, send_to_player
│   │   ├── session_manager.py        # connect, resume, full_state_sync, pruner
│   │   └── vote_system.py            # resolve, finalize, dissent log, timer
│   ├── data/
│   │   ├── seed_world.json           # ✅ Week 0
│   │   └── encounter_templates.json
│   └── db/
│       └── sqlite_store.py           # aiosqlite, WAL, narrative_summaries table
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                   # disconnect() in useEffect cleanup
│   │   ├── main.jsx
│   │   ├── stores/
│   │   │   ├── gameStore.js          # _latestChunk, updateRegions (data mutation)
│   │   │   └── wsStore.js            # dispatcher + explicit disconnect()
│   │   ├── components/
│   │   │   ├── WorldMap/
│   │   │   │   ├── WorldMap.jsx
│   │   │   │   ├── RegionNode.jsx
│   │   │   │   ├── PlayerMarker.jsx
│   │   │   │   ├── AlignmentOverlay.jsx  # useStoreApi()
│   │   │   │   └── FogOfWar.jsx
│   │   │   ├── StoryConsole/
│   │   │   │   ├── StoryConsole.jsx
│   │   │   │   ├── NarrativeBlock.jsx    # useRef + rAF
│   │   │   │   ├── ChoicePanel.jsx       # disabled when is_generating
│   │   │   │   └── VoteTracker.jsx
│   │   │   ├── PartyPanel/
│   │   │   │   ├── PartyPanel.jsx
│   │   │   │   ├── CharacterCard.jsx
│   │   │   │   └── TurnIndicator.jsx
│   │   │   ├── Combat/
│   │   │   │   ├── CombatOverlay.jsx
│   │   │   │   ├── DiceRoller.jsx        # CSS 3D
│   │   │   │   └── CombatLog.jsx         # last 5 entries
│   │   │   ├── AlignmentCompass/
│   │   │   │   └── AlignmentCompass.jsx
│   │   │   └── CharacterCreation/
│   │   │       └── CharacterCreation.jsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js
│   │   │   └── useGameState.js
│   │   └── utils/
│   │       ├── themeEngine.js
│   │       └── diceUtils.js
│   ├── package.json
│   └── vite.config.js
│
├── scripts/
│   ├── check_01_streaming.py
│   ├── check_02_json_format.py
│   ├── check_03_chroma_thread.py
│   ├── check_04_embeddings.py
│   ├── check_05_sqlite_version.py
│   ├── check_06_ollama_lock.py       # ← new in v5
│   └── seed_loader.py
│
├── CLAUDE.md                         # Section 14 only
├── LoreWeaver_Blueprint_v5_Final.md  # This document
└── requirements.txt
```

---

## 16. requirements.txt

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
websockets>=12.0
httpx>=0.27.0
pydantic>=2.7.0
chromadb>=0.5.0
pysqlite3-binary>=0.5.0
aiosqlite>=0.20.0
sentence-transformers>=2.7.0
json-repair>=0.25.0
python-dotenv>=1.0.0
```

---

## 17. Phase Plan — 15 Days

### Week 0 (Before Day 1)
- [ ] `ollama pull mistral:7b-instruct` → `ollama ps` shows `100% GPU`
- [ ] `pip install -r requirements.txt`
- [ ] Run check_01 — first token < 2s, speed > 20 tok/s
- [ ] Run check_02 — 20/20 valid JSON
- [ ] Run check_03 — ChromaDB non-blocking
- [ ] Run check_04 — embed < 200ms, async thread confirmed
- [ ] Run check_05 — sqlite version noted, aiosqlite confirmed
- [ ] Run check_06 — Ollama lock serializes 3 concurrent requests
- [ ] Write seed_world.json (3 regions, 4 NPCs minimum)

### Phase 1 — Foundation (Days 1–3)
**Day 1:** All 7 Pydantic models + `db/sqlite_store.py` (aiosqlite + WAL + narrative_summaries table) + `config.py`  
**Day 2:** `engine/dm_engine.py` — `_ollama_lock`, `stream_dm_response` (live tokens), `validate_dm_response` (3-tier), `get_combat_narration` (locked), `build_prompt`  
**Day 3:** RAG pipeline — `rag/embedder.py` (async), `rag/collections.py` (to_thread writer), `rag/retriever.py` (gather + hybrid recency), `rag/memory_manager.py`, `seed_loader.py`

### Phase 2 — Core Loop (Days 4–6)
**Day 4:** Single-player end-to-end — action → `is_generating` check → RAG → stream DM → WS chunks → `turn_complete` → alignment shift → aiosqlite persist  
**Day 5:** Alignment Engine — dampened shift, quadrant logic, disposition calc, consequence table in prompt  
**Day 6:** Combat Engine — dice, `enemy_ai_turn`, initiative, HP tracking, **sliding window**, **post-combat summarizer** (stores to both ChromaDB + SQLite)

### Phase 3 — Frontend (Days 7–9)
**Day 7:** React Flow map — region nodes, edges, `CharacterCreation`, `wsStore.js` + `gameStore.js` full dispatcher  
**Day 8:** `AlignmentOverlay` (useStoreApi), particles (max 60), `applyTheme()`, `FogOfWar`  
**Day 9:** `NarrativeBlock` (useRef+rAF), `ChoicePanel` (disabled during is_generating), `VoteTracker`, `AlignmentCompass`

### Phase 4 — Multiplayer (Days 10–12)
**Day 10:** WS hub, `handle_connect`, `resume_player_session` + `full_state_sync`, `App.jsx` disconnect cleanup  
**Day 11:** Vote system — `resolve_vote`, timer, tie-break, dissent ChromaDB log, dissenter WS routing  
**Day 12:** Party sync — HP sync via aiosqlite, player markers, turn indicator, combat overlay in multiplayer, session pruner live

### Phase 5 — Polish + Portfolio (Days 13–15)
**Day 13:** Expand to 5 regions + 8 NPCs + 5 encounter templates. 20-turn stress test. RAM monitor active. Validate RAG recency correctness.  
**Day 14:** Map animations, CSS 3D dice, combat log colors (crit=gold, fumble=red, surrender=green), responsive layout, toast for action_rejected  
**Day 15:** Portfolio README, architecture diagram, OBS demo video, `CLAUDE.md` retrospective

---

## 18. Risk Register — All 46 Flaws

| # | Risk | Sev | Fix | Ver |
|---|---|---|---|---|
| 1 | Invalid LLM JSON | 🔴 | Ollama format param + json-repair + hardcoded fallback | v2 |
| 2 | outlines + Ollama incompatible | 🔴 | Dropped. Native format param | v3 |
| 3 | Fake streaming — 12s dead UI | 🔴 | Live token SSE → WS → rAF frontend | v3 |
| 4 | ChromaDB blocks event loop | 🔴 | asyncio.to_thread for all ChromaDB ops | v3 |
| 5 | Windows SQLite crash on import | 🔴 | pysqlite3-binary + 3-line override first in main.py | v4 |
| 6 | Exploration phase race condition | 🔴 | is_generating per-session lock + action_rejected toast | v5 |
| 7 | Ollama concurrent VRAM explosion | 🔴 | _ollama_lock serializes ALL Ollama HTTP calls | v5 |
| 8 | SQLite blocks event loop | 🔴 | aiosqlite replaces all raw sqlite3 calls | v5 |
| 9 | embed() freezes event loop 200ms | 🟠 | embed() is async via asyncio.to_thread internally | v5 |
| 10 | RAG recency blindness | 🟠 | Hybrid: SQLite recency (last 2) + ChromaDB (older history) | v5 |
| 11 | Infinite session RAM bleed | 🟠 | 15-min TTL pruner → serialize to SQLite → del from dict | v5 |
| 12 | Vite HMR zombie WebSockets | 🟠 | disconnect() in App.jsx useEffect cleanup | v5 |
| 13 | React Flow node flashing | 🟠 | updateRegions mutates node.data only — never full replace | v5 |
| 14 | React render thrash (token stream) | 🟠 | useRef + requestAnimationFrame in NarrativeBlock | v4 |
| 15 | Combat log context explosion | 🟠 | COMBAT_LOG_WINDOW=5 + post-combat summarizer | v4 |
| 16 | Sequential RAG queries +300ms | 🟠 | asyncio.gather() — 5 queries concurrent | v4 |
| 17 | Ghost dissenter memory wipe | 🟠 | Dissent logged to player_history per dissenting player | v4 |
| 18 | Reconnection state void | 🟠 | full_state_sync on reconnect match | v4 |
| 19 | CLAUDE.md context collapse | 🟠 | 20-step build order, 10 constraints, one file at a time | v4 |
| 20 | D3 canvas jitter on pan/zoom | 🟠 | useStoreApi() synchronous read each frame | v3 |
| 21 | VRAM OOM on RTX 3050 | 🟠 | q3_K_S (3.5GB) + _ollama_lock keeps it flat | v2+v5 |
| 22 | Streaming vs JSON conflict | 🟠 | Stream narrative live → validate choices from buffer | v3 |
| 23 | Seed data missing at test time | 🟠 | Written Week 0, loaded Day 3 | v2 |
| 24 | Missing EnemyState model | 🟠 | Full model in Sections 9.1 and 13 | v2 |
| 25 | Vote system edge cases | 🟠 | Quorum, timeout, disconnect, tie-break, dissenter routing | v2 |
| 26 | Alignment stuck at extremes | 🟠 | Dampening + ±20 cap | v2 |
| 27 | Character creation missing | 🟠 | Class templates + CharacterCreation component | v2 |
| 28 | world_event chain undefined | 🟠 | world_engine.py: SQLite → ChromaDB → WS broadcast | v2 |
| 29 | SQLite write contention | 🟡 | WAL mode from Day 1 | v2 |
| 30 | Poor RAG retrieval (short queries) | 🟡 | expand_query() with region + NPC + alignment | v2 |
| 31 | NPC memory unbounded | 🟡 | Max 20 docs/NPC, FIFO eviction | v2 |
| 32 | wsStore/gameStore bridge | 🟡 | MESSAGE_HANDLERS dispatcher — typed + complete | v2 |
| 33 | Player reconnection missing | 🟡 | reconnect_token + exponential backoff | v2 |
| 34 | Three.js dice scope creep | 🟡 | CSS 3D dice — 2 hours not 2 days | v2 |
| 35 | D3 particle framerate | 🟡 | Hard cap 60, rAF only | v2 |
| 36 | Alignment variable naming | 🟡 | order_chaos + harm_harmony everywhere | v2 |
| 37 | ChromaDB concurrent write corruption | 🟡 | Single asyncio write queue | v2 |
| 38 | React Flow + world-spanning effects | 🟡 | Canvas approach preserved over per-node | v3 |
| 39 | Windows RAM pressure | 🟡 | 4 discipline rules + PowerShell monitor | v4 |
| 40 | ChoicePanel active during generation | 🟡 | Disabled when is_generating=true | v5 |
| 41 | Combat summary missing from SQLite recency | 🟡 | summarizer writes to BOTH ChromaDB + SQLite | v5 |
| 42 | Session not reloadable after prune | 🟡 | resume_player_session() loads from SQLite if not in memory | v5 |

---

| 43 | Client-server dice desync | 🔴 | Server rolls first → dice_result WS → frontend animates to exact value | v6 |
| 44 | Silent vote resolution (game halts) | 🔴 | finalize_vote() calls stream_dm_response() with synthetic action at end | v6 |
| 45 | Hanging broadcaster blocks all players | 🔴 | broadcast() uses asyncio.gather(return_exceptions=True) — dead sockets fail in isolation | v6 |
| 46 | tokenizer freeze in truncate_chunks | 🟠 | CHARS_PER_TOKEN = 3.5 ratio — zero deps, instantaneous, event loop safe | v6 |

---

**46 flaws. 6 versions. One indestructible architecture.**
**LoreWeaver v6 — THE ABSOLUTE FINAL. Lock it. Open Claude Code. Start Week 0.**