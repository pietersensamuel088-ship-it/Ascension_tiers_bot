"""
Ascension Tiers - Central Configuration
Loads environment variables and maps all gamemodes, channels, tester roles, and tier badges.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# --- Discord Authentication & Core IDs ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = 1570034909441957970

# Bot Owners & Admin Overrides
OWNER_ID = int(os.getenv("OWNER_ID", "1162838607220965377"))
FRIEND_ID = int(os.getenv("FRIEND_ID", "801529542258589777"))
AUTHORIZED_OWNERS: List[int] = [OWNER_ID, FRIEND_ID]

OWNER_ROLE_ID = int(os.getenv("OWNER_ROLE_ID", "1570034909441957971"))

# Channels
RESULTS_CHANNEL_ID = int(os.getenv("RESULTS_CHANNEL_ID", "1570034912625692798"))
LINK_CHANNEL_ID = int(os.getenv("LINK_CHANNEL_ID", "1570492943951995010"))

# Database path
DATABASE_PATH = os.getenv("DATABASE_PATH", "ascension_tiers.db")

# Cooldown duration in seconds (1 day = 86400 seconds)
COOLDOWN_SECONDS = 86400

# Universal / High Tier Tester Roles (can manage/test across queues)
HIGH_TIER_TESTER_ROLES = [
    1570055371140104284,  # HT3 Tester
    1570055422402891866,  # HT2 Tester
    1570055508457553950,  # HT1 Tester
    1570054179303591956,  # Recruiter
]

# Standard tiers testers are allowed to award directly
TESTER_ALLOWED_TIERS = ["LT5", "HT5", "LT4", "HT4"]

# Full tier hierarchy for reference & high tier testers
ALL_TIERS = ["LT5", "HT5", "LT4", "HT4", "LT3", "HT3", "LT2", "HT2", "LT1", "HT1"]

# --- Gamemodes Configuration ---
# Maps gamemode identifiers to their queue channels, tester roles, emojis, and tier role IDs
GAMEMODES: Dict[str, Dict[str, Any]] = {
    "sword": {
        "name": "Sword",
        "emoji": "⚔️",
        "channel_id": 1570034918208180284,
        "tester_role_id": 1570054289315995658,
        "roles": {
            "LT5": 1570034909563723879,
            "HT5": 1570034909563723878,
            "LT4": 1570034909563723877,
            "HT4": 1570034909563723876,
            "LT3": 1570034909521907742,
            "HT3": 1570034909521907741,
            "LT2": 1570034909521907740,
            "HT2": 1570034909521907739,
            "LT1": 1570034909521907738,
            "HT1": 1570034909521907737,
        }
    },
    "axe": {
        "name": "Axe",
        "emoji": "🪓",
        "channel_id": 1570034918208180285,
        "tester_role_id": 1570054258542383265,
        "roles": {
            "LT5": 1570034909806985250,
            "HT5": 1570034909806985249,
            "LT4": 1570034909806985248,
            "HT4": 1570034909806985247,
            "LT3": 1570034909777502217,
            "HT3": 1570034909777502216,
            "LT2": 1570034909777502215,
            "HT2": 1570034909777502214,
            "LT1": 1570034909777502213,
            "HT1": 1570034909777502212,
        }
    },
    "uhc": {
        "name": "UHC",
        "emoji": "🧪",
        "channel_id": 1570034918208180286,
        "tester_role_id": 1570054376351989800,
        "roles": {
            "LT5": 1570034909521907736,
            "HT5": 1570034909521907735,
            "LT4": 1570034909521907734,
            "HT4": 1570034909441957979,
            "LT3": 1570034909441957978,
            "HT3": 1570034909441957977,
            "LT2": 1570034909441957976,
            "HT2": 1570034909441957975,
            "LT1": 1570034909441957974,
            "HT1": 1570034909441957973,
        }
    },
    "diapot": {
        "name": "Diapot",
        "emoji": "💎",
        "channel_id": 1570034918208180287,
        "tester_role_id": 1570054392453791754,
        "roles": {
            "LT5": 1570034909723230261,
            "HT5": 1570034909723230260,
            "LT4": 1570034909723230259,
            "HT4": 1570034909723230258,
            "LT3": 1570034909693612131,
            "HT3": 1570034909693612130,
            "LT2": 1570034909693612129,
            "HT2": 1570034909693612128,
            "LT1": 1570034909693612127,
            "HT1": 1570034909693612126,
        }
    },
    "smp": {
        "name": "SMP",
        "emoji": "🌳",
        "channel_id": 1570034918208180288,
        "tester_role_id": 1570054997432074290,
        "roles": {
            "LT5": 1570034909634887826,
            "HT5": 1570034909634887825,
            "LT4": 1570034909634887824,
            "HT4": 1570034909634887823,
            "LT3": 1570034909605797978,
            "HT3": 1570034909605797977,
            "LT2": 1570034909605797976,
            "HT2": 1570034909605797975,
            "LT1": 1570034909605797974,
            "HT1": 1570034909605797973,
        }
    },
    "nethpot": {
        "name": "Netherite Pot",
        "emoji": "🔥",
        "channel_id": 1570034918770352148,
        "tester_role_id": 1570054948597801041,
        "roles": {
            "LT5": 1570034909664514131,
            "HT5": 1570034909664514130,
            "LT4": 1570034909664514129,
            "HT4": 1570034909664514128,
            "LT3": 1570034909634887832,
            "HT3": 1570034909634887831,
            "LT2": 1570034909634887830,
            "HT2": 1570034909634887829,
            "LT1": 1570034909634887828,
            "HT1": 1570034909634887827,
        }
    },
    "speed": {
        "name": "Speed",
        "emoji": "💨",
        "channel_id": 1570034918770352149,
        "tester_role_id": 1570055142697340989,
        "roles": {
            "LT5": 1570034909589012523,
            "HT5": 1570034909589012522,
            "LT4": 1570034909589012521,
            "HT4": 1570034909589012520,
            "LT3": 1570034909563723885,
            "HT3": 1570034909563723884,
            "LT2": 1570034909563723883,
            "HT2": 1570034909563723882,
            "LT1": 1570034909563723881,
            "HT1": 1570034909563723880,
        }
    },
    "cart": {
        "name": "Cart",
        "emoji": "🛒",
        "channel_id": 1570034918770352150,
        "tester_role_id": 1570055227313487873,
        "roles": {
            "LT5": 1570034909777502211,
            "HT5": 1570034909777502210,
            "LT4": 1570034909777502209,
            "HT4": 1570034909777502208,
            "LT3": 1570034909723230267,
            "HT3": 1570034909723230266,
            "LT2": 1570034909723230265,
            "HT2": 1570034909723230264,
            "LT1": 1570034909723230263,
            "HT1": 1570034909723230262,
        }
    },
    "mace": {
        "name": "Mace",
        "emoji": "🔨",
        "channel_id": 1570034918770352151,
        "tester_role_id": 1570054341920952353,
        "roles": {
            "LT5": 1570034909693612125,
            "HT5": 1570034909693612124,
            "LT4": 1570034909693612123,
            "HT4": 1570034909693612122,
            "LT3": 1570034909664514137,
            "HT3": 1570034909664514136,
            "LT2": 1570034909664514135,
            "HT2": 1570034909664514134,
            "LT1": 1570034909664514133,
            "HT1": 1570034909664514132,
        }
    },
    "spear": {
        "name": "Spear",
        "emoji": "🗡️",
        "channel_id": 1570034918770352152,
        "tester_role_id": 1570055316903825559,
        "roles": {
            "LT5": 1570034909605797972,
            "HT5": 1570034909605797971,
            "LT4": 1570034909605797970,
            "HT4": 1570034909605797969,
            "LT3": 1570034909589012529,
            "HT3": 1570034909589012528,
            "LT2": 1570034909589012527,
            "HT2": 1570034909589012526,
            "LT1": 1570034909589012525,
            "HT1": 1570034909589012524,
        }
    },
    "hole": {
        "name": "Hole Fight",
        "emoji": "🧊",
        "channel_id": 1570466712502149261,
        "tester_role_id": 1570489440105922744,
        "roles": {
            "LT5": 1570465802627448862,
            "HT5": 1570465885070557245,
            "LT4": 1570465931036074065,
            "HT4": 1570466006013321307,
            "LT3": 1570466035935617155,
            "HT3": 1570466126918590494,
            "LT2": 1570466269617070213,
            "HT2": 1570466341453041844,
            "LT1": 1570466404518338631,
            "HT1": 1570466452941570048,
        }
    }
}

# Lookup gamemode by channel ID
CHANNEL_TO_GAMEMODE: Dict[int, str] = {
    cfg["channel_id"]: key for key, cfg in GAMEMODES.items()
}

# Lookup gamemode by tester role ID
TESTER_ROLE_TO_GAMEMODE: Dict[int, str] = {
    cfg["tester_role_id"]: key for key, cfg in GAMEMODES.items()
}

# Colors for Discord Embeds
COLOR_PRIMARY = 0x5865F2    # Blurple
COLOR_SUCCESS = 0x57F287    # Green
COLOR_DANGER = 0xED4245     # Red
COLOR_GOLD = 0xFEE75C       # Gold / High Tier
COLOR_DARK = 0x2B2D31       # Discord Dark Theme
COLOR_CYBER = 0x00F0FF      # Cyberpunk Cyan
