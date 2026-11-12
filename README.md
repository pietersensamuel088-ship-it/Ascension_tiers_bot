# ⚔️ Ascension Tiers — Minecraft PvP Tier Discord Bot 🇿🇦

> **Ascension Tiers** is a high-performance, aesthetic Discord bot built specifically for **Minecraft PvP Tier Testing** in the **South African (ZA)** region. 
> 
> Engineered using Python 3.12+ and `discord.py` with asynchronous SQLite (`aiosqlite`) persistence, interactive buttons, dynamic waiting lists, auto-created private testing threads, and Mojang account verification.

---

## ✨ Features

- **11 PvP Gamemode Queues:**
  - `⚔️ Sword` • `🪓 Axe` • `🧪 UHC` • `💎 Diapot` • `🌳 SMP` • `🔥 Netherite Pot` • `💨 Speed` • `🛒 Cart` • `🔨 Mace` • `🗡️ Spear` • `🧊 Hole Fight`
- **Dynamic Waiting Lists:**
  - Real-time persistent Discord embeds with `Join Queue`, `Leave Queue`, `My Position`, and `Pull Next Player` buttons.
  - Automatic updates whenever players join, leave, or get pulled.
- **Auto-Generated Private Testing Threads:**
  - When a tester pulls a player, the bot automatically creates a private thread named `testing-<ign>` directly under that queue channel.
  - Automatically adds the player and the tester to the thread.
  - Provides interactive **Submit Result** and **Cancel Test** buttons.
- **Automatic Role Assignment & Result Announcements:**
  - Testers award official tiers (`LT5`, `HT5`, `LT4`, `HT4`).
  - The bot automatically grants the tier role, cleans up lower tier roles, posts an announcement embed to `#tier-results`, and logs everything to SQLite.
- **Aesthetic Player Profiles (`/profile`):**
  - Displays linked Minecraft IGN, UUID, 3D Minecraft skin head avatar, rankings across all 11 gamemodes, and recent testing history.
- **Account Verification (`/link` & Button Panel):**
  - Players must verify their Minecraft username or UUID before joining queues.
  - Fast PlayerDB + Mojang API resolution with resilient fallbacks.
- **Cooldown System:**
  - 24-hour (1 day) cooldown between tests per gamemode to prevent spam.
- **High Tier Tester & Staff Hierarchy:**
  - Certified testers can only test within their permitted gamemodes.
  - High-tier testers (`HT3 Tester`, `HT2 Tester`, `HT1 Tester`, `Recruiter`) and Server Admins/Owners hold global testing privileges.
- **No Cogs Architecture:**
  - Clean, modular single-tree service architecture designed for stability and simplicity.
- **Proxmox & Docker Ready:**
  - Comes with `Dockerfile`, `docker-compose.yml`, and `systemd` service files for easy hosting on a Proxmox LXC container or VM.

---

## 📜 Slash Commands (No Underscores)

| Command | Description | Permission |
| :--- | :--- | :--- |
| `/help` | Detailed guide explaining how the tier testing system works | Everyone |
| `/profile [player]` | View an aesthetic player card with Minecraft skin, tiers, and test history | Everyone |
| `/link [ign]` | Link Minecraft username or UUID to Discord profile | Everyone |
| `/unlink [player]` | Unlink Minecraft account | Everyone (Self) / Admin |
| `/queues` | View live overview and waiting counts for all 11 queues | Everyone |
| `/history [player]` | View complete chronological tier test history | Everyone |
| `/open [gamemode]` | Open a queue to allow players to join | Certified Testers / Admins |
| `/close [gamemode]` | Close a queue to pause joins | Certified Testers / Admins |
| `/pull [gamemode]` | Pull the next waiting player and create a private testing thread | Certified Testers / Admins |
| `/result [tier] [notes]` | Submit official tier result inside a testing thread | Certified Testers / Admins |
| `/cancel [reason]` | Cancel an active testing session and close the thread | Certified Testers / Admins |
| `/clearqueue [gamemode]` | Clear all waiting players from a queue | Admins / Owners |
| `/setup [target]` | Deploy persistent queue embeds or link panel (`link`, `current`, `all`) | Admins / Owners |
| `/owner` | Special command for `TTVRecod` (`TTVRecod That goat fr tho.`) | `1162838607220965377` |

---

## 🛠️ Project Structure

```text
Ascension_tiers_bot/
├── .env                     # Private environment variables (Token, IDs)
├── .env.example             # Clean environment template
├── .gitignore               # Excludes secrets, databases, and cache
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container build file
├── docker-compose.yml       # Docker Compose service definition
├── ascensionbot.service     # Linux systemd service unit for Proxmox
├── config.py                # Gamemode IDs, Roles, Channels, Colors, Settings
├── database.py              # Async SQLite database methods (aiosqlite)
├── mojang.py                # PlayerDB & Mojang API skin/UUID resolver
├── embeds.py                # Aesthetic dark-mode embed templates
├── views.py                 # Persistent buttons, views, and modal popups
├── bot.py                   # Main bot executable & command registry
├── test_bot.py              # Automated test suite (pytest)
└── README.md                # Documentation & deployment guide
```

---

## 🚀 Deployment Guide (Proxmox Server)

You can host this bot on your **Proxmox VE** instance inside a lightweight **Ubuntu/Debian LXC container** or VM.

### Option A: Running with Docker (Recommended)

1. **Clone the repository onto your Proxmox LXC/VM:**
   ```bash
   git clone https://github.com/<YOUR_USERNAME>/Ascension_tiers_bot.git
   cd Ascension_tiers_bot
   ```

2. **Configure your `.env`:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   Paste your Discord Bot Token and verify the IDs.

3. **Build and start the container:**
   ```bash
   docker compose up -d --build
   ```

4. **Check logs:**
   ```bash
   docker compose logs -f
   ```

---

### Option B: Running with Linux `systemd` (Native LXC)

1. **Install Python 3.12 and venv:**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv git
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/<YOUR_USERNAME>/Ascension_tiers_bot.git /opt/ascension-tiers-bot
   cd /opt/ascension-tiers-bot
   ```

3. **Set up Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure `.env`:**
   ```bash
   cp .env.example .env
   nano .env
   ```

5. **Install systemd service:**
   ```bash
   sudo cp ascensionbot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable ascensionbot
   sudo systemctl start ascensionbot
   ```

6. **Check status:**
   ```bash
   sudo systemctl status ascensionbot
   ```

---

## ⚡ First-Time Server Setup

Once the bot is online in your Discord server:
1. Run `/setup target:link` inside the `#✅・link-account` channel (`1570492943951995010`). This creates the persistent **Link Minecraft Account** button.
2. Run `/setup target:all` in any staff channel. The bot will automatically post persistent interactive queue embeds across all 11 testing channels!
3. Testers can now open queues with `/open` or click **Pull Next Player** when players join!

---

## 🛡️ License

Developed for **Ascension Tiers**. All rights reserved.
