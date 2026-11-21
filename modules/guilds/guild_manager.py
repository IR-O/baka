from __future__ import annotations

import time
import uuid
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import (
    get_user,
    update_user,
    atomic_deduct_balance,
    atomic_add_balance,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn, log_admin_action


class GuildRole:
    LEADER = "leader"
    OFFICER = "officer"
    MEMBER = "member"


class GuildManager:
    _instance: Optional[GuildManager] = None

    @classmethod
    def get_instance(cls) -> GuildManager:
        if cls._instance is None:
            cls._instance = GuildManager()
        return cls._instance

    def create_guild(self, leader_id: int, tag: str, name: str, description: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        clean_tag = tag.strip().upper()[:5]
        clean_name = name.strip()[:30]

        if len(clean_tag) < 2:
            return False, "Guild tag must be between 2 and 5 characters.", {}
        if len(clean_name) < 3:
            return False, "Guild name must be at least 3 characters.", {}

        CREATION_COST = 25000

        with _STORAGE_LOCK:
            ud = get_user(leader_id)
            if ud.get("guild_id"):
                return False, "You are already a member of a guild! Leave your current guild first.", {}
            if ud.get("level", 1) < 5:
                return False, f"You must be at least Level 5 to found a guild! (Current: Lv.{ud.get('level', 1)})", {}
            if ud.get("balance", 0) < CREATION_COST:
                return False, f"Creating a guild costs ${CREATION_COST:,} coins. You have ${ud.get('balance', 0):,}.", {}

            try:
                conn = _get_conn()
                cur = conn.cursor()
                cur.execute("SELECT guild_id FROM guilds WHERE tag = ? OR name = ?", (clean_tag, clean_name))
                if cur.fetchone():
                    return False, "A guild with this name or tag already exists!", {}

                # Clean any dangling membership if old guild was deleted
                cur.execute("DELETE FROM guild_members WHERE user_id = ?", (str(leader_id),))

                if not atomic_deduct_balance(leader_id, CREATION_COST, currency="coins", reason=f"Created guild {clean_name}"):
                    return False, "Coin transaction failed.", {}

                guild_id = f"g_{uuid.uuid4().hex[:8]}"
                with conn:
                    conn.execute("""
                        INSERT INTO guilds
                        (guild_id, name, tag, description, leader_id, level, xp, treasury_coins, treasury_gems, member_count, max_members)
                        VALUES (?, ?, ?, ?, ?, 1, 0, 0, 0, 1, 30)
                    """, (guild_id, clean_name, clean_tag, description, str(leader_id)))

                    conn.execute("""
                        INSERT OR REPLACE INTO guild_members (guild_id, user_id, role, contribution)
                        VALUES (?, ?, ?, 0)
                    """, (guild_id, str(leader_id), GuildRole.LEADER))

                update_user(leader_id, guild_id=guild_id, guild_role=GuildRole.LEADER)
                guild_data = {
                    "guild_id": guild_id,
                    "name": clean_name,
                    "tag": clean_tag,
                    "leader_id": leader_id,
                    "level": 1,
                    "treasury_coins": 0,
                    "member_count": 1,
                }
                return True, f"🏰 Guild <b>{clean_name} [{clean_tag}]</b> founded successfully!", guild_data
            except Exception as e:
                return False, f"Failed to create guild: {e}", {}

    def get_guild(self, guild_identifier: Any) -> Optional[Dict[str, Any]]:
        if isinstance(guild_identifier, dict):
            guild_identifier = guild_identifier.get("guild_id") or guild_identifier.get("tag")
        if not guild_identifier:
            return None
        guild_identifier = str(guild_identifier)
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT guild_id, name, tag, description, leader_id, level, xp, treasury_coins, treasury_gems, member_count, max_members
                FROM guilds WHERE guild_id = ? OR tag = ?
            """, (guild_identifier, guild_identifier.upper()))
            row = cur.fetchone()
            if row:
                return {
                    "guild_id": row[0],
                    "name": row[1],
                    "tag": row[2],
                    "description": row[3],
                    "leader_id": int(row[4]),
                    "level": row[5],
                    "xp": row[6],
                    "treasury_coins": row[7],
                    "treasury_gems": row[8],
                    "member_count": row[9],
                    "max_members": row[10],
                }
        except Exception as e:
            print(f"Error fetching guild: {e}")
        return None

    def get_guild_by_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("SELECT guild_id FROM guilds WHERE tag = ?", (tag.strip().upper(),))
            row = cur.fetchone()
            if row:
                return self.get_guild(row[0])
        except Exception:
            pass
        return None

    def join_guild(self, user_id: int, tag: str) -> Tuple[bool, str]:
        guild = self.get_guild_by_tag(tag)
        if not guild:
            return False, f"Guild with tag '[{tag}]' was not found."

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            if ud.get("guild_id"):
                return False, "You are already in a guild! Leave your current guild first."

            if guild["member_count"] >= guild["max_members"]:
                return False, f"Guild [{guild['tag']}] is already full ({guild['member_count']}/{guild['max_members']})."

            try:
                conn = _get_conn()
                with conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO guild_members (guild_id, user_id, role, contribution)
                        VALUES (?, ?, ?, 0)
                    """, (guild["guild_id"], str(user_id), GuildRole.MEMBER))
                    conn.execute("UPDATE guilds SET member_count = member_count + 1 WHERE guild_id = ?", (guild["guild_id"],))

                update_user(user_id, guild_id=guild["guild_id"], guild_role=GuildRole.MEMBER)
                return True, f"🎉 You have joined <b>{guild['name']} [{guild['tag']}]</b>!"
            except Exception as e:
                return False, f"Error joining guild: {e}"

    def leave_guild(self, user_id: int) -> Tuple[bool, str]:
        with _STORAGE_LOCK:
            ud = get_user(user_id)
            guild_id = ud.get("guild_id")
            if not guild_id:
                return False, "You are not a member of any guild."

            guild = self.get_guild(guild_id)
            if not guild:
                update_user(user_id, guild_id=None, guild_role=None)
                return True, "Guild record cleared."

            if guild["leader_id"] == user_id:
                return False, "As the Guild Leader, you must transfer leadership or disband the guild before leaving."

            try:
                conn = _get_conn()
                with conn:
                    conn.execute("DELETE FROM guild_members WHERE user_id = ?", (str(user_id),))
                    conn.execute("UPDATE guilds SET member_count = MAX(1, member_count - 1) WHERE guild_id = ?", (guild_id,))

                update_user(user_id, guild_id=None, guild_role=None)
                return True, f"You have left <b>{guild['name']}</b>."
            except Exception as e:
                return False, f"Error leaving guild: {e}"

    def deposit_treasury(self, user_id: int, amount: int, currency: str = "coins") -> Tuple[bool, str]:
        if amount <= 0:
            return False, "Deposit amount must be positive."

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            guild_id = ud.get("guild_id")
            if not guild_id:
                return False, "You are not in a guild! Join or create one first."

            if not atomic_deduct_balance(user_id, amount, currency=currency, reason="Guild treasury donation"):
                return False, f"Insufficient {currency} balance."

            try:
                conn = _get_conn()
                with conn:
                    if currency == "gems":
                        conn.execute("UPDATE guilds SET treasury_gems = treasury_gems + ?, xp = xp + ? WHERE guild_id = ?", (amount, amount * 100, guild_id))
                    else:
                        conn.execute("UPDATE guilds SET treasury_coins = treasury_coins + ?, xp = xp + ? WHERE guild_id = ?", (amount, int(amount * 0.1), guild_id))
                    conn.execute("UPDATE guild_members SET contribution = contribution + ? WHERE user_id = ?", (amount, str(user_id)))

                symbol = "💎" if currency == "gems" else "$"
                return True, f"🏦 Deposited {symbol}{amount:,} into the Guild Treasury! (+Guild XP awarded)"
            except Exception as e:
                return False, f"Deposit error: {e}"

    def get_top_guilds(self, limit: int = 10) -> List[Dict[str, Any]]:
        results = []
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT guild_id, name, tag, level, xp, treasury_coins, member_count
                FROM guilds
                ORDER BY level DESC, xp DESC, treasury_coins DESC
                LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            for rank, r in enumerate(rows, 1):
                results.append({
                    "rank": rank,
                    "guild_id": r[0],
                    "name": r[1],
                    "tag": r[2],
                    "level": r[3],
                    "xp": r[4],
                    "treasury_coins": r[5],
                    "member_count": r[6],
                })
        except Exception as e:
            print(f"Error fetching top guilds: {e}")
        return results
