import time

import aiosqlite

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
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO sessions (session_id, data, updated_at) VALUES (?,?,?)",
            (session.session_id, session.model_dump_json(), time.time()))
        await db.commit()


async def load_session_from_sqlite(session_id: str) -> "GameSession | None":
    async with aiosqlite.connect(DB_PATH) as db:
        row = await db.execute_fetchall(
            "SELECT data FROM sessions WHERE session_id=?", (session_id,))
    if not row:
        return None
    from models.session import GameSession
    return GameSession.model_validate_json(row[0][0])


async def get_last_narrative_sqlite(session_id: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT summary FROM narrative_summaries WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
            (session_id,))
    return rows[0][0] if rows else ""
