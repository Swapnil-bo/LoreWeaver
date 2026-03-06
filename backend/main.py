try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass
# ── Constraint #1: pysqlite3 override MUST be above ALL imports ───────────────

import asyncio
import json
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from db.sqlite_store import init_db
from multiplayer.session_manager import handle_connect, session_pruner, touch_session
from multiplayer.ws_manager import WebSocketManager, add_connection, remove_connection
from rag.collections import chroma_write_worker


ws_manager = WebSocketManager()


async def verify_ollama():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            models = [m["name"] for m in r.json().get("models", [])]
            assert any(OLLAMA_MODEL in m for m in models)
            logging.getLogger("uvicorn").info(f"Ollama connected -- {OLLAMA_MODEL} ready")
    except Exception as e:
        raise RuntimeError(f"[FAIL] Ollama not reachable: {e}\nRun: ollama serve")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await verify_ollama()
    asyncio.create_task(chroma_write_worker())   # ChromaDB write serializer
    asyncio.create_task(session_pruner())         # 15-min session TTL pruner
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str | None = None):
    await ws.accept()
    identity = await handle_connect(ws, token)
    session_id = identity.session_id

    if session_id:
        ws.state.player_id = identity.player_id
        await add_connection(session_id, ws)

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "ping":
                await ws.send_json({"type": "pong"})

            elif msg_type == "join_session":
                session_id = data.get("session_id")
                identity.session_id = session_id
                ws.state.player_id = identity.player_id
                await add_connection(session_id, ws)
                touch_session(session_id)

            elif msg_type == "player_action":
                if session_id:
                    from multiplayer.session_manager import get_session
                    session = get_session(session_id)
                    if session:
                        # Constraint #9: is_generating check before every exploration action
                        if session.is_generating:
                            await ws.send_json({
                                "type":   "action_rejected",
                                "reason": "The DM is speaking... wait for the story to unfold.",
                            })
                        else:
                            session.is_generating = True
                            touch_session(session_id)
                            try:
                                from engine.dm_engine import stream_dm_response
                                from rag.retriever import assemble_context
                                action = data.get("action", "")
                                rag = await assemble_context(
                                    session_id, action, session.current_scene.region_id)
                                context = {
                                    "world":         session.world_state,
                                    "region":        session.current_scene,
                                    "player_action": action,
                                    "rag":           rag,
                                }
                                await stream_dm_response(context, ws_manager, session_id)
                            finally:
                                session.is_generating = False

            elif msg_type == "vote_choice":
                if session_id:
                    from multiplayer.vote_system import get_active_vote
                    vote = get_active_vote(session_id)
                    if vote and not vote.resolved:
                        player_id = data.get("player_id")
                        choice_index = data.get("choice_index")
                        if player_id and choice_index is not None:
                            vote.votes[player_id] = choice_index

    except WebSocketDisconnect:
        if session_id:
            await remove_connection(session_id, ws)
    except Exception:
        if session_id:
            await remove_connection(session_id, ws)
