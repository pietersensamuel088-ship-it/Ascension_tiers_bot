"""
Unit & Integration Tests for Ascension Tiers Discord Bot
"""

import asyncio
import os
import time
from config import GAMEMODES, COOLDOWN_SECONDS, OWNER_ID
from database import Database
from mojang import resolve_minecraft_player
import embeds

TEST_DB_PATH = "test_ascension.db"

def run_async(coro):
    return asyncio.run(coro)

def setup_function():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def teardown_function():
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

def test_link_and_unlink():
    async def _test():
        db = Database(TEST_DB_PATH)
        await db.init_db()

        discord_id = 123456789
        username = "Technoblade"
        uuid_str = "b876ec32e396476ba1158438d83c67d4"

        # Link
        success = await db.link_account(discord_id, username, uuid_str)
        assert success is True

        # Retrieve
        acc = await db.get_linked_account(discord_id)
        assert acc is not None
        assert acc["mc_username"] == username
        assert acc["mc_uuid"] == uuid_str

        # Unlink
        unlinked = await db.unlink_account(discord_id)
        assert unlinked is True
        assert await db.get_linked_account(discord_id) is None

    run_async(_test())


def test_queue_flow():
    async def _test():
        db = Database(TEST_DB_PATH)
        await db.init_db()

        gamemode = "sword"
        user1 = 111111
        user2 = 222222

        # Add to queue
        assert await db.add_to_queue(gamemode, user1) is True
        assert await db.add_to_queue(gamemode, user2) is True
        assert await db.add_to_queue(gamemode, user1) is False  # Cannot double add

        # Members list
        members = await db.get_queue_members(gamemode)
        assert members == [user1, user2]

        # Is in queue
        assert await db.is_in_queue(user1, gamemode) is True
        assert await db.is_in_queue(333333, gamemode) is False

        # Pop
        popped = await db.pop_next_in_queue(gamemode)
        assert popped == user1

        remaining = await db.get_queue_members(gamemode)
        assert remaining == [user2]

        popped2 = await db.pop_next_in_queue(gamemode)
        assert popped2 == user2
        assert await db.pop_next_in_queue(gamemode) is None

    run_async(_test())


def test_active_test_and_cooldown():
    async def _test():
        db = Database(TEST_DB_PATH)
        await db.init_db()

        thread_id = 999888777
        gamemode = "axe"
        tester_id = 555555
        player_id = 666666

        await db.create_active_test(thread_id, gamemode, tester_id, player_id)
        active = await db.get_active_test(thread_id)
        assert active is not None
        assert active["player_id"] == player_id
        assert active["gamemode"] == gamemode

        # Record Result
        await db.record_tier_result(player_id, gamemode, "HT4", tester_id, notes="Clean 3-0")
        await db.delete_active_test(thread_id)

        assert await db.get_active_test(thread_id) is None

        # Verify Tiers
        tiers = await db.get_player_tiers(player_id)
        assert tiers.get(gamemode) == "HT4"

        # Verify History
        hist = await db.get_player_test_history(player_id)
        assert len(hist) == 1
        assert hist[0]["tier"] == "HT4"
        assert hist[0]["notes"] == "Clean 3-0"

        # Verify Cooldown
        cd = await db.get_cooldown_remaining(player_id, gamemode)
        assert cd > 86000

    run_async(_test())


def test_mojang_resolver():
    async def _test():
        res = await resolve_minecraft_player("Notch")
        assert res is not None
        assert res["username"].lower() == "notch"
        assert len(res["uuid"]) == 32
        assert "avatar_url" in res

    run_async(_test())


def test_embed_generation():
    q_embed = embeds.build_queue_embed("sword", True, [{"mention": "<@123>", "ign": "TestPlayer"}])
    assert "SWORD QUEUE" in q_embed.title
    assert "OPEN FOR TESTING" in q_embed.description

    l_embed = embeds.build_link_embed()
    assert "MINECRAFT VERIFICATION" in l_embed.title
