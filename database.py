import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spanish TEXT NOT NULL,
                russian TEXT NOT NULL,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_shown INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                UNIQUE(spanish)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                finished_at DATETIME,
                direction TEXT,
                total_words INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                wrong INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                time TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                reminders_enabled INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def add_words(words: list[dict]) -> tuple[int, int]:
    added = 0
    skipped = 0
    async with aiosqlite.connect(DB_PATH) as db:
        for word in words:
            try:
                await db.execute(
                    "INSERT INTO words (spanish, russian) VALUES (?, ?)",
                    (word["spanish"].strip(), word["russian"].strip())
                )
                added += 1
            except aiosqlite.IntegrityError:
                skipped += 1
        await db.commit()
    return added, skipped


async def get_words_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM words") as cursor:
            row = await cursor.fetchone()
            return row[0]


async def get_random_words(limit: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, spanish, russian FROM words ORDER BY RANDOM() LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def update_word_stats(word_id: int, correct: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        if correct:
            await db.execute(
                "UPDATE words SET total_shown = total_shown+1, correct_count = correct_count+1 WHERE id=?",
                (word_id,)
            )
        else:
            await db.execute(
                "UPDATE words SET total_shown = total_shown+1, wrong_count = wrong_count+1 WHERE id=?",
                (word_id,)
            )
        await db.commit()


async def get_hard_words(limit: int = 5) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT spanish, russian, wrong_count FROM words
               WHERE wrong_count > 0 ORDER BY wrong_count DESC LIMIT ?""",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def clear_words():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM words")
        await db.commit()


async def get_all_words_for_export() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT spanish, russian FROM words") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def create_session(direction: str, total_words: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO sessions (direction, total_words) VALUES (?, ?)",
            (direction, total_words)
        )
        await db.commit()
        return cursor.lastrowid


async def finish_session(session_id: int, correct: int, wrong: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE sessions SET finished_at=CURRENT_TIMESTAMP,
               correct=?, wrong=? WHERE id=?""",
            (correct, wrong, session_id)
        )
        await db.commit()


async def get_global_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM words") as c:
            words_total = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM sessions WHERE finished_at IS NOT NULL") as c:
            sessions_total = (await c.fetchone())[0]
        async with db.execute("SELECT SUM(correct), SUM(wrong) FROM sessions") as c:
            row = await c.fetchone()
            correct_total = row[0] or 0
            wrong_total = row[1] or 0
        async with db.execute(
            "SELECT started_at FROM sessions ORDER BY id DESC LIMIT 1"
        ) as c:
            last = await c.fetchone()
            last_session = last[0] if last else "—"
    return {
        "words_total": words_total,
        "sessions_total": sessions_total,
        "correct_total": correct_total,
        "wrong_total": wrong_total,
        "last_session": last_session,
    }


async def set_reminders_enabled(user_id: int, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO settings (user_id, reminders_enabled)
               VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET reminders_enabled=excluded.reminders_enabled""",
            (user_id, int(enabled))
        )
        await db.commit()


async def get_reminders_enabled(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT reminders_enabled FROM settings WHERE user_id=?", (user_id,)
        ) as c:
            row = await c.fetchone()
            return bool(row[0]) if row else False


async def save_reminder_times(user_id: int, times: list[str]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM reminders WHERE user_id=?", (user_id,))
        for t in times:
            await db.execute(
                "INSERT INTO reminders (user_id, time) VALUES (?, ?)", (user_id, t)
            )
        await db.commit()


async def get_reminder_times(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT time FROM reminders WHERE user_id=?", (user_id,)
        ) as c:
            rows = await c.fetchall()
            return [r[0] for r in rows]


async def get_all_reminder_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT r.user_id, r.time FROM reminders r
               JOIN settings s ON s.user_id = r.user_id
               WHERE s.reminders_enabled = 1"""
        ) as c:
            rows = await c.fetchall()
            return [dict(r) for r in rows]
