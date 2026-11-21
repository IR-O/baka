# 🌸 MIKO — ADVANCED TELEGRAM GAMING & AI PLATFORM

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v20.7-blue)](https://python-telegram-bot.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3%20WAL-brightgreen)](https://www.sqlite.org/wal.html)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/IR-O/baka)

An enterprise-grade, highly scalable, feature-rich **Telegram Gaming Platform & AI Assistant**. Miko combines a centralized game engine, a 5-tier balanced virtual economy, collectible card trading & dueling, turn-based dungeon crawler RPG, clan/guild warfare, virtual pets, customizable houses, achievements, daily missions, OpenRouter-powered AI copilot, and comprehensive administration into a unified, high-performance Telegram bot.

---

## 📑 TABLE OF CONTENTS
1. [Architecture & System Overview](#-architecture--system-overview)
2. [Database Architecture & Data Integrity](#-database-architecture--data-integrity)
3. [Virtual Economy & Currencies](#-virtual-economy--currencies)
4. [Central Gaming Engine](#-central-gaming-engine)
5. [Complete Game Catalog (Original + 20 New Games)](#-complete-game-catalog)
6. [Collectible Trading Cards & Arena](#-collectible-trading-cards--arena)
7. [Dungeon RPG Adventure Engine](#-dungeon-rpg-adventure-engine)
8. [Guilds, Clans & Social Systems](#-guilds-clans--social-systems)
9. [Virtual Pets & Virtual House Simulation](#-virtual-pets--virtual-house-simulation)
10. [Achievements, Quests & Events](#-achievements-quests--events)
11. [AI Gaming Copilot & OpenRouter Integration](#-ai-gaming-copilot--openrouter-integration)
12. [Premium VIP Membership & Payments](#-premium-vip-membership--payments)
13. [Admin Dashboard & Moderation System](#-admin-dashboard--moderation-system)
14. [Full Command Reference](#-full-command-reference)
15. [Installation & Deployment](#-installation--deployment)
16. [Database Backup & Recovery](#-database-backup--recovery)

---

## 🏛️ ARCHITECTURE & SYSTEM OVERVIEW

Miko is built upon an asynchronous, modular architecture designed for high concurrency, zero race conditions, and strict data persistence.

```
                              ┌────────────────────────────────────────┐
                              │      Telegram Bot API (PTB v20.7)      │
                              └───────────────────┬────────────────────┘
                                                  │
                                       ┌──────────┴──────────┐
                                       │    main.py Router   │
                                       │   (360+ Handlers)   │
                                       └──────────┬──────────┘
                                                  │
         ┌──────────────────┬─────────────────────┼─────────────────────┬──────────────────┐
         │                  │                     │                     │                  │
┌────────┴────────┐ ┌───────┴───────┐ ┌───────────┴───────────┐ ┌───────┴───────┐ ┌────────┴────────┐
│ Central Gaming  │ │ Multi-Tier    │ │   RPG & Social Core   │ │ AI Copilot    │ │ Advanced Admin  │
│ Engine (27 Gms) │ │ Economy Engine│ │(Cards/Dungeon/Guilds/ │ │ (OpenRouter   │ │ Dashboard &     │
│ Matchmaking/Anti│ │ Coins/Gems/XP/│ │ Pets/House/Missions/  │ │ Guardrails &  │ │ Role-Based Auth │
│ Cheat/Sessions  │ │ Event/VIP Tok.│ │ Social/Achievements)  │ │ Rate Limiter) │ │ (Warn/Ban/Eco)  │
└────────┬────────┘ └───────┬───────┘ └───────────┬───────────┘ └───────┬───────┘ └────────┬────────┘
         │                  │                     │                     │                  │
         └──────────────────┴─────────────────────┼─────────────────────┴──────────────────┘
                                                  │
                                      ┌───────────┴───────────┐
                                      │ Thread-Safe Storage   │
                                      │ (_STORAGE_LOCK Mutex) │
                                      └───────────┬───────────┘
                                                  │
                                      ┌───────────┴───────────┐
                                      │ SQLite3 (WAL Mode)    │
                                      │ 30+ Normalized Tables │
                                      │ 10s Concurrency Busy  │
                                      └───────────────────────┘
```

### Key Technical Pillars:
- **Centralized Game Registration**: All games implement the standard `BaseGame` interface and register into `CentralGamingEngine` with unified lifecycle tracking, timeouts, anti-cheat validation, and fair rewards.
- **Thread-Safe Wallet Mutation**: Financial transactions execute under mutex locks (`_STORAGE_LOCK`) with atomic debit/credit operations, preventing duplicate spending, negative balances, and race conditions.
- **SQLite3 WAL Mode**: Production database operates with Write-Ahead Logging (`PRAGMA journal_mode=WAL`), `synchronous=NORMAL`, and a 10,000ms busy timeout to support concurrent reads and writes seamlessly on VPS hosting.
- **Security-First AI Copilot**: All user inputs passed to the OpenRouter LLM are filtered through hardened security guardrails blocking prompt injection, unauthorized balance grants, and privilege escalation.

---

## 🗄️ DATABASE ARCHITECTURE & DATA INTEGRITY

The platform uses a production-hardened SQLite schema (`radha_data.db`) featuring **30+ normalized tables**:

| Table | Purpose |
|---|---|
| `users` | Primary user identity, Telegram ID, username, balance, XP, level, ban status |
| `wallets` | Multi-currency balances (`coins`, `gems`, `event_tokens`, `premium_tokens`) |
| `transactions` | Immutable double-entry financial audit logs with unique IDs |
| `game_sessions` | Active and historical multiplayer/singleplayer game instances |
| `game_statistics` | Per-user, per-game records (`played`, `won`, `lost`, `earnings`, `last_played`) |
| `cards` & `card_inventory` | Unique collectible cards, power, defense, rarity, level, copies |
| `dungeons` & `dungeon_sessions` | Dungeon levels, rooms, active encounters, boss battles |
| `guilds` & `guild_members` | Guild ownership, treasury, level, announcements, member roles |
| `friendships` & `friend_requests` | Bidirectional social graph, pending requests, friend interactions |
| `pets` & `pet_inventory` | Adopted virtual pets, species, rarity, hunger, happiness, evolution stage |
| `houses` & `furniture` | Virtual house tier, rooms, owned furniture catalog, placement |
| `achievements` & `user_achievements` | 10 categories of milestone achievements, secrets, unlocked rewards |
| `daily_missions` & `user_missions` | Daily/weekly quest progression, seasonal event claims |
| `premium_subscriptions` | VIP tier status, expiration timestamps, perk claim tracking |
| `admin_audit_logs` & `user_warnings` | Administrative actions, warning counts, ban records, eco adjustments |

---

## 💰 VIRTUAL ECONOMY & CURRENCIES

The economy is architected around 5 distinct virtual currencies:

1. **Coins (🪙)**: Primary gaming currency used for bets, marketplace trading, house furniture, and common card packs.
2. **Gems (💎)**: Rare progression currency earned via level-ups, rare achievements, high-tier dungeon bosses, and VIP perks. Used for epic card packs and rare pet adoptions.
3. **XP (⭐)**: Progression points determining player level, prestige title, and unlocking advanced games and dungeons.
4. **Event Tokens (🎫)**: Exclusive currency awarded during seasonal events; redeemable in the seasonal event shop.
5. **Premium Tokens (👑)**: VIP membership tokens for cosmetic profiles and special perks.

### Economy Protections & Features:
- **Daily / Weekly / Monthly Streaks**: Guaranteed progression rewards with scaling streak multipliers (`/daily`, `/weekly`, `/monthly`).
- **Referral Program**: Every player has a unique referral code (`REF<user_id>`). Both referrer and referee earn 2,500 Coins and 15 Gems upon registration (`/referral`).
- **Peer-to-Peer Trading & Gifting**: Secure `/pay` and `/gift` commands with sender verification, fee-free user transactions, and complete audit trail.
- **Global Marketplace**: Players can list items, cards, and furniture on the marketplace with `/market` and `/buyitem`.
- **System Metrics & Balancing**: Real-time Gini coefficient calculation, inflation tracking, and total currency circulation monitoring via `EconomyEngine.get_economy_overview()`.

---

## 🎮 CENTRAL GAMING ENGINE

All games in Miko run through `modules.core.game_engine.CentralGamingEngine`:
- **Session Management**: Tracks active session states, player turn order, move timeouts (auto-forfeit on inactivity).
- **Matchmaking Queue**: Central multiplayer matchmaking for 1v1 and party games.
- **Anti-Cheat Validation**: Validates user inputs against allowed game states and bounds on the server side.
- **Unified Rewards**: Automatically credits Coins, Gems, and XP upon match completion, updates `game_statistics`, triggers achievement checks, and emits progression notifications.

---

## 🎲 COMPLETE GAME CATALOG

### Original Preserved Games:
1. **Poker**: Multi-player Texas Hold'em card game with chips and betting rounds.
2. **Roulette**: Casino European roulette wheel (`red`, `black`, `odd`, `even`, direct numbers).
3. **Bluff**: Deception card game where players attempt to shed cards while calling out bluffs.
4. **Bomb Game**: Defuse the hidden bomb or risk losing your coins.
5. **Hack Game**: Cyber terminal hacking simulation with security levels.
6. **Card Game**: High-card draw challenge.
7. **Word Quiz / Word Grid / Word Seek**: Vocabulary and anagram challenges.
8. **Truth & Dare**: Social group engagement with randomized truth and dare prompts.
9. **Secret Game & Puzzles**: Riddles and math brain teasers.

### 20 Requested New Games (Fully Implemented & Production-Ready):

| # | Game | Command | Description | Mechanics |
|---|---|---|---|---|
| 1 | **Tic Tac Toe** | `/tictactoe [bet]` | Classic 3x3 grid battle | Smart AI opponent, win/draw detection, reward payouts |
| 2 | **Rock Paper Scissors** | `/rps <rock/paper/scissors> [bet]` | Instant showdown | Fair pseudo-randomized opponent, win streaks |
| 3 | **Connect Four** | `/connect4 [col] [bet]` | 6x7 vertical dropping token grid | Connect 4 horizontal, vertical, or diagonal tokens to win |
| 4 | **Hangman** | `/hangman [guess] [bet]` | Word mystery guessing | 6 allowed misses, visual ASCII hangman stages, letter reveal |
| 5 | **Wordle** | `/wordle [word] [bet]` | 5-letter hidden word puzzle | 6 attempts, 🟩 green (correct), 🟨 yellow (wrong spot), ⬛ grey |
| 6 | **Memory Match** | `/memory [bet]` | Grid icon memory matching | Card flipping, match recognition, timer challenge |
| 7 | **Sudoku Mini** | `/sudoku [bet]` | 4x4 logic grid | Row, column, and 2x2 box uniqueness validation |
| 8 | **Minesweeper** | `/minesweeper [r,c] [bet]` | Minefield clearance | Hidden bombs, numerical proximity clues, safe clearing |
| 9 | **Blackjack** | `/blackjack [action] [bet]` | 21 card casino game | Hit, Stand, Double Down, Dealer stands on 17 |
| 10 | **Higher or Lower** | `/higherlower [h/l] [bet]` | Card sequence guessing | Predict if next card is higher or lower, streak multipliers |
| 11 | **Number Guess** | `/numberguess [guess] [bet]` | 1-100 binary search | Higher/Lower hint feedback within 7 attempts |
| 12 | **Trivia Battle** | `/trivia [choice] [bet]` | General knowledge quiz | Multiple choice questions across science, history, pop culture |
| 13 | **Emoji Quiz** | `/emojiquiz [answer] [bet]` | Guess the word/movie from emojis | Pattern matching, case-insensitive alias recognition |
| 14 | **Chess Puzzle** | `/chess [move] [bet]` | Tactical chess checkmate problems | Standard SAN notation parsing, mating net execution |
| 15 | **Checkers** | `/checkers [action] [bet]` | Diagonal piece jumping battle | Capture mechanics, kinging, diagonal traversal |
| 16 | **Battleship** | `/battleship [r,c] [bet]` | Naval grid warfare | 5x5 grid, hidden ships, Hit/Miss/Sink tracking |
| 17 | **Quiz Tournament** | `/quiztourney [answer]` | Multi-question gauntlet | 3 consecutive timed questions, cumulative score rewards |
| 18 | **Word Battle** | `/wordbattle [word]` | Vocabulary anagram showdown | Anagram solving from randomized letter pool |
| 19 | **Reaction Challenge** | `/reaction [click]` | Quick reflexes challenge | Timed trigger testing reaction speeds in milliseconds |
| 20 | **Daily Puzzle** | `/dailypuzzle [answer]` | Global daily brain teaser | New puzzle generated daily, global one-time daily bonus |
| + | **Interactive Ludo** | `/ludo [bet]` | Complete interactive board race | Dice roll (1-6), 40-step track, bonus turn on rolling 6 |

---

## 🎴 COLLECTIBLE TRADING CARDS & ARENA

A full trading card game (TCG) subsystem featuring 7 rarity tiers:
- **Common (⚪)** | **Uncommon (🟢)** | **Rare (🔵)** | **Epic (🟣)** | **Legendary (🟡)** | **Mythic (🔴)** | **Limited Edition (✨)**

### Features:
- **Pack Opening (`/openpack <common|rare|epic|legendary>`)**: Realistic probability weightings, drop tables, duplicate card level upgrades.
- **Card Inventory (`/cards`)**: View total collection, power rankings, and duplicate counts.
- **Card Upgrading (`/upgradecard <card_id>`)**: Burn duplicate copies and coins to increase card Power and Defense stats.
- **Card Dueling (`/cardduel <card_id>`)**: Fast-paced elemental card duel arena against AI or players with elemental advantages (`Fire > Earth > Air > Water > Fire`).
- **Gifting & Marketplace (`/giftcard <card_id> <user_id>`)**: Securely trade cards with friends.

---

## ⚔️ DUNGEON RPG ADVENTURE ENGINE

A complete turn-based dungeon crawler with server-validated combat:
- **Dungeon Locations**: *Goblin Caves (Lvl 1)*, *Sunken Crypts (Lvl 5)*, *Dragon Peak (Lvl 10)*.
- **Combat Mechanics**: Real-time HP, Attack, Defense calculation with critical strikes, boss phases, and enemy special attacks.
- **Commands**:
  - `/dungeon`: Start an expedition into available dungeons.
  - `/explore`: Advance into the next chamber (encounter enemies, find treasure, trigger traps).
  - `/attack`: Attack the active dungeon enemy or boss.
  - `/potion`: Drink a health potion to restore HP mid-battle.
  - `/flee`: Escape the dungeon with partial loot.
  - `/dstats`: View RPG stats, equipped weapons, armor, and inventory.
  - `/equip <item_id>`: Equip higher tier swords and armor found as dungeon drops.

---

## 🏰 GUILDS, CLANS & SOCIAL SYSTEMS

- **Guild Creation & Management**: Create a guild with `/createguild <name> <tag>`, deposit funds to `/depositguild <amount>`, and view rankings with `/topguilds`.
- **Guild Perks**: Guild levels unlock passive economy interest, bonus XP from games, and increased daily claim limits.
- **Friend System**:
  - `/addfriend <user_id>`: Send a bidirectional friend invitation.
  - `/acceptfriend <user_id>`: Accept pending friend request.
  - `/friendlist`: View online friends, their levels, and last active status.
  - `/unfriend <user_id>`: Remove friend.
  - `/reportplayer <user_id> <reason>`: File an official moderation report reviewed by admins.

---

## 🐾 VIRTUAL PETS & VIRTUAL HOUSE SIMULATION

### Virtual Pets:
- **Adoption (`/adoptpet <species> <name>`)**: Adopt Dragons, Wolves, Cats, Phoenixes, or Golems.
- **Care Routine (`/feedpet`, `/playpet`, `/trainpet`)**: Manage Hunger, Happiness, and Level. Neglected pets become unhappy and provide no bonuses.
- **Evolution (`/petevolve`)**: Evolve max-level pets into mythical forms with visual badges and game buffs.
- **Pet Battles (`/petbattle`)**: Pit your pet against arena opponents.

### Virtual Houses:
- **House Upgrades (`/house`, `/upgradehouse`)**: Upgrade from a *Cozy Studio* to a *Suburban Home*, *Luxury Villa*, or *Grand Palace*.
- **Interior Decorating (`/furniture`, `/buyfurniture <item>`)**: Purchase beds, sofas, gaming setups, and luxury fireplaces from the catalog.
- **Social Visits (`/visithouse <user_id>`)**: Visit friends' houses and leave guest ratings.

---

## 🏆 ACHIEVEMENTS, QUESTS & EVENTS

- **10 Achievement Categories**: Gaming, Economy, Social, Collection, Dungeon, Guild, Pet, House, Daily Activity, and Secret Milestones.
- **Rewards**: Unlocking achievements grants permanent title badges, large Coin bundles, and rare Gems.
- **Daily & Weekly Quests (`/missions`)**: Auto-resetting objectives (e.g. *Win 3 games*, *Feed your pet*, *Explore 5 dungeon rooms*) with direct claiming (`/claimmission <id>`).
- **Seasonal Campaigns (`/events`)**: Limited-time community events awarding Event Tokens (`/events`).

---

## 🤖 AI GAMING COPILOT & OPENROUTER INTEGRATION

Powered by OpenRouter LLM infrastructure:
- **Context-Aware Assistance**: `/askai <question>` answers game rules, strategies, and bot commands.
- **Game Recommender (`/recommend`)**: Analyzes the player's recent game history, win rate, and level to suggest the optimal game to play next.
- **Game Rule Explainer (`/gamehelp <game>`)**: Detailed, interactive walkthrough of any game's mechanics.
- **Security & Integrity Guardrails**: Hardened prompt filters reject all attempts to trick the AI into giving away coins, changing database entries, or executing administrative actions.

---

## 💎 PREMIUM VIP MEMBERSHIP & PAYMENTS

Three distinct VIP tiers:
1. **Silver VIP**: 1.25x XP multiplier, silver badge `[🥈 SILVER VIP]`, daily 25 Gems perk.
2. **Gold VIP**: 1.50x XP multiplier, gold badge `[🥇 GOLD VIP]`, daily 60 Gems perk, marketplace fee waiver.
3. **Diamond Sovereign**: 2.0x XP multiplier, crown badge `[💎 DIAMOND VIP]`, daily 150 Gems perk, exclusive card pack discounts.

### Supported Payment Gateways:
- **Razorpay**: Server-side webhook verified payments for real-world currency conversions (`/buygems`, `/buyvip`).
- **Telegram Stars**: Native Telegram in-app currency purchasing flow.

---

## 🛡️ ADMIN DASHBOARD & MODERATION SYSTEM

Strict role-based access control based on verified numeric Telegram user IDs (`OWNER_ID` and dynamic sudoers):
- `/dashboard`: Comprehensive live operational overview (DAU, MAU, total currency in circulation, active sessions, system health).
- `/maintenance <on/off>`: Gracefully lock non-admin commands during server maintenance.
- `/admin_warn <user_id> <reason>`: Issue official warning (auto-ban on 3 warnings).
- `/admin_ban <user_id> <reason>` & `/admin_unban <user_id>`: Platform-wide access revocation.
- `/admin_reports`: Review unresolved user harassment and cheat reports.
- `/eco_give <user_id> <currency> <amount>`: Audit-logged admin currency grant.
- `/eco_take <user_id> <currency> <amount>`: Revoke exploited or accidental balances.
- `/broadcast <flags> <message>`: High-speed broadcast system with dead-chat cleanup.

---

## 📜 FULL COMMAND REFERENCE

| Category | Commands |
|---|---|
| **Core & Progression** | `/start`, `/help`, `/profile`, `/rank`, `/setintro`, `/top`, `/leaderboard` |
| **Virtual Economy** | `/balance`, `/wallet`, `/daily`, `/weekly`, `/monthly`, `/referral`, `/pay`, `/gift`, `/market`, `/buyitem` |
| **Original Mini Games** | `/poker`, `/roulette`, `/bluff`, `/bomb`, `/hack`, `/card`, `/wordquiz`, `/wordgrid`, `/wordseek`, `/truth`, `/dare` |
| **20 New Games** | `/tictactoe`, `/rps`, `/connect4`, `/hangman`, `/wordle`, `/memory`, `/sudoku`, `/minesweeper`, `/blackjack`, `/higherlower`, `/numberguess`, `/trivia`, `/emojiquiz`, `/chess`, `/checkers`, `/battleship`, `/quiztourney`, `/wordbattle`, `/reaction`, `/dailypuzzle`, `/ludo` |
| **Trading Cards** | `/cards`, `/cardpacks`, `/openpack`, `/upgradecard`, `/giftcard`, `/cardduel` |
| **Dungeon RPG** | `/dungeon`, `/explore`, `/attack`, `/potion`, `/flee`, `/dstats`, `/equip` |
| **Guilds & Clans** | `/guild`, `/createguild`, `/joinguild`, `/leaveguild`, `/depositguild`, `/topguilds` |
| **Friends & Social** | `/addfriend`, `/acceptfriend`, `/unfriend`, `/friendlist`, `/reportplayer` |
| **Pets & Houses** | `/adoptpet`, `/pets`, `/feedpet`, `/playpet`, `/trainpet`, `/petevolve`, `/petbattle`, `/house`, `/upgradehouse`, `/furniture`, `/buyfurniture`, `/visithouse`, `/tophouses` |
| **Missions & Events** | `/achievements`, `/topachievers`, `/missions`, `/claimmission`, `/events` |
| **AI Gaming Copilot** | `/askai`, `/gamehelp`, `/recommend` |
| **VIP & Premium** | `/vip`, `/vipperk`, `/viptiers`, `/buygems` |
| **SuperAdmin** | `/dashboard`, `/maintenance`, `/admin_warn`, `/admin_ban`, `/admin_unban`, `/admin_reports`, `/eco_give`, `/eco_take`, `/eco_set`, `/broadcast` |

---

## 🚀 INSTALLATION & DEPLOYMENT

### Prerequisites:
- Python 3.10, 3.11, or 3.12
- SQLite3 (included in standard Python)
- Valid Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Step 1: Clone & Prepare Environment
```bash
# Clone the repository
git clone https://github.com/yourusername/miko.git
cd miko

# Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```
Key configuration values:
```ini
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
OWNER_ID=7408854697
OPENROUTER_API_KEY=your_openrouter_api_key_here
SQLITE_DB_PATH=radha_data.db
```

### Step 3: Run the Bot
```bash
python main.py
```
Upon startup, Miko will automatically initialize all 30+ SQLite database tables, configure WAL mode, and register all 360+ command handlers.

### Production Deployment (Systemd VPS Service)
Create `/etc/systemd/system/miko.service`:
```ini
[Unit]
Description=Miko Telegram Gaming Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/miko
ExecStart=/home/miko/venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=/home/miko/.env

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable miko
sudo systemctl start miko
sudo systemctl status miko
```

---

## 💾 DATABASE BACKUP & RECOVERY

Because Miko uses SQLite in Write-Ahead Logging (WAL) mode, online hot backups can be taken without taking the bot offline.

### 1. Hot Backup (Zero Downtime)
```bash
# Using standard sqlite3 CLI:
sqlite3 radha_data.db ".backup 'radha_data_backup_$(date +%Y%m%d_%H%M%S).db'"
```

### 2. Automated Daily Cron Backup (Linux VPS)
Add this entry to your `crontab -e`:
```bash
0 3 * * * sqlite3 /home/miko/radha_data.db ".backup '/home/miko/backups/miko_backup_$(date +\%F).db'"
```

### 3. Database Restoration
```bash
# 1. Stop bot process
sudo systemctl stop miko

# 2. Replace database file with backup
cp backups/miko_backup_2026-11-22.db radha_data.db

# 3. Restart bot
sudo systemctl start miko
```

---

## 🧪 TESTING & VERIFICATION

Run the comprehensive unit test suite:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
All **50 test cases** across all 13 modules run and pass in under 2 seconds.

---

## 📄 LICENSE

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
