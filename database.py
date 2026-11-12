"""
Ascension Tiers - SQLite Database Handler (aiosqlite)
Async storage for linked accounts, queues, active tests, tiers, and test history.
"""

import aiosqlite
import time
from typing import Optional, List, Dict, Any
from config import DATABASE_PATH, COOLDOWN_SECONDS

class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initializes all database tables and indexes."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS linked_accounts (
                    discord_id INTEGER PRIMARY KEY,
                    mc_username TEXT NOT NULL,
                    mc_uuid TEXT NOT NULL,
                    linked_at INTEGER NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS queues (
                    gamemode TEXT PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    is_open INTEGER DEFAULT 1,
                    message_id INTEGER
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS queue_members (
                    gamemode TEXT NOT NULL,
                    discord_id INTEGER NOT NULL,
                    joined_at INTEGER NOT NULL,
                    PRIMARY KEY (gamemode, discord_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS active_tests (
                    thread_id INTEGER PRIMARY KEY,
                    gamemode TEXT NOT NULL,
                    tester_id INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    started_at INTEGER NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS player_tiers (
                    discord_id INTEGER NOT NULL,
                    gamemode TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    updated_at INTEGER NOT NULL,
                    PRIMARY KEY (discord_id, gamemode)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS tier_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER NOT NULL,
                    gamemode TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    tester_id INTEGER NOT NULL,
                    tested_at INTEGER NOT NULL,
                    notes TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS cooldowns (
                    discord_id INTEGER NOT NULL,
                    gamemode TEXT NOT NULL,
                    last_tested_at INTEGER NOT NULL,
                    PRIMARY KEY (discord_id, gamemode)
                )
            """)

            await db.commit()

    # --- Linked Accounts ---
    async def link_account(self, discord_id: int, username: str, uuid_str: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO linked_accounts (discord_id, mc_username, mc_uuid, linked_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(discord_id) DO UPDATE SET
                    mc_username = excluded.mc_username,
                    mc_uuid = excluded.mc_uuid,
                    linked_at = excluded.linked_at
            """, (discord_id, username, uuid_str, int(time.time())))
            await db.commit()
            return True

    async def unlink_account(self, discord_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM linked_accounts WHERE discord_id = ?", (discord_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def get_linked_account(self, discord_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM linked_accounts WHERE discord_id = ?", (discord_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    # --- Queue Management ---
    async def get_queue_state(self, gamemode: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM queues WHERE gamemode = ?", (gamemode,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def set_queue_state(self, gamemode: str, channel_id: int, is_open: bool, message_id: Optional[int] = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO queues (gamemode, channel_id, is_open, message_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(gamemode) DO UPDATE SET
                    is_open = excluded.is_open,
                    message_id = COALESCE(excluded.message_id, queues.message_id)
            """, (gamemode, channel_id, 1 if is_open else 0, message_id))
            await db.commit()

    async def set_queue_message_id(self, gamemode: str, channel_id: int, message_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO queues (gamemode, channel_id, is_open, message_id)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(gamemode) DO UPDATE SET
                    message_id = excluded.message_id
            """, (gamemode, channel_id, message_id))
            await db.commit()

    async def add_to_queue(self, gamemode: str, discord_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    INSERT INTO queue_members (gamemode, discord_id, joined_at)
                    VALUES (?, ?, ?)
                """, (gamemode, discord_id, int(time.time())))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def remove_from_queue(self, gamemode: str, discord_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM queue_members WHERE gamemode = ? AND discord_id = ?
            """, (gamemode, discord_id))
            await db.commit()
            return cursor.rowcount > 0

    async def remove_from_all_queues(self, discord_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM queue_members WHERE discord_id = ?", (discord_id,))
            await db.commit()

    async def get_queue_members(self, gamemode: str) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT discord_id FROM queue_members
                WHERE gamemode = ?
                ORDER BY joined_at ASC
            """, (gamemode,))
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

    async def is_in_queue(self, discord_id: int, gamemode: Optional[str] = None) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            if gamemode:
                cursor = await db.execute("""
                    SELECT 1 FROM queue_members WHERE gamemode = ? AND discord_id = ?
                """, (gamemode, discord_id))
            else:
                cursor = await db.execute("""
                    SELECT 1 FROM queue_members WHERE discord_id = ?
                """, (discord_id,))
            row = await cursor.fetchone()
            return row is not None

    async def pop_next_in_queue(self, gamemode: str) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT discord_id FROM queue_members
                WHERE gamemode = ?
                ORDER BY joined_at ASC LIMIT 1
            """, (gamemode,))
            row = await cursor.fetchone()
            if not row:
                return None
            next_user_id = row[0]
            await db.execute("DELETE FROM queue_members WHERE gamemode = ? AND discord_id = ?", (gamemode, next_user_id))
            await db.commit()
            return next_user_id

    # --- Active Tests ---
    async def create_active_test(self, thread_id: int, gamemode: str, tester_id: int, player_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO active_tests (thread_id, gamemode, tester_id, player_id, started_at)
                VALUES (?, ?, ?, ?, ?)
            """, (thread_id, gamemode, tester_id, player_id, int(time.time())))
            await db.commit()

    async def get_active_test(self, thread_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM active_tests WHERE thread_id = ?", (thread_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def delete_active_test(self, thread_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM active_tests WHERE thread_id = ?", (thread_id,))
            await db.commit()

    async def is_player_in_test(self, player_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM active_tests WHERE player_id = ?", (player_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    # --- Tier Results & History ---
    async def record_tier_result(self, discord_id: int, gamemode: str, tier: str, tester_id: int, notes: str = ""):
        now = int(time.time())
        async with aiosqlite.connect(self.db_path) as db:
            # 1. Update player current tier
            await db.execute("""
                INSERT INTO player_tiers (discord_id, gamemode, tier, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(discord_id, gamemode) DO UPDATE SET
                    tier = excluded.tier,
                    updated_at = excluded.updated_at
            """, (discord_id, gamemode, tier, now))

            # 2. Append to testing log history
            await db.execute("""
                INSERT INTO tier_results (discord_id, gamemode, tier, tester_id, tested_at, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (discord_id, gamemode, tier, tester_id, now, notes))

            # 3. Apply cooldown
            await db.execute("""
                INSERT INTO cooldowns (discord_id, gamemode, last_tested_at)
                VALUES (?, ?, ?)
                ON CONFLICT(discord_id, gamemode) DO UPDATE SET
                    last_tested_at = excluded.last_tested_at
            """, (discord_id, gamemode, now))

            await db.commit()

    async def get_player_tiers(self, discord_id: int) -> Dict[str, str]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT gamemode, tier FROM player_tiers WHERE discord_id = ?
            """, (discord_id,))
            rows = await cursor.fetchall()
            return {r[0]: r[1] for r in rows}

    async def get_player_test_history(self, discord_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM tier_results
                WHERE discord_id = ?
                ORDER BY tested_at DESC
                LIMIT ?
            """, (discord_id, limit))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_cooldown_remaining(self, discord_id: int, gamemode: str) -> int:
        """Returns remaining cooldown seconds, or 0 if expired."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT last_tested_at FROM cooldowns
                WHERE discord_id = ? AND gamemode = ?
            """, (discord_id, gamemode))
            row = await cursor.fetchone()
            if not row:
                return 0
            elapsed = int(time.time()) - row[0]
            remaining = COOLDOWN_SECONDS - elapsed
            return max(0, remaining)
