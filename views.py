"""
Ascension Tiers - Interactive Views & Persistent Components
Handles Queue buttons, Account Linking modals, and Testing Session controls.
"""

import discord
from discord import ui
import time
from typing import Optional, Dict, Any, List

from config import (
    GAMEMODES,
    CHANNEL_TO_GAMEMODE,
    HIGH_TIER_TESTER_ROLES,
    AUTHORIZED_OWNERS,
    TESTER_ALLOWED_TIERS,
    ALL_TIERS,
    RESULTS_CHANNEL_ID,
    LINK_CHANNEL_ID,
    COLOR_SUCCESS,
    COLOR_DANGER,
    COLOR_PRIMARY
)
from database import Database
from mojang import resolve_minecraft_player
import embeds

def is_user_tester(member: discord.Member, gamemode_key: str) -> bool:
    """Checks whether a guild member is authorized to test for a gamemode."""
    if member.id in AUTHORIZED_OWNERS:
        return True
    if member.guild_permissions.administrator:
        return True
    
    # Check High Tier Tester roles
    for role in member.roles:
        if role.id in HIGH_TIER_TESTER_ROLES:
            return True

    # Check gamemode specific tester role
    cfg = GAMEMODES.get(gamemode_key, {})
    tester_role_id = cfg.get("tester_role_id")
    if tester_role_id and any(r.id == tester_role_id for r in member.roles):
        return True

    return False


async def update_queue_embed_message(
    channel: discord.TextChannel,
    message_id: int,
    gamemode_key: str,
    db: Database,
    guild: discord.Guild
):
    """Refreshes the live queue embed in the channel."""
    try:
        msg = await channel.fetch_message(message_id)
        queue_state = await db.get_queue_state(gamemode_key)
        is_open = bool(queue_state.get("is_open", 1)) if queue_state else True
        member_ids = await db.get_queue_members(gamemode_key)

        member_data_list = []
        for uid in member_ids:
            mem = guild.get_member(uid)
            mention_str = mem.mention if mem else f"<@{uid}>"
            mc_info = await db.get_linked_account(uid)
            ign_str = mc_info["mc_username"] if mc_info else "Unlinked"
            member_data_list.append({"mention": mention_str, "ign": ign_str})

        new_embed = embeds.build_queue_embed(gamemode_key, is_open, member_data_list)
        await msg.edit(embed=new_embed, view=QueueView(gamemode_key, db))
    except Exception:
        pass


# --- Account Linking Modal & View ---

class LinkModal(ui.Modal, title="Link Minecraft Account"):
    ign_input = ui.TextInput(
        label="Minecraft Username or UUID",
        placeholder="e.g. Notch or 069a79f4-44e9-4726-a5be-fca90e38aaf5",
        min_length=3,
        max_length=36,
        required=True
    )

    def __init__(self, db: Database):
        super().__init__()
        self.db = db

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        raw_val = self.ign_input.value.strip()

        player_data = await resolve_minecraft_player(raw_val)
        if not player_data:
            await interaction.followup.send(
                "❌ **Could not verify that Minecraft account!** Please check the spelling or provide a valid UUID.",
                ephemeral=True
            )
            return

        username = player_data["username"]
        uuid_str = player_data["uuid"]

        await self.db.link_account(interaction.user.id, username, uuid_str)

        confirm_embed = discord.Embed(
            title="✅ MINECRAFT ACCOUNT LINKED",
            description=(
                f"Successfully linked **{interaction.user.mention}** to Minecraft account **`{username}`**!\n\n"
                f"**UUID:** `{uuid_str}`\n"
                f"You are now eligible to join all testing queues."
            ),
            color=COLOR_SUCCESS
        )
        confirm_embed.set_thumbnail(url=player_data["avatar_url"])
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)


