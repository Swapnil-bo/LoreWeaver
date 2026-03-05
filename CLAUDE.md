# CLAUDE.md — LoreWeaver

## WHO YOU ARE WORKING WITH
You are pair-programming with Swapnil on LoreWeaver — a multiplayer tabletop RPG
where a local Mistral 7B LLM acts as a living Dungeon Master with a 2D moral
alignment system, RAG memory pipeline, WebSocket multiplayer, and a React Flow world map.

Full architecture is in: `LoreWeaver_Blueprint_v6_Final.md`
When uncertain about ANY decision → read the relevant section before writing code.
If your instinct conflicts with a constraint below → follow the constraint.

---

## PRIME DIRECTIVE

**ONE file per response. Always.**
Write the file. Stop. Wait for Swapnil to run the verify command and confirm it passed.
Do not write the next file until you hear "passed" or "ok next".
Do not write multiple files "to save time". This breaks everything.

---

## 14 HARD CONSTRAINTS — NEVER VIOLATE THESE

```
1.  main.py MUST start with the pysqlite3 override — 3 lines, before ANY import.
    Skipping this = ChromaDB crashes on Windows on Day 1.

2.  embed() is ASYNC — it calls asyncio.to_thread(_embed_sync) internally.
    Never call it with `embed(query)`. Always `await embed(query)`.
    See: rag/embedder.py → Section 7.1

3.  ALL SQLite calls use aiosqlite — never raw sqlite3 in async context.
    Raw sqlite3 in a FastAPI route = event loop freeze = WebSocket drops.
    See: db/sqlite_store.py → Section 11.1

4.  ALL Ollama HTTP calls are wrapped in `async with _ollama_lock`.
    Concurrent Ollama requests duplicate KV cache → VRAM OOM on RTX 3050.
    See: engine/dm_engine.py → Section 8.1

5.  asyncio.gather() for RAG queries — NEVER sequential awaits.
    Sequential = ~400ms. Concurrent = ~100ms. Free win, one line change.
    See: rag/retriever.py → Section 7.5

6.  useStoreApi() for D3 canvas — NOT useViewport().
    useViewport() has async lag. useStoreApi() reads synchronously every frame.
    See: AlignmentOverlay.jsx → Section 12.3

7.  useRef + requestAnimationFrame for NarrativeBlock — NOT useState.
    useState = 50 re-renders/sec during token stream = UI freeze.
    See: NarrativeBlock.jsx → Section 12.1

8.  updateRegions() mutates node.data only — NEVER replaces full nodes array.
    Full array replacement = React Flow unmounts every node + viewport snaps to (0,0).
    See: gameStore.js → Section 12.4

9.  is_generating flag checked before EVERY exploration action (per session).
    Without this: two simultaneous actions = two parallel DM streams = garbled text.
    See: ws_manager.py → Section 10.1

10. disconnect() returned from App.jsx useEffect cleanup.
    Without this: every Ctrl+S during dev creates a zombie WebSocket.
    50 saves = FastAPI broadcasting to 50 dead sockets = crash.
    See: App.jsx → Section 12.5

11. truncate_chunks() uses CHARS_PER_TOKEN = 3.5 — NEVER import transformers tokenizer.
    Tokenizer init = synchronous CPU freeze 100-300ms on every player action.
    See: rag/retriever.py → Section 7.3

12. broadcast() uses asyncio.gather(return_exceptions=True) — NEVER sequential for-loop.
    One sleeping laptop in sequential loop = stream paused for ALL players.
    See: ws_manager.py → Section 10.5

13. finalize_vote() calls stream_dm_response() at the end with synthetic action.
    Without this: players vote, see the result, and the DM never speaks again. Ever.
    See: vote_system.py → Section 10.4

14. DiceRoller NEVER calls Math.random() for game values.
    Server rolls → sends dice_result WS message → frontend animates to that exact value.
    See: DiceRoller.jsx → Section 12.6
```

---

## BUILD ORDER — 20 STEPS, ONE FILE AT A TIME

Complete each step fully before moving to the next.
Run the verify command. Wait for confirmation. Then proceed.

