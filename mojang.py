"""
Ascension Tiers - Minecraft / Mojang API Resolver
Fetches Minecraft username, UUID, and avatar renders.
"""

import aiohttp
import uuid
import re
from typing import Optional, Dict

UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$")

async def resolve_minecraft_player(player_input: str) -> Optional[Dict[str, str]]:
    """
    Resolves a Minecraft username or UUID using PlayerDB / Mojang API.
    Returns a dict with 'username', 'uuid' (without dashes), and 'avatar_url', or None if invalid.
    """
    clean_input = player_input.strip()
    is_uuid = bool(UUID_REGEX.match(clean_input))

    headers = {
        "User-Agent": "AscensionTiersBot/1.0 (Minecraft PvP Tier System)"
    }

    # 1. Try PlayerDB API first (Fast, high rate limits)
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as session:
            url = f"https://playerdb.co/api/player/minecraft/{clean_input}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success") and "data" in data and "player" in data["data"]:
                        player = data["data"]["player"]
                        raw_uuid = player.get("raw_id") or player.get("id", "").replace("-", "")
                        username = player.get("username", clean_input)
                        return {
                            "username": username,
                            "uuid": raw_uuid,
                            "avatar_url": f"https://mc-heads.net/avatar/{raw_uuid}/128.png",
                            "body_url": f"https://mc-heads.net/body/{raw_uuid}/right"
                        }
    except Exception:
        pass

    # 2. Try Mojang API directly as fallback
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as session:
            if is_uuid:
                clean_uuid = clean_input.replace("-", "")
                url = f"https://sessionserver.mojang.com/session/minecraft/profile/{clean_uuid}"
            else:
                url = f"https://api.mojang.com/users/profiles/minecraft/{clean_input}"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    raw_uuid = data.get("id", "").replace("-", "")
                    username = data.get("name", clean_input)
                    return {
                        "username": username,
                        "uuid": raw_uuid,
                        "avatar_url": f"https://mc-heads.net/avatar/{raw_uuid}/128.png",
                        "body_url": f"https://mc-heads.net/body/{raw_uuid}/right"
                    }
    except Exception:
        pass

    # 3. If external APIs fail or are unreachable, allow standard username format validation
    # Standard Minecraft username is 3-16 chars [a-zA-Z0-9_]
    if re.match(r"^[a-zA-Z0-9_]{3,16}$", clean_input):
        offline_uuid = uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{clean_input}").hex
        return {
            "username": clean_input,
            "uuid": offline_uuid,
            "avatar_url": f"https://mc-heads.net/avatar/{clean_input}/128.png",
            "body_url": f"https://mc-heads.net/body/{clean_input}/right"
        }

    return None
