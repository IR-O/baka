from __future__ import annotations

import os
import json
import sqlite3
import threading
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(BASE_DIR, "radha_data.db"))

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            _local.conn = conn
        except sqlite3.DatabaseError:
            # Auto-heal in case of binary corruption
            if os.path.exists(DB_PATH):
                try:
                    backup_path = DB_PATH + ".corrupt"
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(DB_PATH, backup_path)
                    for ext in ["-wal", "-shm"]:
                        if os.path.exists(DB_PATH + ext):
                            os.remove(DB_PATH + ext)
                except Exception:
                    pass
            conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            _local.conn = conn
    return _local.conn


def _init_db():
    conn = _get_conn()
    with conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=10000;")
        conn.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, data TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS groups (chat_id TEXT PRIMARY KEY, data TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS chats (chat_id TEXT PRIMARY KEY, title TEXT, username TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS users_chats (user_id TEXT PRIMARY KEY)")
        conn.execute("CREATE TABLE IF NOT EXISTS whispers (whisper_id TEXT PRIMARY KEY, data TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS sudoers (user_id TEXT PRIMARY KEY)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wordseek_leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                chat_id TEXT,
                name TEXT,
                username TEXT,
                score INTEGER,
                word_length INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wordseek_active_games (
                chat_id TEXT,
                topic_id TEXT,
                word TEXT,
                length INTEGER,
                started_by INTEGER,
                started_by_name TEXT,
                guesses TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, topic_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wordgrid_active_games (
                chat_id TEXT,
                topic_id TEXT,
                grid_data TEXT,
                words_data TEXT,
                message_id INTEGER,
                started_by INTEGER,
                started_by_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (chat_id, topic_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS anonymous_admin_links (
                chat_id TEXT PRIMARY KEY,
                user_id TEXT,
                username TEXT,
                name TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wordgrid_leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                chat_id TEXT,
                name TEXT,
                username TEXT,
                score INTEGER,
                word TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wordquiz_leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                chat_id TEXT,
                name TEXT,
                username TEXT,
                score INTEGER,
                word TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # === ADVANCED PLATFORM NORMALIZED TABLES ===
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                tx_type TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'coins',
                balance_after REAL NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_id, created_at)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                session_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                host_user_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'waiting',
                stake REAL DEFAULT 0,
                max_players INTEGER DEFAULT 2,
                players_data TEXT DEFAULT '[]',
                state_data TEXT DEFAULT '{}',
                winner_id TEXT,
                reward_payout REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_game_chat ON game_sessions(chat_id, status)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS game_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                game_key TEXT NOT NULL,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                total_won REAL DEFAULT 0,
                total_lost REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, game_key)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                card_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                element TEXT DEFAULT 'Neutral',
                attack INTEGER DEFAULT 10,
                defense INTEGER DEFAULT 10,
                hp INTEGER DEFAULT 50,
                speed INTEGER DEFAULT 10,
                image_url TEXT,
                description TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS card_ownership (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                card_id TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                count INTEGER DEFAULT 1,
                acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, card_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_card_user ON card_ownership(user_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS card_trades (
                trade_id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                sender_card_id TEXT NOT NULL,
                receiver_card_id TEXT,
                coins_offered REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS dungeons (
                dungeon_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                min_level INTEGER DEFAULT 1,
                max_floors INTEGER DEFAULT 10,
                difficulty TEXT DEFAULT 'normal',
                boss_name TEXT,
                boss_hp INTEGER,
                boss_attack INTEGER,
                coin_reward INTEGER,
                gem_reward REAL,
                xp_reward INTEGER,
                drop_item_id TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS dungeon_profiles (
                user_id TEXT PRIMARY KEY,
                level INTEGER DEFAULT 1,
                hp INTEGER DEFAULT 100,
                max_hp INTEGER DEFAULT 100,
                attack INTEGER DEFAULT 25,
                defense INTEGER DEFAULT 15,
                speed INTEGER DEFAULT 10,
                weapon TEXT DEFAULT 'Wooden Sword',
                armor TEXT DEFAULT 'Leather Tunic',
                potions INTEGER DEFAULT 3,
                dungeon_tier INTEGER DEFAULT 1,
                completed_floors INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                tag TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                leader_id TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                treasury_coins REAL DEFAULT 0,
                treasury_gems REAL DEFAULT 0,
                member_count INTEGER DEFAULT 1,
                max_members INTEGER DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                user_id TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'member',
                contribution REAL DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_guild_members ON guild_members(guild_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_wars (
                war_id TEXT PRIMARY KEY,
                challenger_guild_id TEXT NOT NULL,
                opponent_guild_id TEXT NOT NULL,
                challenger_score INTEGER DEFAULT 0,
                opponent_score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                friend_id TEXT NOT NULL,
                status TEXT DEFAULT 'accepted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, friend_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sender_id, receiver_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                pet_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                species TEXT NOT NULL,
                name TEXT NOT NULL,
                rarity TEXT DEFAULT 'Common',
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                hunger INTEGER DEFAULT 100,
                happiness INTEGER DEFAULT 100,
                stamina INTEGER DEFAULT 100,
                evolved INTEGER DEFAULT 0,
                adopted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pet_user ON pets(user_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS houses (
                user_id TEXT PRIMARY KEY,
                house_type TEXT DEFAULT 'Cozy Cottage',
                level INTEGER DEFAULT 1,
                comfort INTEGER DEFAULT 50,
                rooms_count INTEGER DEFAULT 2,
                decor_score INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS house_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_type TEXT DEFAULT 'furniture',
                comfort_bonus INTEGER DEFAULT 5,
                room TEXT DEFAULT 'living_room',
                placed INTEGER DEFAULT 0,
                acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                reward_coins REAL DEFAULT 0,
                reward_gems REAL DEFAULT 0,
                reward_xp INTEGER DEFAULT 0,
                max_progress INTEGER DEFAULT 1,
                is_hidden INTEGER DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                achievement_id TEXT NOT NULL,
                current_progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                unlocked_at TIMESTAMP,
                UNIQUE(user_id, achievement_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                mission_id TEXT PRIMARY KEY,
                category TEXT NOT NULL DEFAULT 'daily',
                description TEXT NOT NULL,
                target_count INTEGER DEFAULT 1,
                reward_coins REAL DEFAULT 1000,
                reward_gems REAL DEFAULT 0,
                reward_xp INTEGER DEFAULT 50,
                active INTEGER DEFAULT 1
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_missions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                reset_date TEXT NOT NULL,
                UNIQUE(user_id, mission_id, reset_date)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT DEFAULT 'xp_boost',
                multiplier REAL DEFAULT 1.5,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                active INTEGER DEFAULT 1
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id TEXT NOT NULL,
                action TEXT NOT NULL,
                target_user_id TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id TEXT NOT NULL,
                reported_id TEXT NOT NULL,
                chat_id TEXT,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cooldowns (
                user_id TEXT NOT NULL,
                action_key TEXT NOT NULL,
                expires_at REAL NOT NULL,
                PRIMARY KEY (user_id, action_key)
            )
        """)
    print("✅ Local VPS SQLite Storage Initialized Successfully (30+ Tables Verified)!")


_init_db()


# Compatibility dummies
def get_redis_client() -> None:
    return None


def get_mongo_db() -> None:
    return None


# --- CHATS & USERS TRACKING FOR BROADCAST ---

def add_chat(chat_id: int, title: Optional[str] = None, username: Optional[str] = None) -> None:
    cid = str(chat_id)
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO chats (chat_id, title, username) VALUES (?, ?, ?)",
                (cid, title or "Telegram Group", username or "")
            )
    except Exception as e:
        print(f"Error adding chat to SQLite: {e}")


def rm_chat(chat_id: int) -> None:
    cid = str(chat_id)
    try:
        conn = _get_conn()
        with conn:
            conn.execute("DELETE FROM chats WHERE chat_id = ?", (cid,))
    except Exception as e:
        print(f"Error removing chat from SQLite: {e}")


def get_chats() -> List[int]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM chats")
        rows = cur.fetchall()
        return [int(r[0]) for r in rows if r[0] and (r[0].startswith("-") or r[0].isdigit())]
    except Exception as e:
        print(f"Error getting chats from SQLite: {e}")
        return []


def add_user_chat(user_id: int) -> None:
    uid = str(user_id)
    try:
        conn = _get_conn()
        with conn:
            conn.execute("INSERT OR REPLACE INTO users_chats (user_id) VALUES (?)", (uid,))
    except Exception as e:
        print(f"Error adding user chat to SQLite: {e}")


def rm_user_chat(user_id: int) -> None:
    uid = str(user_id)
    try:
        conn = _get_conn()
        with conn:
            conn.execute("DELETE FROM users_chats WHERE user_id = ?", (uid,))
    except Exception as e:
        print(f"Error removing user chat from SQLite: {e}")


def get_user_chats() -> List[int]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users_chats")
        rows = cur.fetchall()
        return [int(r[0]) for r in rows if r[0] and r[0].isdigit()]
    except Exception as e:
        print(f"Error getting user chats from SQLite: {e}")
        return []


def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code (e.g. datetime)."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def _sanitize_doc(data: Any) -> Any:
    """Recursively converts non-serializable objects into JSON-compatible types."""
    if isinstance(data, dict):
        return {k: _sanitize_doc(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_sanitize_doc(v) for v in data]
    elif hasattr(data, "isoformat"):
        return data.isoformat()
    return data


# --- USER DATA LOCAL LAYER ---

def db_load_user(user_id: int) -> Optional[Dict[str, Any]]:
    uid = str(user_id)
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT data FROM users WHERE user_id = ?", (uid,))
        row = cur.fetchone()
        if row and row[0]:
            return json.loads(row[0])
    except Exception as e:
        print(f"Error loading user {uid} from SQLite: {e}")
    return None


def db_save_user(user_id: int, udata: Dict[str, Any]) -> None:
    uid = str(user_id)
    try:
        udata = _sanitize_doc(udata)
        serialized = json.dumps(udata, default=_json_serial)
        conn = _get_conn()
        with conn:
            conn.execute("INSERT OR REPLACE INTO users (user_id, data) VALUES (?, ?)", (uid, serialized))
            conn.execute("INSERT OR REPLACE INTO users_chats (user_id) VALUES (?)", (uid,))
    except Exception as e:
        print(f"Error saving user {uid} to SQLite: {e}")


def warmup_redis_cache() -> None:
    """Initializes local storage if needed."""
    _init_db()


def db_load_all_users() -> Dict[str, Dict[str, Any]]:
    res: Dict[str, Dict[str, Any]] = {}
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, data FROM users")
        for uid, data_str in cur.fetchall():
            if data_str:
                try:
                    res[str(uid)] = json.loads(data_str)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error loading all users from SQLite: {e}")
    return res


# --- SUDOERS LOCAL LAYER ---

DEFAULT_SUDOERS = {7408854697, 6605051662, 5971488185, 7810795240}


def get_owner_id() -> int:
    env_owner = os.getenv("OWNER_ID")
    if env_owner:
        try:
            return int(env_owner)
        except ValueError:
            pass
    return 7408854697


def get_all_sudoers() -> Set[int]:
    sudoers = set(DEFAULT_SUDOERS)
    sudoers.add(get_owner_id())
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM sudoers")
        for (uid,) in cur.fetchall():
            if uid and uid.isdigit():
                sudoers.add(int(uid))
    except Exception as e:
        print(f"Error loading sudoers from SQLite: {e}")
    return sudoers


def add_sudoer_to_db(user_id: int) -> None:
    DEFAULT_SUDOERS.add(user_id)
    suid = str(user_id)
    try:
        conn = _get_conn()
        with conn:
            conn.execute("INSERT OR REPLACE INTO sudoers (user_id) VALUES (?)", (suid,))
    except Exception as e:
        print(f"Error adding sudoer to SQLite: {e}")


def remove_sudoer_from_db(user_id: int) -> None:
    if user_id in DEFAULT_SUDOERS:
        DEFAULT_SUDOERS.remove(user_id)
    suid = str(user_id)
    try:
        conn = _get_conn()
        with conn:
            conn.execute("DELETE FROM sudoers WHERE user_id = ?", (suid,))
    except Exception as e:
        print(f"Error removing sudoer from SQLite: {e}")


def is_user_sudoer(user_id: int) -> bool:
    return user_id in get_all_sudoers()


add_sudo_user = add_sudoer_to_db
rm_sudo_user = remove_sudoer_from_db


def get_sudo_users() -> List[int]:
    return list(get_all_sudoers())


is_sudo_user = is_user_sudoer


# --- GROUP SETTINGS LOCAL LAYER ---

def db_load_group(chat_id: int) -> Optional[Dict[str, Any]]:
    cid = str(chat_id)
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT data FROM groups WHERE chat_id = ?", (cid,))
        row = cur.fetchone()
        if row and row[0]:
            return json.loads(row[0])
    except Exception as e:
        print(f"Error loading group {cid} from SQLite: {e}")
    return None


def db_save_group(chat_id: int, gdata: Dict[str, Any]) -> None:
    cid = str(chat_id)
    try:
        gdata = _sanitize_doc(gdata)
        serialized = json.dumps(gdata, default=_json_serial)
        conn = _get_conn()
        with conn:
            conn.execute("INSERT OR REPLACE INTO groups (chat_id, data) VALUES (?, ?)", (cid, serialized))
            conn.execute("INSERT OR REPLACE INTO chats (chat_id, title) VALUES (?, ?)", (cid, gdata.get("title", "Telegram Group")))
    except Exception as e:
        print(f"Error saving group {cid} to SQLite: {e}")


# --- WHISPERS LOCAL LAYER ---

def db_save_whisper(whisper_id: str, data: Dict[str, Any]) -> None:
    try:
        data = _sanitize_doc(data)
        serialized = json.dumps(data, default=_json_serial)
        conn = _get_conn()
        with conn:
            conn.execute("INSERT OR REPLACE INTO whispers (whisper_id, data) VALUES (?, ?)", (whisper_id, serialized))
    except Exception as e:
        print(f"Error saving whisper {whisper_id} to SQLite: {e}")


def db_load_whisper(whisper_id: str) -> Optional[Dict[str, Any]]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT data FROM whispers WHERE whisper_id = ?", (whisper_id,))
        row = cur.fetchone()
        if row and row[0]:
            return json.loads(row[0])
    except Exception as e:
        print(f"Error loading whisper {whisper_id} from SQLite: {e}")
    return None


# --- WORDSEEK SCORES & LEADERBOARDS ---

def add_wordseek_score(user_id: int, chat_id: int, name: str, username: str, score: int, word_length: int) -> None:
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                "INSERT INTO wordseek_leaderboard (user_id, chat_id, name, username, score, word_length) VALUES (?, ?, ?, ?, ?, ?)",
                (str(user_id), str(chat_id), name or "User", username or "", score, word_length)
            )
    except Exception as e:
        print(f"Error saving wordseek score: {e}")


def get_wordseek_leaderboard(chat_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                """
                SELECT user_id, name, username, SUM(score) as total_score
                FROM wordseek_leaderboard
                WHERE chat_id = ?
                GROUP BY user_id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (str(chat_id), limit)
            )
        else:
            cur.execute(
                """
                SELECT user_id, name, username, SUM(score) as total_score
                FROM wordseek_leaderboard
                GROUP BY user_id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (limit,)
            )
        rows = cur.fetchall()
        return [{"user_id": r[0], "name": r[1], "username": r[2], "totalScore": r[3]} for r in rows]
    except Exception as e:
        print(f"Error getting wordseek leaderboard: {e}")
        return []


def get_wordseek_user_score(user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                "SELECT SUM(score) FROM wordseek_leaderboard WHERE user_id = ? AND chat_id = ?",
                (str(user_id), str(chat_id))
            )
            tot_row = cur.fetchone()
            tot = (tot_row[0] if tot_row and tot_row[0] else 0)
            if tot > 0:
                cur.execute(
                    """
                    SELECT COUNT(*) + 1 FROM (
                        SELECT user_id, SUM(score) as s FROM wordseek_leaderboard
                        WHERE chat_id = ? GROUP BY user_id HAVING s > ?
                    )
                    """,
                    (str(chat_id), tot)
                )
                r_row = cur.fetchone()
                rank = r_row[0] if r_row else 1
            else:
                rank = "-"
        else:
            cur.execute(
                "SELECT SUM(score) FROM wordseek_leaderboard WHERE user_id = ?",
                (str(user_id),)
            )
            tot_row = cur.fetchone()
            tot = (tot_row[0] if tot_row and tot_row[0] else 0)
            if tot > 0:
                cur.execute(
                    """
                    SELECT COUNT(*) + 1 FROM (
                        SELECT user_id, SUM(score) as s FROM wordseek_leaderboard
                        GROUP BY user_id HAVING s > ?
                    )
                    """,
                    (tot,)
                )
                r_row = cur.fetchone()
                rank = r_row[0] if r_row else 1
            else:
                rank = "-"
        return {"totalScore": tot, "rank": rank}
    except Exception as e:
        print(f"Error getting user wordseek score: {e}")
        return {"totalScore": 0, "rank": "-"}


# --- WORDGRID SCORES & LEADERBOARDS ---

def add_wordgrid_score(user_id: int, chat_id: int, name: str, username: str, score: int, word: str) -> None:
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                "INSERT INTO wordgrid_leaderboard (user_id, chat_id, name, username, score, word) VALUES (?, ?, ?, ?, ?, ?)",
                (str(user_id), str(chat_id), name or "User", username or "", score, word)
            )
    except Exception as e:
        print(f"Error saving wordgrid score: {e}")


def get_wordgrid_leaderboard(chat_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                """
                SELECT user_id, name, username, SUM(score) as total_score
                FROM wordgrid_leaderboard
                WHERE chat_id = ?
                GROUP BY user_id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (str(chat_id), limit)
            )
        else:
            cur.execute(
                """
                SELECT user_id, name, username, SUM(score) as total_score
                FROM wordgrid_leaderboard
                GROUP BY user_id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (limit,)
            )
        rows = cur.fetchall()
        return [{"user_id": r[0], "name": r[1], "username": r[2], "totalScore": r[3]} for r in rows]
    except Exception as e:
        print(f"Error getting wordgrid leaderboard: {e}")
        return []


def get_wordgrid_user_score(user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                "SELECT SUM(score) FROM wordgrid_leaderboard WHERE user_id = ? AND chat_id = ?",
                (str(user_id), str(chat_id))
            )
            tot_row = cur.fetchone()
            tot = (tot_row[0] if tot_row and tot_row[0] else 0)
            if tot > 0:
                cur.execute(
                    """
                    SELECT COUNT(*) + 1 FROM (
                        SELECT user_id, SUM(score) as s FROM wordgrid_leaderboard
                        WHERE chat_id = ? GROUP BY user_id HAVING s > ?
                    )
                    """,
                    (str(chat_id), tot)
                )
                r_row = cur.fetchone()
                rank = r_row[0] if r_row else 1
            else:
                rank = "-"
        else:
            cur.execute(
                "SELECT SUM(score) FROM wordgrid_leaderboard WHERE user_id = ?",
                (str(user_id),)
            )
            tot_row = cur.fetchone()
            tot = (tot_row[0] if tot_row and tot_row[0] else 0)
            if tot > 0:
                cur.execute(
                    """
                    SELECT COUNT(*) + 1 FROM (
                        SELECT user_id, SUM(score) as s FROM wordgrid_leaderboard
                        GROUP BY user_id HAVING s > ?
                    )
                    """,
                    (tot,)
                )
                r_row = cur.fetchone()
                rank = r_row[0] if r_row else 1
            else:
                rank = "-"
        return {"totalScore": tot, "rank": rank}
    except Exception as e:
        print(f"Error getting user wordgrid score: {e}")
        return {"totalScore": 0, "rank": "-"}


# --- WORD QUIZ SCORES & LEADERBOARDS ---

def add_wordquiz_score(user_id: int, chat_id: int, name: str, username: str, score: int, word: str) -> None:
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                "INSERT INTO wordquiz_leaderboard (user_id, chat_id, name, username, score, word) VALUES (?, ?, ?, ?, ?, ?)",
                (str(user_id), str(chat_id), name or "User", username or "", score, word)
            )
    except Exception as e:
        print(f"Error saving wordquiz score: {e}")


def get_wordquiz_leaderboard(chat_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                """
                SELECT user_id, name, username, SUM(score) as total_score
                FROM wordquiz_leaderboard
                WHERE chat_id = ?
                GROUP BY user_id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (str(chat_id), limit)
            )
        else:
            cur.execute(
                """
                SELECT user_id, name, username, SUM(score) as total_score
                FROM wordquiz_leaderboard
                GROUP BY user_id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (limit,)
            )
        rows = cur.fetchall()
        return [{"user_id": r[0], "name": r[1], "username": r[2], "totalScore": r[3]} for r in rows]
    except Exception as e:
        print(f"Error getting wordquiz leaderboard: {e}")
        return []


def get_wordquiz_user_score(user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                "SELECT SUM(score) FROM wordquiz_leaderboard WHERE user_id = ? AND chat_id = ?",
                (str(user_id), str(chat_id))
            )
            tot_row = cur.fetchone()
            tot = (tot_row[0] if tot_row and tot_row[0] else 0)
            if tot > 0:
                cur.execute(
                    """
                    SELECT COUNT(*) + 1 FROM (
                        SELECT user_id, SUM(score) as s FROM wordquiz_leaderboard
                        WHERE chat_id = ? GROUP BY user_id HAVING s > ?
                    )
                    """,
                    (str(chat_id), tot)
                )
                r_row = cur.fetchone()
                rank = r_row[0] if r_row else 1
            else:
                rank = "-"
        else:
            cur.execute(
                "SELECT SUM(score) FROM wordquiz_leaderboard WHERE user_id = ?",
                (str(user_id),)
            )
            tot_row = cur.fetchone()
            tot = (tot_row[0] if tot_row and tot_row[0] else 0)
            if tot > 0:
                cur.execute(
                    """
                    SELECT COUNT(*) + 1 FROM (
                        SELECT user_id, SUM(score) as s FROM wordquiz_leaderboard
                        GROUP BY user_id HAVING s > ?
                    )
                    """,
                    (tot,)
                )
                r_row = cur.fetchone()
                rank = r_row[0] if r_row else 1
            else:
                rank = "-"
        return {"totalScore": tot, "rank": rank}
    except Exception as e:
        print(f"Error getting user wordquiz score: {e}")
        return {"totalScore": 0, "rank": "-"}


# --- OVERALL COMBINED LEADERBOARDS ---

def get_overall_leaderboard(chat_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                """
                SELECT user_id, name, username, SUM(score) as total_score
                FROM (
                    SELECT user_id, name, username, score, chat_id FROM wordseek_leaderboard
                    UNION ALL
                    SELECT user_id, name, username, score, chat_id FROM wordgrid_leaderboard
                    UNION ALL
                    SELECT user_id, name, username, score, chat_id FROM wordquiz_leaderboard
                )
                WHERE chat_id = ?
                GROUP BY user_id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (str(chat_id), limit)
            )
        else:
            cur.execute(
                """
                SELECT user_id, name, username, SUM(score) as total_score
                FROM (
                    SELECT user_id, name, username, score, chat_id FROM wordseek_leaderboard
                    UNION ALL
                    SELECT user_id, name, username, score, chat_id FROM wordgrid_leaderboard
                    UNION ALL
                    SELECT user_id, name, username, score, chat_id FROM wordquiz_leaderboard
                )
                GROUP BY user_id
                ORDER BY total_score DESC
                LIMIT ?
                """,
                (limit,)
            )
        rows = cur.fetchall()
        return [{"user_id": r[0], "name": r[1], "username": r[2], "totalScore": r[3]} for r in rows]
    except Exception as e:
        print(f"Error getting overall leaderboard: {e}")
        return []


def get_overall_user_score(user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if chat_id:
            cur.execute(
                """
                SELECT SUM(score) FROM (
                    SELECT user_id, score, chat_id FROM wordseek_leaderboard
                    UNION ALL
                    SELECT user_id, score, chat_id FROM wordgrid_leaderboard
                    UNION ALL
                    SELECT user_id, score, chat_id FROM wordquiz_leaderboard
                )
                WHERE user_id = ? AND chat_id = ?
                """,
                (str(user_id), str(chat_id))
            )
            tot_row = cur.fetchone()
            tot = (tot_row[0] if tot_row and tot_row[0] else 0)
            if tot > 0:
                cur.execute(
                    """
                    SELECT COUNT(*) + 1 FROM (
                        SELECT user_id, SUM(score) as s FROM (
                            SELECT user_id, score, chat_id FROM wordseek_leaderboard
                            UNION ALL
                            SELECT user_id, score, chat_id FROM wordgrid_leaderboard
                            UNION ALL
                            SELECT user_id, score, chat_id FROM wordquiz_leaderboard
                        )
                        WHERE chat_id = ? GROUP BY user_id HAVING s > ?
                    )
                    """,
                    (str(chat_id), tot)
                )
                r_row = cur.fetchone()
                rank = r_row[0] if r_row else 1
            else:
                rank = "-"
        else:
            cur.execute(
                """
                SELECT SUM(score) FROM (
                    SELECT user_id, score, chat_id FROM wordseek_leaderboard
                    UNION ALL
                    SELECT user_id, score, chat_id FROM wordgrid_leaderboard
                    UNION ALL
                    SELECT user_id, score, chat_id FROM wordquiz_leaderboard
                )
                WHERE user_id = ?
                """,
                (str(user_id),)
            )
            tot_row = cur.fetchone()
            tot = (tot_row[0] if tot_row and tot_row[0] else 0)
            if tot > 0:
                cur.execute(
                    """
                    SELECT COUNT(*) + 1 FROM (
                        SELECT user_id, SUM(score) as s FROM (
                            SELECT user_id, score, chat_id FROM wordseek_leaderboard
                            UNION ALL
                            SELECT user_id, score, chat_id FROM wordgrid_leaderboard
                            UNION ALL
                            SELECT user_id, score, chat_id FROM wordquiz_leaderboard
                        )
                        GROUP BY user_id HAVING s > ?
                    )
                    """,
                    (tot,)
                )
                r_row = cur.fetchone()
                rank = r_row[0] if r_row else 1
            else:
                rank = "-"
        return {"totalScore": tot, "rank": rank}
    except Exception as e:
        print(f"Error getting overall user score: {e}")
        return {"totalScore": 0, "rank": "-"}


# --- ACTIVE WORDSEEK GAMES PERSISTENCE ---

def save_active_wordseek_game(chat_id: int, topic_id: Optional[Any], game: Dict[str, Any]) -> None:
    try:
        t_id = str(topic_id) if topic_id else "general"
        conn = _get_conn()
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO wordseek_active_games
                (chat_id, topic_id, word, length, started_by, started_by_name, guesses)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(chat_id),
                    t_id,
                    game.get("word", ""),
                    int(game.get("length", 5)),
                    int(game.get("started_by", 0)),
                    game.get("started_by_name", "User"),
                    json.dumps(game.get("guesses", [])),
                ),
            )
    except Exception as e:
        print(f"Error saving active wordseek game: {e}")


def get_active_wordseek_game_db(chat_id: int, topic_id: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    try:
        t_id = str(topic_id) if topic_id else "general"
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT word, length, started_by, started_by_name, guesses FROM wordseek_active_games WHERE chat_id = ? AND topic_id = ?",
            (str(chat_id), t_id),
        )
        row = cur.fetchone()
        if not row and t_id != "general":
            cur.execute(
                "SELECT word, length, started_by, started_by_name, guesses FROM wordseek_active_games WHERE chat_id = ? AND topic_id = 'general'",
                (str(chat_id),),
            )
            row = cur.fetchone()

        if row:
            guesses = []
            try:
                guesses = json.loads(row[4])
            except Exception:
                pass
            return {
                "word": row[0],
                "length": row[1],
                "started_by": row[2],
                "started_by_name": row[3],
                "guesses": guesses,
                "chat_id": chat_id,
                "thread_id": topic_id,
            }
    except Exception as e:
        print(f"Error fetching active wordseek game from DB: {e}")
    return None


def delete_active_wordseek_game_db(chat_id: int, topic_id: Optional[Any] = None) -> None:
    try:
        t_id = str(topic_id) if topic_id else "general"
        conn = _get_conn()
        with conn:
            conn.execute(
                "DELETE FROM wordseek_active_games WHERE chat_id = ? AND (topic_id = ? OR topic_id = 'general')",
                (str(chat_id), t_id),
            )
    except Exception as e:
        print(f"Error deleting active wordseek game: {e}")


def update_wordseek_guesses_db(chat_id: int, topic_id: Optional[Any], guesses: List[str]) -> None:
    try:
        t_id = str(topic_id) if topic_id else "general"
        conn = _get_conn()
        with conn:
            conn.execute(
                "UPDATE wordseek_active_games SET guesses = ? WHERE chat_id = ? AND topic_id = ?",
                (json.dumps(guesses), str(chat_id), t_id),
            )
    except Exception as e:
        print(f"Error updating wordseek guesses: {e}")


# --- ACTIVE WORDGRID GAMES PERSISTENCE ---

def save_active_wordgrid_game(chat_id: int, topic_id: Optional[Any], game: Dict[str, Any]) -> None:
    try:
        t_id = str(topic_id) if topic_id else "general"
        conn = _get_conn()
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO wordgrid_active_games
                (chat_id, topic_id, grid_data, words_data, message_id, started_by, started_by_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(chat_id),
                    t_id,
                    json.dumps(game.get("grid", [])),
                    json.dumps(game.get("words", {})),
                    int(game.get("message_id", 0)),
                    int(game.get("started_by", 0)),
                    game.get("started_by_name", "User"),
                ),
            )
    except Exception as e:
        print(f"Error saving active wordgrid game: {e}")


def get_active_wordgrid_game_db(chat_id: int, topic_id: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    try:
        t_id = str(topic_id) if topic_id else "general"
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT grid_data, words_data, message_id, started_by, started_by_name FROM wordgrid_active_games WHERE chat_id = ? AND topic_id = ?",
            (str(chat_id), t_id),
        )
        row = cur.fetchone()
        if not row and t_id != "general":
            cur.execute(
                "SELECT grid_data, words_data, message_id, started_by, started_by_name FROM wordgrid_active_games WHERE chat_id = ? AND topic_id = 'general'",
                (str(chat_id),),
            )
            row = cur.fetchone()

        if row:
            grid = json.loads(row[0]) if row[0] else []
            words = json.loads(row[1]) if row[1] else {}
            return {
                "grid": grid,
                "words": words,
                "message_id": row[2],
                "started_by": row[3],
                "started_by_name": row[4],
                "chat_id": chat_id,
                "thread_id": topic_id,
            }
    except Exception as e:
        print(f"Error fetching active wordgrid game from DB: {e}")
    return None


def delete_active_wordgrid_game_db(chat_id: int, topic_id: Optional[Any] = None) -> None:
    try:
        t_id = str(topic_id) if topic_id else "general"
        conn = _get_conn()
        with conn:
            conn.execute(
                "DELETE FROM wordgrid_active_games WHERE chat_id = ? AND (topic_id = ? OR topic_id = 'general')",
                (str(chat_id), t_id),
            )
    except Exception as e:
        print(f"Error deleting active wordgrid game: {e}")


def update_wordgrid_words_db(chat_id: int, topic_id: Optional[Any], words: Dict[str, Any]) -> None:
    try:
        t_id = str(topic_id) if topic_id else "general"
        conn = _get_conn()
        with conn:
            conn.execute(
                "UPDATE wordgrid_active_games SET words_data = ? WHERE chat_id = ? AND topic_id = ?",
                (json.dumps(words), str(chat_id), t_id),
            )
    except Exception as e:
        print(f"Error updating wordgrid words: {e}")


# --- ANONYMOUS ADMIN IDENTITY MAPPING ---

def set_anonymous_link(chat_id: int, user_id: int, username: str, name: str) -> None:
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO anonymous_admin_links (chat_id, user_id, username, name, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (str(chat_id), str(user_id), username or "", name or "Admin"),
            )
    except Exception as e:
        print(f"Error saving anonymous admin link: {e}")


def get_anonymous_link(chat_id: int) -> Optional[Dict[str, Any]]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, username, name FROM anonymous_admin_links WHERE chat_id = ?",
            (str(chat_id),),
        )
        row = cur.fetchone()
        if row:
            return {
                "user_id": int(row[0]) if row[0] and row[0].isdigit() else row[0],
                "username": row[1] or "",
                "name": row[2] or "Admin",
            }
    except Exception as e:
        print(f"Error getting anonymous admin link: {e}")
    return None


def clear_anonymous_link(chat_id: int) -> None:
    try:
        conn = _get_conn()
        with conn:
            conn.execute("DELETE FROM anonymous_admin_links WHERE chat_id = ?", (str(chat_id),))
    except Exception as e:
        print(f"Error clearing anonymous admin link: {e}")


# --- AUDIT TRANSACTIONS & COOLDOWNS ---

def log_transaction(user_id: int, tx_type: str, amount: float, currency: str, balance_after: float, description: str = "") -> None:
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO transactions (user_id, tx_type, amount, currency, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(user_id), tx_type, float(amount), currency, float(balance_after), description)
            )
    except Exception as e:
        print(f"Error logging transaction for {user_id}: {e}")


def get_transaction_history(user_id: int, limit: int = 15) -> List[Dict[str, Any]]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT tx_type, amount, currency, balance_after, description, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (str(user_id), limit)
        )
        rows = cur.fetchall()
        return [
            {
                "type": r[0],
                "amount": r[1],
                "currency": r[2],
                "balance_after": r[3],
                "description": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error getting transactions for {user_id}: {e}")
        return []


def log_admin_action(admin_id: int, action: str, target_user_id: Optional[int] = None, details: str = "") -> None:
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO admin_logs (admin_id, action, target_user_id, details)
                VALUES (?, ?, ?, ?)
                """,
                (str(admin_id), action, str(target_user_id) if target_user_id else None, details)
            )
    except Exception as e:
        print(f"Error logging admin action: {e}")


def get_admin_logs(limit: int = 30) -> List[Dict[str, Any]]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT admin_id, action, target_user_id, details, created_at
            FROM admin_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cur.fetchall()
        return [
            {
                "admin_id": r[0],
                "action": r[1],
                "target_user_id": r[2],
                "details": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error getting admin logs: {e}")
        return []


def set_cooldown(user_id: int, action_key: str, duration_seconds: float) -> None:
    import time
    expires_at = time.time() + duration_seconds
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO cooldowns (user_id, action_key, expires_at) VALUES (?, ?, ?)",
                (str(user_id), action_key, expires_at)
            )
    except Exception as e:
        print(f"Error setting cooldown: {e}")


def check_cooldown(user_id: int, action_key: str) -> Tuple[bool, float]:
    """Returns (is_active, remaining_seconds)."""
    import time
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT expires_at FROM cooldowns WHERE user_id = ? AND action_key = ?",
            (str(user_id), action_key)
        )
        row = cur.fetchone()
        if row:
            remaining = row[0] - time.time()
            if remaining > 0:
                return True, round(remaining, 1)
    except Exception as e:
        print(f"Error checking cooldown: {e}")
    return False, 0.0


def record_player_report(reporter_id: int, reported_id: int, chat_id: Optional[int], reason: str) -> None:
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO player_reports (reporter_id, reported_id, chat_id, reason)
                VALUES (?, ?, ?, ?)
                """,
                (str(reporter_id), str(reported_id), str(chat_id) if chat_id else None, reason)
            )
    except Exception as e:
        print(f"Error saving player report: {e}")




