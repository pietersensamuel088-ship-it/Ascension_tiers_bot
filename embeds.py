"""
Ascension Tiers - Aesthetic Discord Embeds
Provides clean, dark-mode cyberpunk/PvP styled embeds for queues, profiles, sessions, and results.
"""

import discord
import time
from typing import Dict, Any, List, Optional
from config import (
    GAMEMODES,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_DANGER,
    COLOR_GOLD,
    COLOR_DARK,
    COLOR_CYBER,
    TESTER_ALLOWED_TIERS
)

def format_timestamp(epoch: int, format_type: str = "R") -> str:
    return f"<t:{epoch}:{format_type}>"

def build_queue_embed(
    gamemode_key: str,
    is_open: bool,
    member_data_list: List[Dict[str, str]],  # [{'mention': '@user', 'ign': 'IGN'}]
) -> discord.Embed:
    """Builds the persistent embed shown in the queue channel."""
    cfg = GAMEMODES.get(gamemode_key, {})
    name = cfg.get("name", gamemode_key.title())
    emoji = cfg.get("emoji", "⚔️")
    tester_role_id = cfg.get("tester_role_id", 0)

    color = COLOR_SUCCESS if is_open else COLOR_DANGER
    status_text = "🟢 **STATUS: OPEN FOR TESTING**" if is_open else "🔴 **STATUS: QUEUE CLOSED**"

    embed = discord.Embed(
        title=f"{emoji} ASCENSION TIERS — {name.upper()} QUEUE",
        description=(
            f"{status_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**Region:** 🇿🇦 South Africa (ZA)\n"
            f"**Assigned Tester Role:** <@&{tester_role_id}>\n"
            f"**Testable Tiers:** `{'` • `'.join(TESTER_ALLOWED_TIERS)}`\n"
            f"**Cooldown:** `24 Hours` after testing\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=color
    )

    # Queue list formatting
    if not member_data_list:
        embed.add_field(
            name="📋 Current Waiting List (0)",
            value="*The queue is currently empty. Click **Join Queue** below to get tested!*",
            inline=False
        )
    else:
        entries = []
        for i, item in enumerate(member_data_list, start=1):
            ign = item.get("ign", "Unlinked")
            mention = item.get("mention", "")
            entries.append(f"`#{i:02d}` **{ign}** ({mention})")
        
        # Split into chunks if long
        queue_text = "\n".join(entries[:15])
        if len(entries) > 15:
            queue_text += f"\n*...and {len(entries) - 15} more in line*"

        embed.add_field(
            name=f"📋 Current Waiting List ({len(member_data_list)})",
            value=queue_text,
            inline=False
        )

    embed.set_footer(
        text="Ascension Tiers • ZA Region • Click buttons below to interact",
        icon_url="https://i.imgur.com/8QnUqQ9.png"
    )
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_link_embed() -> discord.Embed:
    """Builds the verification and account linking embed."""
    embed = discord.Embed(
        title="🔗 ASCENSION TIERS — MINECRAFT VERIFICATION",
        description=(
            "Welcome to **Ascension Tiers**!\n\n"
            "To participate in official PvP tier testing and join any queue, "
            "you **must** link your Minecraft account to your Discord profile.\n\n"
            "### 📌 How to Link:\n"
            "1. Click the **`Link Account`** button below.\n"
            "2. Enter your valid **Minecraft IGN** or **UUID** in the popup.\n"
            "3. Once verified, your tier card will sync with your Minecraft skin!\n\n"
            "*(You can also use `/link <username_or_uuid>` anywhere in the server)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_CYBER
    )
    embed.set_image(url="https://i.imgur.com/rWzS7XU.png")  # Optional banner aesthetic
    embed.set_footer(text="Ascension Tiers • Secure Mojang Verification • ZA Region")
    return embed


def build_profile_embed(
    member: discord.Member,
    mc_data: Optional[Dict[str, Any]],
    tiers: Dict[str, str],
    history: List[Dict[str, Any]]
) -> discord.Embed:
    """Builds the aesthetic player profile card."""
    username = mc_data.get("username", "Not Linked") if mc_data else "Not Linked"
    uuid_str = mc_data.get("uuid", "N/A") if mc_data else "N/A"
    avatar_url = mc_data.get("avatar_url", member.display_avatar.url) if mc_data else member.display_avatar.url

    embed = discord.Embed(
        title=f"⚔️ {username.upper()} — TIER PROFILE",
        description=(
            f"**Player:** {member.mention} (`{member.id}`)\n"
            f"**Minecraft IGN:** `{username}`\n"
            f"**Minecraft UUID:** `{uuid_str}`\n"
            f"**Region:** 🇿🇦 South Africa (ZA)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_GOLD if tiers else COLOR_DARK
    )
    embed.set_thumbnail(url=avatar_url)

    # Format Tier Badges for each of the 11 gamemodes
    gamemode_fields = []
    for g_key, g_info in GAMEMODES.items():
        name = g_info["name"]
        emoji = g_info["emoji"]
        current_tier = tiers.get(g_key)
        
        if current_tier:
            badge = f"`[{current_tier}]`"
        else:
            badge = "*Unranked*"
        gamemode_fields.append(f"{emoji} **{name}:** {badge}")

    # Arrange into 2 clean columns
    half = (len(gamemode_fields) + 1) // 2
    col1 = "\n".join(gamemode_fields[:half])
    col2 = "\n".join(gamemode_fields[half:])

    embed.add_field(name="🏆 Current Tier Rankings", value=col1, inline=True)
    embed.add_field(name="ㅤ", value=col2, inline=True)

    # Recent test history
    if history:
        history_lines = []
        for entry in history[:4]:
            t_name = GAMEMODES.get(entry["gamemode"], {}).get("name", entry["gamemode"].title())
            tier = entry["tier"]
            tester_mention = f"<@{entry['tester_id']}>"
            ts = format_timestamp(entry["tested_at"], "R")
            history_lines.append(f"• **{t_name}:** `{tier}` by {tester_mention} ({ts})")
        embed.add_field(
            name="📜 Recent Testing History",
            value="\n".join(history_lines),
            inline=False
        )
    else:
        embed.add_field(
            name="📜 Recent Testing History",
            value="*No official test history recorded yet.*",
            inline=False
        )

    embed.set_footer(
        text="Ascension Tiers • Official ZA Minecraft Tier Network",
        icon_url="https://i.imgur.com/8QnUqQ9.png"
    )
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_session_embed(
    gamemode_key: str,
    player: discord.Member,
    tester: discord.Member,
    mc_data: Optional[Dict[str, Any]]
) -> discord.Embed:
    """Builds the embed sent inside the private testing thread."""
    cfg = GAMEMODES.get(gamemode_key, {})
    name = cfg.get("name", gamemode_key.title())
    emoji = cfg.get("emoji", "⚔️")
    ign = mc_data.get("username", player.display_name) if mc_data else player.display_name

    embed = discord.Embed(
        title=f"{emoji} ASCENSION TIERS — TESTING SESSION: {name.upper()}",
        description=(
            f"A private tier testing session has started!\n\n"
            f"👤 **Player:** {player.mention} (`{ign}`)\n"
            f"🛡️ **Tester:** {tester.mention}\n"
            f"⚔️ **Gamemode:** {emoji} {name}\n"
            f"🇿🇦 **Region:** South Africa (ZA)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"### 📋 Instructions for Tester:\n"
            f"1. Coordinate duels / server IP with the player in this thread.\n"
            f"2. Conduct the official tier test matches.\n"
            f"3. When finished, click **`Submit Result`** below to award their rank.\n"
            f"4. If the test cannot proceed, click **`Cancel Test`**.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_PRIMARY
    )
    if mc_data and mc_data.get("avatar_url"):
        embed.set_thumbnail(url=mc_data["avatar_url"])

    embed.set_footer(text="Ascension Tiers • Private Testing Thread")
    embed.timestamp = discord.utils.utcnow()
    return embed


def build_result_announcement_embed(
    player: discord.Member,
    mc_data: Optional[Dict[str, Any]],
    gamemode_key: str,
    tier: str,
    tester: discord.Member,
    notes: str = ""
) -> discord.Embed:
    """Builds the public announcement embed posted to #tier-results."""
    cfg = GAMEMODES.get(gamemode_key, {})
    name = cfg.get("name", gamemode_key.title())
    emoji = cfg.get("emoji", "⚔️")
    ign = mc_data.get("username", player.display_name) if mc_data else player.display_name
    avatar_url = mc_data.get("avatar_url", player.display_avatar.url) if mc_data else player.display_avatar.url

    embed = discord.Embed(
        title="🏆 OFFICIAL TIER RESULT ANNOUNCEMENT 🇿🇦",
        description=(
            f"**Player:** {player.mention} (`{ign}`)\n"
            f"**Gamemode:** {emoji} **{name}**\n"
            f"**Awarded Tier:** 🎖️ **`{tier}`**\n"
            f"**Certified Tester:** {tester.mention}\n"
            f"**Tested At:** <t:{int(time.time())}:F>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_GOLD
    )
    if notes:
        embed.add_field(name="📝 Tester Notes / Score", value=f"*{notes}*", inline=False)

    embed.set_thumbnail(url=avatar_url)
    embed.set_footer(
        text="Ascension Tiers • ZA Region • Official Verification",
        icon_url="https://i.imgur.com/8QnUqQ9.png"
    )
    embed.timestamp = discord.utils.utcnow()
    return embed
