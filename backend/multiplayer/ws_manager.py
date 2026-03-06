import asyncio

from fastapi import WebSocket

# ── Connection registry — keyed by session_id ─────────────────────────────────
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


# ── Constraint #12: broadcast uses asyncio.gather(return_exceptions=True) ─────
# NEVER a sequential for-loop. One sleeping laptop must not block all players.

async def broadcast(session_id: str, message: dict):
    """
    v6 FIX: asyncio.gather with return_exceptions=True.

    The bug: sequential `for ws in connections: await ws.send_json(msg)`
    A player's laptop goes to sleep -> TCP socket half-open for MINUTES.
    Server awaits acknowledgment from dead socket -> entire loop hangs.
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
    for ws in conns:
        if getattr(ws.state, "player_id", None) == player_id:
            try:
                await ws.send_json(message)
            except Exception:
                await remove_connection(session_id, ws)
            return


class WebSocketManager:
    """Thin class wrapper so other modules can type-hint against it."""

    async def broadcast(self, session_id: str, message: dict):
        await broadcast(session_id, message)

    async def send_to_player(self, session_id: str, player_id: str, message: dict):
        await send_to_player(session_id, player_id, message)

    async def add_connection(self, session_id: str, ws: WebSocket):
        await add_connection(session_id, ws)

    async def remove_connection(self, session_id: str, ws: WebSocket):
        await remove_connection(session_id, ws)