```
PHASE 1 — FOUNDATION (Days 1-3)

Step 1:  backend/config.py
         verify: python -c "from config import OLLAMA_BASE_URL, OLLAMA_MODEL; print(OLLAMA_BASE_URL, OLLAMA_MODEL)"
         expected: http://localhost:11434 mistral:7b-instruct-q3_K_S

Step 2:  backend/models/alignment.py
         verify: python -c "from models.alignment import WorldAlignment; w=WorldAlignment(); print(w.quadrant, w.mood_descriptor)"
         expected: justice mildly justice

Step 3:  backend/models/characters.py
         verify: python -c "from models.characters import CLASS_STAT_TEMPLATES, CharacterClass; print(CLASS_STAT_TEMPLATES[CharacterClass.warrior].ac)"
         expected: 11

Step 4:  backend/models/combat.py
         verify: python -c "from models.combat import EnemyState, EnemyBehavior; e=EnemyState(enemy_id='x',name='Goblin',hp=10,max_hp=10,ac=12,damage_dice='1d6'); print(e.is_alive)"
         expected: True

Step 5:  backend/models/narrative.py
         verify: python -c "from models.narrative import DM_RESPONSE_SCHEMA; assert 'narrative' in DM_RESPONSE_SCHEMA['properties']; print('ok')"
         expected: ok

Step 6:  backend/models/region.py
         verify: python -c "from models.region import Region, NPC; print('ok')"
         expected: ok

Step 7:  backend/models/session.py
         verify: python -c "from models.session import GameSession; fields=GameSession.model_fields; assert 'is_generating' in fields; print('ok')"
         expected: ok

Step 8:  backend/db/sqlite_store.py
         verify: python -c "import asyncio; from db.sqlite_store import init_db; asyncio.run(init_db()); print('WAL ready')"
         expected: WAL ready

Step 9:  backend/rag/embedder.py
         verify: python scripts/check_04_embeddings.py
         expected: async thread confirmed, < 200ms per query

Step 10: backend/rag/collections.py
         verify: python scripts/check_03_chroma_thread.py
         expected: Non-blocking confirmed

Step 11: backend/rag/retriever.py
         verify: python -c "import asyncio,inspect; from rag.retriever import assemble_context,truncate_chunks; assert asyncio.iscoroutinefunction(assemble_context); from rag.retriever import CHARS_PER_TOKEN; assert CHARS_PER_TOKEN==3.5; print('ok')"
         expected: ok

Step 12: backend/rag/memory_manager.py
         verify: python -c "from rag.memory_manager import enforce_npc_memory_limit; print('ok')"
         expected: ok

Step 13: backend/engine/alignment_engine.py
         verify: python -c "from engine.alignment_engine import apply_alignment_shift; from models.alignment import WorldAlignment; w=apply_alignment_shift(WorldAlignment(),{'order_chaos_shift':25}); assert w.order_chaos==20.0; print('capped correctly:', w.order_chaos)"
         expected: capped correctly: 20.0

Step 14: backend/engine/dm_engine.py
         verify: python scripts/check_01_streaming.py
                 python scripts/check_02_json_format.py
                 python scripts/check_06_ollama_lock.py
         expected: first token < 2s, 20/20 JSON, lock serializes requests

Step 15: backend/engine/combat_engine.py
         verify: python -c "from engine.combat_engine import roll_dice,process_combat_action; r,rolls=roll_dice('2d6+3'); assert 5<=r<=15; print('dice ok:', r)"
         expected: dice ok: [5-15]

Step 16: backend/engine/world_engine.py
         verify: python -c "from engine.world_engine import summarize_and_clear_combat_log; print('ok')"
         expected: ok

Step 17: backend/multiplayer/ws_manager.py
         verify: python -c "import inspect; from multiplayer.ws_manager import broadcast; src=inspect.getsource(broadcast); assert 'return_exceptions=True' in src; print('concurrent broadcast confirmed')"
         expected: concurrent broadcast confirmed

Step 18: backend/multiplayer/session_manager.py
         verify: python -c "from multiplayer.session_manager import handle_connect, session_pruner, resume_player_session; print('ok')"
         expected: ok

Step 19: backend/multiplayer/vote_system.py
         verify: python -c "import inspect; from multiplayer.vote_system import finalize_vote; src=inspect.getsource(finalize_vote); assert 'stream_dm_response' in src; print('vote triggers DM confirmed')"
         expected: vote triggers DM confirmed

Step 20: backend/main.py
         verify: uvicorn main:app --reload
         expected: "✅ Ollama connected — mistral:7b-instruct-q3_K_S ready" printed, no errors
```

---

## HOW TO WORK WITH SWAPNIL

```
When Swapnil says "next" or "passed" → write the next file in the build order.
When Swapnil shares an error → fix ONLY that error in ONLY the affected file.
When Swapnil asks "why" → explain concisely before writing any code.
When Swapnil says "skip" → note it and move to the next step.
When uncertain about architecture → ask before writing, not after.
```

**Never do this:**
- Write 3 files because they "go together"
- Refactor something that wasn't asked for
- Add dependencies not in requirements.txt without flagging it
- Use any library not already in the blueprint

**Always do this:**
- Put the pysqlite3 override at the very top of main.py
- Check Section numbers in the blueprint before implementing anything non-trivial
- State which constraint you're following when it's relevant

---

## TECH STACK REFERENCE

```
Backend:    FastAPI + uvicorn + WebSockets
LLM:        Ollama (mistral:7b-instruct-q3_K_S) — localhost:11434
Embeddings: sentence-transformers all-MiniLM-L6-v2 — CPU only
Vector DB:  ChromaDB — asyncio.Queue + asyncio.to_thread writes
SQL DB:     SQLite via aiosqlite — WAL mode
Frontend:   React + Vite + Zustand + React Flow + D3 canvas
State:      gameStore.js (game state) + wsStore.js (WS + dispatcher)
```

---

## CURRENT STATUS

```
✅ mistral:7b-instruct-q3_K_S — 100% GPU, 4.0 GB VRAM confirmed
✅ Blueprint v6 locked — 46 flaws resolved
⬜ Week 0 checks (check_01 through check_06) — run before Day 1
⬜ seed_world.json — write before Day 4
⬜ Step 1: config.py — start here
```

---

*Full architecture reference: LoreWeaver_Blueprint_v6_Final.md*
*46 flaws. 6 versions. One architecture. Let's build.*