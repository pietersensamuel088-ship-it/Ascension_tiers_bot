"""
Ascension Tiers - Main Discord Bot Runner
Minecraft PvP Tier Testing Bot for South Africa (ZA).
Structured cleanly without Cogs.
"""

import os
import sys
import logging
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal

from config import (
    DISCORD_TOKEN,
    GUILD_ID,
    OWNER_ID,
    FRIEND_ID,
    AUTHORIZED_OWNERS,
    OWNER_ROLE_ID,
    RESULTS_CHANNEL_ID,
    LINK_CHANNEL_ID,
    GAMEMODES,
    CHANNEL_TO_GAMEMODE,
    TESTER_ALLOWED_TIERS,
    ALL_TIERS,
    HIGH_TIER_TESTER_ROLES,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_DANGER,
    COLOR_GOLD,
    COLOR_CYBER
)
from database import Database
from mojang import resolve_minecraft_player
import embeds
from views import (
    LinkModal,
    LinkView,
    QueueView,
    PersistentTestingSessionView,
    ResultSubmitModal,
    is_user_tester,
    update_queue_embed_message
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AscensionBot")

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

# Bot initialization (No Cogs)
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

db = Database()


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Connected Guilds: {[g.name for g in bot.guilds]}")

    # Set Bot Presence
    activity = discord.Activity(
        type=discord.ActivityType.competing,
        name="Ascension Tiers 🇿🇦 | /help"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)


async def setup_hook():
    """Initializes SQLite database, registers persistent views, and syncs slash commands."""
    await db.init_db()
    logger.info("Database initialized successfully.")

    # Register persistent views for buttons to survive bot restarts
    bot.add_view(LinkView(db))
    bot.add_view(QueueView("", db))
    bot.add_view(PersistentTestingSessionView(db))
    logger.info("Persistent views registered.")

    # Sync slash commands with Discord
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
        logger.info(f"Synced {len(synced)} slash commands to Guild ID {GUILD_ID}.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

bot.setup_hook = setup_hook


# =========================================================================
# SLASH COMMANDS (Strictly NO underscores in command names!)
# =========================================================================

# --- 1. /help ---
@bot.tree.command(name="help", description="Learn how Ascension Tiers works and view all available commands.")
async def cmd_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ ASCENSION TIERS — BOT GUIDE & COMMANDS 🇿🇦",
        description=(
            "Welcome to **Ascension Tiers**, the official Minecraft PvP tier testing platform for South Africa!\n\n"
            "### 🎮 Player Guide:\n"
            "1. **Link Account:** Connect your Minecraft username with `/link`.\n"
            "2. **Join a Queue:** Go to any queue channel (e.g. `sword-q`, `axe-q`) and click **Join Queue**.\n"
            "3. **Testing:** When a tester pulls you, a private thread is created for your matches.\n"
            "4. **Get Ranked:** The tester submits your score and your tier role is awarded automatically!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 📜 Available Slash Commands:\n"
            "• `/profile [player]` — View tier rankings, skin head, and test history\n"
            "• `/link [ign]` — Link your Minecraft account via username or UUID\n"
            "• `/unlink` — Unlink your Minecraft account\n"
            "• `/queues` — Overview of all 11 testing queues\n"
            "• `/history [player]` — View detailed past test records\n"
            "• `/open [gamemode]` — *(Testers)* Open a queue for testing\n"
            "• `/close [gamemode]` — *(Testers)* Close a queue\n"
            "• `/pull [gamemode]` — *(Testers)* Pull the next waiting player into a private thread\n"
            "• `/result [tier] [notes]` — *(Testers)* Submit official tier test result\n"
            "• `/cancel [reason]` — *(Testers)* Cancel active test session\n"
            "• `/setup [target]` — *(Admins)* Deploy persistent queue or link panels\n"
            "• `/owner` — *Special command for TTVRecod*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_PRIMARY
    )
    embed.set_footer(text="Ascension Tiers • ZA Region", icon_url=bot.user.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- 2. /link ---
@bot.tree.command(name="link", description="Link your Minecraft username or UUID to your Discord account.")
@app_commands.describe(ign="Your Minecraft Username or UUID")
async def cmd_link(interaction: discord.Interaction, ign: Optional[str] = None):
    if ign is None:
        # Open Modal
        await interaction.response.send_modal(LinkModal(db))
        return

    await interaction.response.defer(ephemeral=True)
    player_data = await resolve_minecraft_player(ign)
    if not player_data:
        await interaction.followup.send(
            "❌ **Could not verify that Minecraft account!** Please check the spelling or provide a valid UUID.",
            ephemeral=True
        )
        return

    username = player_data["username"]
    uuid_str = player_data["uuid"]
    await db.link_account(interaction.user.id, username, uuid_str)

    embed = discord.Embed(
        title="✅ MINECRAFT ACCOUNT LINKED",
        description=(
            f"Successfully linked {interaction.user.mention} to Minecraft account **`{username}`**!\n\n"
            f"**UUID:** `{uuid_str}`\n"
            f"You can now join any testing queue in Ascension Tiers."
        ),
        color=COLOR_SUCCESS
    )
    embed.set_thumbnail(url=player_data["avatar_url"])
    await interaction.followup.send(embed=embed, ephemeral=True)


# --- 3. /unlink ---
@bot.tree.command(name="unlink", description="Unlink your Minecraft account from your Discord profile.")
@app_commands.describe(player="Staff option: unbind a specific player")
async def cmd_unlink(interaction: discord.Interaction, player: Optional[discord.Member] = None):
    target = player if (player and interaction.user.guild_permissions.administrator) else interaction.user
    removed = await db.unlink_account(target.id)
    if removed:
        await interaction.response.send_message(
            f"✅ Unlinked Minecraft account for {target.mention}.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"⚠️ No linked Minecraft account was found for {target.mention}.",
            ephemeral=True
        )


# --- 4. /profile ---
@bot.tree.command(name="profile", description="View a player's official tier profile and testing history.")
@app_commands.describe(player="The player whose profile you want to inspect")
async def cmd_profile(interaction: discord.Interaction, player: Optional[discord.Member] = None):
    target = player or interaction.user
    await interaction.response.defer()

    mc_data = await db.get_linked_account(target.id)
    if mc_data:
        mc_data["avatar_url"] = f"https://mc-heads.net/avatar/{mc_data['mc_uuid']}/128.png"

    tiers = await db.get_player_tiers(target.id)
    history = await db.get_player_test_history(target.id, limit=5)

    profile_embed = embeds.build_profile_embed(target, mc_data, tiers, history)
    await interaction.followup.send(embed=profile_embed)


# --- 5. /owner ---
@bot.tree.command(name="owner", description="TTVRecod That goat fr tho.")
async def cmd_owner(interaction: discord.Interaction):
    # Only allowed for TTVRecod (ID: 1162838607220965377)
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "❌ This command is exclusively reserved for **TTVRecod**.",
            ephemeral=True
        )
        return

    role = interaction.guild.get_role(OWNER_ROLE_ID)
    if not role:
        await interaction.response.send_message(
            f"⚠️ Owner role `{OWNER_ROLE_ID}` not found in this guild.",
            ephemeral=True
        )
        return

    if role in interaction.user.roles:
        await interaction.response.send_message(
            f"👑 You already hold the {role.mention} role, goat!",
            ephemeral=True
        )
        return

    try:
        await interaction.user.add_roles(role, reason="TTVRecod That goat fr tho. /owner command")
        await interaction.response.send_message(
            f"👑 **Granted {role.mention} to {interaction.user.mention}!** TTVRecod That goat fr tho.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Error assigning role: {e}", ephemeral=True)


# --- 6. /open ---
@bot.tree.command(name="open", description="Open a testing queue for players to join.")
@app_commands.describe(gamemode="Gamemode queue to open (or automatically detects current channel)")
async def cmd_open(
    interaction: discord.Interaction,
    gamemode: Optional[Literal[
        "sword", "axe", "uhc", "diapot", "smp", "nethpot", "speed", "cart", "mace", "spear", "hole"
    ]] = None
):
    target_mode = gamemode or CHANNEL_TO_GAMEMODE.get(interaction.channel_id)
    if not target_mode:
        await interaction.response.send_message(
            "❌ Please specify a gamemode or run this command inside a queue channel.",
            ephemeral=True
        )
        return

    if not is_user_tester(interaction.user, target_mode):
        await interaction.response.send_message("❌ You are not authorized to open this queue!", ephemeral=True)
        return

    cfg = GAMEMODES[target_mode]
    ch_id = cfg["channel_id"]
    await db.set_queue_state(target_mode, ch_id, is_open=True)

    await interaction.response.send_message(
        f"🟢 **The {cfg['name']} queue is now OPEN for testing!**",
        ephemeral=False
    )

    # Refresh queue embed if message exists
    q_state = await db.get_queue_state(target_mode)
    channel = interaction.guild.get_channel(ch_id)
    if q_state and q_state.get("message_id") and channel:
        await update_queue_embed_message(channel, q_state["message_id"], target_mode, db, interaction.guild)


# --- 7. /close ---
@bot.tree.command(name="close", description="Close a testing queue to prevent new joins.")
@app_commands.describe(gamemode="Gamemode queue to close (or automatically detects current channel)")
async def cmd_close(
    interaction: discord.Interaction,
    gamemode: Optional[Literal[
        "sword", "axe", "uhc", "diapot", "smp", "nethpot", "speed", "cart", "mace", "spear", "hole"
    ]] = None
):
    target_mode = gamemode or CHANNEL_TO_GAMEMODE.get(interaction.channel_id)
    if not target_mode:
        await interaction.response.send_message(
            "❌ Please specify a gamemode or run this command inside a queue channel.",
            ephemeral=True
        )
        return

    if not is_user_tester(interaction.user, target_mode):
        await interaction.response.send_message("❌ You are not authorized to close this queue!", ephemeral=True)
        return

    cfg = GAMEMODES[target_mode]
    ch_id = cfg["channel_id"]
    await db.set_queue_state(target_mode, ch_id, is_open=False)

    await interaction.response.send_message(
        f"🔴 **The {cfg['name']} queue is now CLOSED.**",
        ephemeral=False
    )

    q_state = await db.get_queue_state(target_mode)
    channel = interaction.guild.get_channel(ch_id)
    if q_state and q_state.get("message_id") and channel:
        await update_queue_embed_message(channel, q_state["message_id"], target_mode, db, interaction.guild)


# --- 8. /pull ---
@bot.tree.command(name="pull", description="Pull the next player from the queue into a private testing thread.")
@app_commands.describe(gamemode="Gamemode queue to pull from (or automatically detects current channel)")
async def cmd_pull(
    interaction: discord.Interaction,
    gamemode: Optional[Literal[
        "sword", "axe", "uhc", "diapot", "smp", "nethpot", "speed", "cart", "mace", "spear", "hole"
    ]] = None
):
    target_mode = gamemode or CHANNEL_TO_GAMEMODE.get(interaction.channel_id)
    if not target_mode:
        await interaction.response.send_message(
            "❌ Please specify a gamemode or run this command inside a queue channel.",
            ephemeral=True
        )
        return

    if not is_user_tester(interaction.user, target_mode):
        await interaction.response.send_message(
            "❌ You do not have tester permissions for this queue!",
            ephemeral=True
        )
        return

    next_player_id = await db.pop_next_in_queue(target_mode)
    if not next_player_id:
        await interaction.response.send_message("⚠️ The queue is empty! Nobody waiting.", ephemeral=True)
        return

    player_member = interaction.guild.get_member(next_player_id)
    if not player_member:
        await interaction.response.send_message("⚠️ The next player in queue is no longer in the server.", ephemeral=True)
        return

    cfg = GAMEMODES[target_mode]
    channel = interaction.guild.get_channel(cfg["channel_id"]) or interaction.channel

    mc_data = await db.get_linked_account(player_member.id)
    mc_name = mc_data["mc_username"] if mc_data else player_member.name

    try:
        thread = await channel.create_thread(
            name=f"testing-{mc_name}",
            auto_archive_duration=1440,
            type=discord.ChannelType.private_thread,
            invitable=False
        )
    except Exception:
        thread = await channel.create_thread(
            name=f"testing-{mc_name}",
            auto_archive_duration=1440
        )

    await thread.add_user(interaction.user)
    await thread.add_user(player_member)

    await db.create_active_test(thread.id, target_mode, interaction.user.id, player_member.id)

    session_embed = embeds.build_session_embed(target_mode, player_member, interaction.user, mc_data)
    session_view = PersistentTestingSessionView(db)
    await thread.send(
        content=f"⚔️ {player_member.mention} pulled by tester {interaction.user.mention}!",
        embed=session_embed,
        view=session_view
    )

    await interaction.response.send_message(
        f"✅ Pulled {player_member.mention}! Private testing thread: {thread.mention}",
        ephemeral=True
    )

    # Refresh queue embed
    q_state = await db.get_queue_state(target_mode)
    if q_state and q_state.get("message_id"):
        await update_queue_embed_message(channel, q_state["message_id"], target_mode, db, interaction.guild)


# --- 9. /result ---
@bot.tree.command(name="result", description="Submit a tier test result inside a testing thread.")
@app_commands.describe(
    tier="Awarded tier (e.g. LT5, HT5, LT4, HT4)",
    notes="Match score or tester notes (e.g. 3-0, great aim)"
)
async def cmd_result(
    interaction: discord.Interaction,
    tier: str,
    notes: Optional[str] = ""
):
    active_test = await db.get_active_test(interaction.channel_id)
    if not active_test:
        await interaction.response.send_message(
            "⚠️ This command can only be used inside an active private testing thread!",
            ephemeral=True
        )
        return

    gamemode = active_test["gamemode"]
    tester_id = active_test["tester_id"]
    player_id = active_test["player_id"]

    if interaction.user.id != tester_id and not is_user_tester(interaction.user, gamemode):
        await interaction.response.send_message(
            "❌ Only the assigned tester or authorized staff can submit results!",
            ephemeral=True
        )
        return

    awarded_tier = tier.strip().upper()
    is_high_tier = (
        interaction.user.id in AUTHORIZED_OWNERS or
        any(r.id in HIGH_TIER_TESTER_ROLES for r in interaction.user.roles)
    )
    valid_list = ALL_TIERS if is_high_tier else TESTER_ALLOWED_TIERS
    if awarded_tier not in valid_list:
        await interaction.response.send_message(
            f"❌ **Invalid tier!** Permitted tiers: `{'`, `'.join(valid_list)}`.",
            ephemeral=True
        )
        return

    await interaction.response.defer()
    player_member = interaction.guild.get_member(player_id)
    if not player_member:
        await interaction.followup.send("❌ Player not found in guild.")
        return

    # Record in DB
    await db.record_tier_result(player_id, gamemode, awarded_tier, interaction.user.id, notes or "")
    await db.delete_active_test(interaction.channel_id)

    # Assign role
    cfg = GAMEMODES.get(gamemode, {})
    roles_map = cfg.get("roles", {})
    target_role_id = roles_map.get(awarded_tier)
    role_msg = ""

    if target_role_id:
        target_role = interaction.guild.get_role(target_role_id)
        if target_role:
            try:
                # Remove conflicting tiers for this gamemode
                for rid in roles_map.values():
                    if rid != target_role_id and any(r.id == rid for r in player_member.roles):
                        old_r = interaction.guild.get_role(rid)
                        if old_r:
                            await player_member.remove_roles(old_r, reason="Tier update")
                await player_member.add_roles(target_role, reason=f"Ascension Tier Result: {awarded_tier}")
                role_msg = f"Assigned role: {target_role.mention}"
            except Exception as e:
                role_msg = f"*(Role error: {e})*"
    else:
        role_msg = f"{awarded_tier.lower()} {gamemode} rank is put in broski dm TTVRecod with the role id for the category"

    # Post to #tier-results
    results_ch = interaction.guild.get_channel(RESULTS_CHANNEL_ID)
    mc_data = await db.get_linked_account(player_id)
    if results_ch:
        ann = embeds.build_result_announcement_embed(
            player_member, mc_data, gamemode, awarded_tier, interaction.user, notes or ""
        )
        await results_ch.send(embed=ann)

    success_embed = discord.Embed(
        title="🎉 TEST COMPLETED & SAVED",
        description=(
            f"**Player:** {player_member.mention}\n"
            f"**Gamemode:** {cfg.get('name', gamemode.title())}\n"
            f"**Awarded Tier:** `{awarded_tier}`\n"
            f"**Status:** {role_msg}\n\n"
            f"*Closing thread in 10 seconds...*"
        ),
        color=COLOR_SUCCESS
    )
    await interaction.followup.send(embed=success_embed)

    await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.datetime.timedelta(seconds=10))
    try:
        thread = interaction.guild.get_thread(interaction.channel_id)
        if thread:
            await thread.edit(archived=True, locked=True)
    except Exception:
        pass


# --- 10. /cancel ---
@bot.tree.command(name="cancel", description="Cancel an active test session inside a testing thread.")
@app_commands.describe(reason="Reason for cancellation (optional)")
async def cmd_cancel(interaction: discord.Interaction, reason: Optional[str] = "No reason provided"):
    active_test = await db.get_active_test(interaction.channel_id)
    if not active_test:
        await interaction.response.send_message(
            "⚠️ This command can only be used inside an active private testing thread!",
            ephemeral=True
        )
        return

    gamemode = active_test["gamemode"]
    tester_id = active_test["tester_id"]

    if interaction.user.id != tester_id and not is_user_tester(interaction.user, gamemode):
        await interaction.response.send_message(
            "❌ Only the assigned tester or authorized staff can cancel this session!",
            ephemeral=True
        )
        return

    await db.delete_active_test(interaction.channel_id)

    cancel_embed = discord.Embed(
        title="🛑 TEST SESSION CANCELLED",
        description=(
            f"This test session was cancelled by {interaction.user.mention}.\n"
            f"**Reason:** *{reason}*\n"
            f"The player is freed to join queues again.\n\n"
            f"*Closing thread in 5 seconds...*"
        ),
        color=COLOR_DANGER
    )
    await interaction.response.send_message(embed=cancel_embed)

    await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.datetime.timedelta(seconds=5))
    try:
        thread = interaction.guild.get_thread(interaction.channel_id)
        if thread:
            await thread.edit(archived=True, locked=True)
    except Exception:
        pass