class LinkView(ui.View):
    def __init__(self, db: Database):
        super().__init__(timeout=None)
        self.db = db

    @ui.button(
        label="Link Minecraft Account",
        emoji="🔗",
        style=discord.ButtonStyle.success,
        custom_id="ascension:btn_link_account"
    )
    async def btn_link(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(LinkModal(self.db))


# --- Queue Buttons View ---

class QueueView(ui.View):
    def __init__(self, gamemode_key: str, db: Database):
        super().__init__(timeout=None)
        self.gamemode_key = gamemode_key
        self.db = db

    @ui.button(
        label="Join Queue",
        emoji="🟢",
        style=discord.ButtonStyle.success,
        custom_id="ascension:btn_join_queue"
    )
    async def btn_join(self, interaction: discord.Interaction, button: ui.Button):
        # 1. Determine gamemode from channel
        gamemode = CHANNEL_TO_GAMEMODE.get(interaction.channel_id, self.gamemode_key)
        if not gamemode:
            await interaction.response.send_message("❌ This channel is not a registered queue channel.", ephemeral=True)
            return

        # 2. Check if queue is open
        q_state = await self.db.get_queue_state(gamemode)
        if q_state and not q_state.get("is_open", 1):
            await interaction.response.send_message(
                "🔴 **This queue is currently closed by testers!** Please wait until a tester re-opens it.",
                ephemeral=True
            )
            return

        # 3. Check if account is linked
        linked = await self.db.get_linked_account(interaction.user.id)
        if not linked:
            await interaction.response.send_message(
                f"❌ **You must link your Minecraft account before joining the queue!**\n"
                f"Head over to <#{LINK_CHANNEL_ID}> or use `/link` to connect your account.",
                ephemeral=True
            )
            return

        # 4. Check Cooldown (1 day / 86400s)
        cooldown_left = await self.db.get_cooldown_remaining(interaction.user.id, gamemode)
        if cooldown_left > 0 and interaction.user.id not in AUTHORIZED_OWNERS:
            hours = cooldown_left // 3600
            mins = (cooldown_left % 3600) // 60
            await interaction.response.send_message(
                f"⏳ **You are on cooldown for this gamemode!**\n"
                f"You can re-test in **{hours}h {mins}m** (<t:{int(time.time() + cooldown_left)}:R>).",
                ephemeral=True
            )
            return

        # 5. Check if already in this queue
        if await self.db.is_in_queue(interaction.user.id, gamemode):
            await interaction.response.send_message("⚠️ You are already in this waiting list!", ephemeral=True)
            return

        # 6. Check if already in an active test
        if await self.db.is_player_in_test(interaction.user.id):
            await interaction.response.send_message("⚔️ You already have an active test session in progress!", ephemeral=True)
            return

        # Add to queue
        await self.db.add_to_queue(gamemode, interaction.user.id)
        members = await self.db.get_queue_members(gamemode)
        position = members.index(interaction.user.id) + 1

        await interaction.response.send_message(
            f"✅ **You joined the {GAMEMODES[gamemode]['name']} queue!**\n"
            f"Your position: **#{position}** in line. You will be pinged when a tester pulls you.",
            ephemeral=True
        )

        # Refresh embed
        if q_state and q_state.get("message_id"):
            await update_queue_embed_message(
                interaction.channel, q_state["message_id"], gamemode, self.db, interaction.guild
            )

    @ui.button(
        label="Leave Queue",
        emoji="🔴",
        style=discord.ButtonStyle.secondary,
        custom_id="ascension:btn_leave_queue"
    )
    async def btn_leave(self, interaction: discord.Interaction, button: ui.Button):
        gamemode = CHANNEL_TO_GAMEMODE.get(interaction.channel_id, self.gamemode_key)
        if not gamemode:
            await interaction.response.send_message("❌ This channel is not a registered queue channel.", ephemeral=True)
            return

        removed = await self.db.remove_from_queue(gamemode, interaction.user.id)
        if not removed:
            await interaction.response.send_message("⚠️ You are not currently in this queue.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"🚪 You have left the **{GAMEMODES[gamemode]['name']}** queue.",
            ephemeral=True
        )

        q_state = await self.db.get_queue_state(gamemode)
        if q_state and q_state.get("message_id"):
            await update_queue_embed_message(
                interaction.channel, q_state["message_id"], gamemode, self.db, interaction.guild
            )

    @ui.button(
        label="My Position",
        emoji="📋",
        style=discord.ButtonStyle.primary,
        custom_id="ascension:btn_view_queue"
    )
    async def btn_position(self, interaction: discord.Interaction, button: ui.Button):
        gamemode = CHANNEL_TO_GAMEMODE.get(interaction.channel_id, self.gamemode_key)
        if not gamemode:
            await interaction.response.send_message("❌ This channel is not a registered queue channel.", ephemeral=True)
            return

        members = await self.db.get_queue_members(gamemode)
        if interaction.user.id not in members:
            await interaction.response.send_message(
                f"ℹ️ You are not in the **{GAMEMODES[gamemode]['name']}** queue.\n"
                f"Total players currently waiting: **{len(members)}**",
                ephemeral=True
            )
            return

        pos = members.index(interaction.user.id) + 1
        await interaction.response.send_message(
            f"📍 **Queue Status for {GAMEMODES[gamemode]['name']}:**\n"
            f"• Your Position: **#{pos}** of **{len(members)}** players waiting.",
            ephemeral=True
        )

    @ui.button(
        label="Pull Next Player",
        emoji="⚔️",
        style=discord.ButtonStyle.danger,
        custom_id="ascension:btn_pull_queue"
    )
    async def btn_pull(self, interaction: discord.Interaction, button: ui.Button):
        gamemode = CHANNEL_TO_GAMEMODE.get(interaction.channel_id, self.gamemode_key)
        if not gamemode:
            await interaction.response.send_message("❌ This channel is not a registered queue channel.", ephemeral=True)
            return

        # Check tester authorization
        if not is_user_tester(interaction.user, gamemode):
            await interaction.response.send_message(
                "❌ **You do not have permission to pull players from this queue!** (Tester role required)",
                ephemeral=True
            )
            return

        # Pop next player
        next_player_id = await self.db.pop_next_in_queue(gamemode)
        if not next_player_id:
            await interaction.response.send_message("⚠️ The queue is currently empty! Nobody to pull.", ephemeral=True)
            return

        player_member = interaction.guild.get_member(next_player_id)
        if not player_member:
            await interaction.response.send_message(
                f"⚠️ The next player in queue (`{next_player_id}`) is no longer in this server.",
                ephemeral=True
            )
            return

        # Fetch player's linked MC account
        mc_data = await self.db.get_linked_account(player_member.id)
        mc_name = mc_data["mc_username"] if mc_data else player_member.name

        # Create private testing thread directly under the queue channel
        try:
            thread = await interaction.channel.create_thread(
                name=f"testing-{mc_name}",
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread,
                invitable=False
            )
        except Exception:
            # Fallback if private threads need public fallback or permissions
            thread = await interaction.channel.create_thread(
                name=f"testing-{mc_name}",
                auto_archive_duration=1440
            )

        # Add both tester and player to the private thread
        await thread.add_user(interaction.user)
        await thread.add_user(player_member)

        # Record active test in DB
        await self.db.create_active_test(thread.id, gamemode, interaction.user.id, player_member.id)

        # Post session card inside the thread
        session_embed = embeds.build_session_embed(gamemode, player_member, interaction.user, mc_data)
        session_view = TestingSessionView(thread.id, gamemode, interaction.user.id, player_member.id, self.db)
        await thread.send(
            content=f"⚔️ {player_member.mention} has been pulled by tester {interaction.user.mention}!",
            embed=session_embed,
            view=session_view
        )

        await interaction.response.send_message(
            f"✅ **Pulled {player_member.mention}!** Created testing thread: {thread.mention}",
            ephemeral=True
        )

        # Update persistent queue embed
        q_state = await self.db.get_queue_state(gamemode)
        if q_state and q_state.get("message_id"):
            await update_queue_embed_message(
                interaction.channel, q_state["message_id"], gamemode, self.db, interaction.guild
            )


# --- Testing Session Modal & Controls ---

class ResultSubmitModal(ui.Modal, title="Submit Tier Test Result"):
    tier_input = ui.TextInput(
        label="Awarded Tier (e.g. LT5, HT5, LT4, HT4)",
        placeholder="Enter tier: LT5, HT5, LT4, or HT4",
        min_length=3,
        max_length=5,
        required=True
    )
    notes_input = ui.TextInput(
        label="Tester Notes / Score (Optional)",
        placeholder="e.g. 3-1 win, good movement and mechanics",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False
    )

    def __init__(self, thread_id: int, gamemode: str, tester_id: int, player_id: int, db: Database):
        super().__init__()
        self.thread_id = thread_id
        self.gamemode = gamemode
        self.tester_id = tester_id
        self.player_id = player_id
        self.db = db

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        awarded_tier = self.tier_input.value.strip().upper()
        notes = self.notes_input.value.strip()

        # Validate tier: testers can award LT5, HT5, LT4, HT4
        # High-tier testers / owners can also award higher tiers if needed
        is_high_tier_tester = (
            interaction.user.id in AUTHORIZED_OWNERS or
            any(r.id in HIGH_TIER_TESTER_ROLES for r in interaction.user.roles)
        )

        valid_list = ALL_TIERS if is_high_tier_tester else TESTER_ALLOWED_TIERS
        if awarded_tier not in valid_list:
            await interaction.followup.send(
                f"❌ **Invalid tier!** You can only award: `{'`, `'.join(valid_list)}`.",
                ephemeral=True
            )
            return

        player_member = interaction.guild.get_member(self.player_id)
        if not player_member:
            await interaction.followup.send("❌ Player is no longer in this server.", ephemeral=True)
            return

        # 1. Record in DB
        await self.db.record_tier_result(
            self.player_id, self.gamemode, awarded_tier, interaction.user.id, notes
        )
        await self.db.delete_active_test(self.thread_id)

        # 2. Assign Role & Clean old tiers for this gamemode
        role_assigned_msg = ""
        cfg = GAMEMODES.get(self.gamemode, {})
        roles_map = cfg.get("roles", {})
        target_role_id = roles_map.get(awarded_tier)

        if target_role_id:
            target_role = interaction.guild.get_role(target_role_id)
            if target_role:
                try:
                    # Remove any existing tier roles for this specific gamemode
                    roles_to_remove = [
                        interaction.guild.get_role(rid)
                        for rid in roles_map.values()
                        if rid in [r.id for r in player_member.roles] and rid != target_role_id
                    ]
                    for r in roles_to_remove:
                        if r:
                            await player_member.remove_roles(r, reason="Tier update")

                    # Add new role
                    await player_member.add_roles(target_role, reason=f"Ascension Tier Result: {awarded_tier}")
                    role_assigned_msg = f"Assigned role: {target_role.mention}"
                except Exception as e:
                    role_assigned_msg = f"*(Note: Bot could not manage role: {e})*"
        else:
            # Fallback message as specified by user
            role_assigned_msg = (
                f"{awarded_tier.lower()} {self.gamemode} rank is put in broski dm TTVRecod with the role id for the category"
            )

        # 3. Post to #tier-results
        results_channel = interaction.guild.get_channel(RESULTS_CHANNEL_ID)
        mc_data = await self.db.get_linked_account(self.player_id)
        if results_channel:
            announcement = embeds.build_result_announcement_embed(
                player_member, mc_data, self.gamemode, awarded_tier, interaction.user, notes
            )
            await results_channel.send(embed=announcement)

        # 4. Confirmation in testing thread
        success_embed = discord.Embed(
            title="🎉 TEST COMPLETED & SAVED",
            description=(
                f"**Player:** {player_member.mention}\n"
                f"**Gamemode:** {cfg.get('name', self.gamemode.title())}\n"
                f"**Awarded Tier:** `{awarded_tier}`\n"
                f"**Status:** {role_assigned_msg}\n\n"
                f"*This testing thread will be closed in 10 seconds.*"
            ),
            color=COLOR_SUCCESS
        )
        await interaction.followup.send(embed=success_embed)

        # Close/archive thread after 10s
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.datetime.timedelta(seconds=10))
        try:
            thread = interaction.guild.get_thread(self.thread_id)
            if thread:
                await thread.edit(archived=True, locked=True)
        except Exception:
            pass