# --- 11. /queues ---
@bot.tree.command(name="queues", description="Overview of all 11 testing queues and current waiting counts.")
async def cmd_queues(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 ASCENSION TIERS — ALL QUEUES OVERVIEW 🇿🇦",
        description="Current status and waiting counts for all official tier queues:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=COLOR_PRIMARY
    )

    for key, cfg in GAMEMODES.items():
        state = await db.get_queue_state(key)
        is_open = bool(state.get("is_open", 1)) if state else True
        members = await db.get_queue_members(key)
        status_dot = "🟢 Open" if is_open else "🔴 Closed"
        channel_mention = f"<#{cfg['channel_id']}>"
        embed.add_field(
            name=f"{cfg['emoji']} {cfg['name']}",
            value=f"• Channel: {channel_mention}\n• Status: **{status_dot}**\n• Waiting: **{len(members)}**",
            inline=True
        )

    embed.set_footer(text="Ascension Tiers • ZA Region", icon_url=bot.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)


# --- 12. /history ---
@bot.tree.command(name="history", description="View all past tier tests recorded for a player.")
@app_commands.describe(player="The player whose history to inspect")
async def cmd_history(interaction: discord.Interaction, player: Optional[discord.Member] = None):
    target = player or interaction.user
    records = await db.get_player_test_history(target.id, limit=15)

    if not records:
        await interaction.response.send_message(
            f"ℹ️ No official testing history found for {target.mention}.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"📜 TIER TESTING HISTORY — {target.display_name.upper()}",
        description=f"Official records for {target.mention} (Showing latest {len(records)} tests):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=COLOR_PRIMARY
    )

    for item in records:
        gm = GAMEMODES.get(item["gamemode"], {}).get("name", item["gamemode"].title())
        tier = item["tier"]
        tester_m = f"<@{item['tester_id']}>"
        ts = f"<t:{item['tested_at']}:F>"
        notes_txt = f"\n*Notes: {item['notes']}*" if item.get("notes") else ""
        embed.add_field(
            name=f"⚔️ {gm} — Tier `{tier}`",
            value=f"• Tested by: {tester_m}\n• Date: {ts}{notes_txt}",
            inline=False
        )

    embed.set_footer(text="Ascension Tiers • Tier Records Database")
    await interaction.response.send_message(embed=embed)


# --- 13. /clearqueue ---
@bot.tree.command(name="clearqueue", description="Clear all waiting players from a queue (Staff only).")
@app_commands.describe(gamemode="Queue to clear")
async def cmd_clearqueue(
    interaction: discord.Interaction,
    gamemode: Literal[
        "sword", "axe", "uhc", "diapot", "smp", "nethpot", "speed", "cart", "mace", "spear", "hole"
    ]
):
    if not (interaction.user.guild_permissions.administrator or interaction.user.id in AUTHORIZED_OWNERS):
        await interaction.response.send_message("❌ Administrator permission required.", ephemeral=True)
        return

    members = await db.get_queue_members(gamemode)
    for uid in members:
        await db.remove_from_queue(gamemode, uid)

    cfg = GAMEMODES[gamemode]
    await interaction.response.send_message(
        f"🧹 Cleared {len(members)} players from the **{cfg['name']}** queue.",
        ephemeral=True
    )

    # Refresh embed
    q_state = await db.get_queue_state(gamemode)
    channel = interaction.guild.get_channel(cfg["channel_id"])
    if q_state and q_state.get("message_id") and channel:
        await update_queue_embed_message(channel, q_state["message_id"], gamemode, db, interaction.guild)


# --- 14. /setup ---
@bot.tree.command(name="setup", description="Deploy the persistent queue or account linking panels.")
@app_commands.describe(target="What to set up: link (link channel), current (this channel's queue), or all (all 11 queues)")
async def cmd_setup(
    interaction: discord.Interaction,
    target: Literal["link", "current", "all"]
):
    if not (interaction.user.guild_permissions.administrator or interaction.user.id in AUTHORIZED_OWNERS):
        await interaction.response.send_message("❌ Administrator permission required.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if target == "link":
        link_ch = interaction.guild.get_channel(LINK_CHANNEL_ID) or interaction.channel
        link_embed = embeds.build_link_embed()
        link_view = LinkView(db)
        await link_ch.send(embed=link_embed, view=link_view)
        await interaction.followup.send(f"✅ Sent persistent Link Panel to {link_ch.mention}!", ephemeral=True)
        return

    if target == "current":
        gm = CHANNEL_TO_GAMEMODE.get(interaction.channel_id)
        if not gm:
            await interaction.followup.send("❌ This channel is not mapped to any known gamemode queue.", ephemeral=True)
            return

        member_ids = await db.get_queue_members(gm)
        member_data = []
        for uid in member_ids:
            mem = interaction.guild.get_member(uid)
            mc_info = await db.get_linked_account(uid)
            member_data.append({
                "mention": mem.mention if mem else f"<@{uid}>",
                "ign": mc_info["mc_username"] if mc_info else "Unlinked"
            })

        q_embed = embeds.build_queue_embed(gm, True, member_data)
        q_view = QueueView(gm, db)
        msg = await interaction.channel.send(embed=q_embed, view=q_view)
        await db.set_queue_message_id(gm, interaction.channel_id, msg.id)
        await interaction.followup.send(f"✅ Sent persistent queue panel for **{GAMEMODES[gm]['name']}**!", ephemeral=True)
        return

    if target == "all":
        count = 0
        for gm_key, gm_cfg in GAMEMODES.items():
            ch = interaction.guild.get_channel(gm_cfg["channel_id"])
            if ch:
                member_ids = await db.get_queue_members(gm_key)
                member_data = []
                for uid in member_ids:
                    mem = interaction.guild.get_member(uid)
                    mc_info = await db.get_linked_account(uid)
                    member_data.append({
                        "mention": mem.mention if mem else f"<@{uid}>",
                        "ign": mc_info["mc_username"] if mc_info else "Unlinked"
                    })
                q_embed = embeds.build_queue_embed(gm_key, True, member_data)
                q_view = QueueView(gm_key, db)
                msg = await ch.send(embed=q_embed, view=q_view)
                await db.set_queue_message_id(gm_key, ch.id, msg.id)
                count += 1
                await asyncio.sleep(0.5)

        await interaction.followup.send(f"✅ Successfully deployed queue panels to {count} channels!", ephemeral=True)


# =========================================================================
# MAIN EXECUTION
# =========================================================================

async def main():
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is missing! Please configure .env.")
        sys.exit(1)

    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