class PersistentTestingSessionView(ui.View):
    def __init__(self, db: Database):
        super().__init__(timeout=None)
        self.db = db

    @ui.button(
        label="Submit Result",
        emoji="🏆",
        style=discord.ButtonStyle.success,
        custom_id="ascension:btn_session_submit"
    )
    async def btn_submit(self, interaction: discord.Interaction, button: ui.Button):
        # Look up active test for this thread in DB
        active_test = await self.db.get_active_test(interaction.channel_id)
        if not active_test:
            await interaction.response.send_message(
                "⚠️ No active test session recorded for this thread, or it was already completed.",
                ephemeral=True
            )
            return

        tester_id = active_test["tester_id"]
        gamemode = active_test["gamemode"]
        player_id = active_test["player_id"]

        if interaction.user.id != tester_id and not is_user_tester(interaction.user, gamemode):
            await interaction.response.send_message(
                "❌ Only the assigned tester or authorized staff can submit the test result!",
                ephemeral=True
            )
            return

        modal = ResultSubmitModal(
            interaction.channel_id, gamemode, tester_id, player_id, self.db
        )
        await interaction.response.send_modal(modal)

    @ui.button(
        label="Cancel Test",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ascension:btn_session_cancel"
    )
    async def btn_cancel(self, interaction: discord.Interaction, button: ui.Button):
        active_test = await self.db.get_active_test(interaction.channel_id)
        if not active_test:
            await interaction.response.send_message(
                "⚠️ No active test session recorded for this thread.",
                ephemeral=True
            )
            return

        tester_id = active_test["tester_id"]
        gamemode = active_test["gamemode"]

        if interaction.user.id != tester_id and not is_user_tester(interaction.user, gamemode):
            await interaction.response.send_message(
                "❌ Only the assigned tester or authorized staff can cancel this session!",
                ephemeral=True
            )
            return

        await self.db.delete_active_test(interaction.channel_id)

        cancel_embed = discord.Embed(
            title="🛑 TEST SESSION CANCELLED",
            description=(
                f"This testing session was cancelled by {interaction.user.mention}.\n"
                f"The player is freed to join queues again.\n\n"
                f"*This thread will be closed in 5 seconds.*"
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
