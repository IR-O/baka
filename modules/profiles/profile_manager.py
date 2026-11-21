from __future__ import annotations

import html
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from modules.utils.storage import (
    get_user,
    update_user,
    global_rank,
)
from modules.progression.level_manager import get_level_title
from modules.utils.db import _get_conn


class ProfileManager:
    _instance: Optional[ProfileManager] = None

    @classmethod
    def get_instance(cls) -> ProfileManager:
        if cls._instance is None:
            cls._instance = ProfileManager()
        return cls._instance

    def get_detailed_profile(self, user_id: int) -> Dict[str, Any]:
        ud = get_user(user_id)

        # Update last active timestamp
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not ud.get("registered_at"):
            update_user(user_id, registered_at=now_iso, last_active=now_iso)
        else:
            update_user(user_id, last_active=now_iso)

        level = ud.get("level", 1)
        xp = ud.get("xp", 0)
        xp_max = ud.get("xp_max", 1000)
        title = get_level_title(level)

        total_games = ud.get("total_games", 0)
        games_won = ud.get("games_won", 0)
        games_lost = ud.get("games_lost", 0)
        win_rate = round((games_won / total_games * 100), 1) if total_games > 0 else 0.0

        coins_rank = global_rank(user_id, "balance")
        kills_rank = global_rank(user_id, "kills")

        # Database queries for cards, pets, guilds, achievements counts
        cards_count = self._get_cards_count(user_id)
        pets_count, active_pet = self._get_pet_info(user_id)
        guild_info = self._get_guild_info(user_id)
        achievements_count = self._get_achievements_count(user_id)

        return {
            "user_id": user_id,
            "username": ud.get("username", "User"),
            "display_name": ud.get("display_name") or ud.get("username", "User"),
            "intro_text": ud.get("intro_text") or "No personal bio set. Use /setintro to customize!",
            "level": level,
            "title": title,
            "xp": xp,
            "xp_max": xp_max,
            "balance": ud.get("balance", 0),
            "wallet_balance": ud.get("wallet_balance", 0),
            "gems": round(float(ud.get("gems", 0.0) or 0.0), 2),
            "event_tokens": ud.get("event_tokens", 0),
            "premium_tokens": ud.get("premium_tokens", 0),
            "total_games": total_games,
            "games_won": games_won,
            "games_lost": games_lost,
            "win_rate": win_rate,
            "kills": ud.get("kills", 0),
            "robs": ud.get("robs", 0),
            "coins_rank": coins_rank,
            "kills_rank": kills_rank,
            "cards_count": cards_count,
            "pets_count": pets_count,
            "active_pet": active_pet,
            "guild": guild_info,
            "achievements_count": achievements_count,
            "premium": ud.get("premium", False),
            "registered_at": ud.get("registered_at", "Recently"),
            "last_active": ud.get("last_active", "Now"),
            "shield_active": bool(ud.get("protected")),
            "house_level": ud.get("house_level", 1),
        }

    def render_profile_text(self, p: Dict[str, Any]) -> str:
        name_clean = html.escape(str(p["display_name"]))
        uname_clean = f"@{html.escape(p['username'])}" if p["username"] != "User" else "N/A"
        vip_tag = "👑 <b>VIP PREMIUM</b>" if p["premium"] else "👤 <b>STANDARD</b>"
        shield_str = "🛡️ Active" if p["shield_active"] else "🔓 Inactive"

        # Progress bar
        xp_pct = min(100, max(0, int((p["xp"] / max(1, p["xp_max"])) * 100)))
        bar_len = 10
        filled = int(bar_len * (xp_pct / 100))
        bar = "▰" * filled + "▱" * (bar_len - filled)

        pet_str = f"{p['active_pet']['name']} ({p['active_pet']['species']})" if p.get("active_pet") else "None (Adopt at /pet)"
        guild_str = f"{p['guild']['name']} [{p['guild']['tag']}] ({p['guild']['role']})" if p.get("guild") else "None (Join at /guild)"

        text = (
            f"👤 <b>{name_clean}</b> | {vip_tag}\n"
            f"🆔 <code>{p['user_id']}</code> | 🏷️ {uname_clean}\n"
            f"💬 <i>\"{html.escape(p['intro_text'])}\"</i>\n\n"
            f"🎖️ <b>Title:</b> {p['title']}\n"
            f"🟤 <b>Level {p['level']}:</b> {p['xp']:,} / {p['xp_max']:,} XP\n"
            f"   <code>[{bar}] {xp_pct}%</code>\n\n"
            f"💰 <b>FINANCES</b>\n"
            f"• Coins: <b>${p['balance']:,}</b> (Rank #{p['coins_rank']})\n"
            f"• Vault: <b>${p['wallet_balance']:,}</b>\n"
            f"• Gems: <b>{p['gems']} 💎</b>\n"
            f"• Event Tokens: <b>{p['event_tokens']} 🎟️</b> | VIP: <b>{p['premium_tokens']} 👑</b>\n\n"
            f"🎮 <b>GAMING RECORD</b>\n"
            f"• Total Games: <b>{p['total_games']:,}</b>\n"
            f"• Won: <b>{p['games_won']:,}</b> | Lost: <b>{p['games_lost']:,}</b>\n"
            f"• Win Rate: <b>{p['win_rate']}%</b>\n"
            f"• PvP Kills: <b>{p['kills']}</b> (Rank #{p['kills_rank']}) | Robberies: <b>{p['robs']}</b>\n\n"
            f"🏰 <b>SOCIAL & ASSETS</b>\n"
            f"• Guild: <b>{guild_str}</b>\n"
            f"• Pet: <b>{pet_str}</b>\n"
            f"• Cards Collected: <b>{p['cards_count']} cards</b>\n"
            f"• Achievements: <b>{p['achievements_count']} completed</b>\n"
            f"• House Tier: <b>Level {p['house_level']} Estate</b>\n"
            f"• Shield: <b>{shield_str}</b>\n\n"
            f"📅 Registered: <code>{p['registered_at']}</code>"
        )
        return text

    def set_intro(self, user_id: int, intro_text: str) -> Tuple[bool, str]:
        cleaned = intro_text.strip()[:150]
        if not cleaned:
            return False, "Intro text cannot be empty."
        update_user(user_id, intro_text=cleaned)
        return True, "✅ Your profile bio has been updated!"

    def _get_cards_count(self, user_id: int) -> int:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM card_ownership WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            return row[0] if row else 0
        except Exception:
            return 0

    def _get_pet_info(self, user_id: int) -> Tuple[int, Optional[Dict[str, Any]]]:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("SELECT pet_id, species, name, rarity, level FROM pets WHERE user_id = ?", (str(user_id),))
            rows = cur.fetchall()
            count = len(rows)
            active = None
            if count > 0:
                active = {
                    "id": rows[0][0],
                    "species": rows[0][1],
                    "name": rows[0][2],
                    "rarity": rows[0][3],
                    "level": rows[0][4],
                }
            return count, active
        except Exception:
            return 0, None

    def _get_guild_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT g.name, g.tag, gm.role
                FROM guild_members gm
                JOIN guilds g ON gm.guild_id = g.guild_id
                WHERE gm.user_id = ?
            """, (str(user_id),))
            row = cur.fetchone()
            if row:
                return {"name": row[0], "tag": row[1], "role": row[2].capitalize()}
        except Exception:
            pass
        return None

    def _get_achievements_count(self, user_id: int) -> int:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM player_achievements WHERE user_id = ? AND completed = 1", (str(user_id),))
            row = cur.fetchone()
            return row[0] if row else 0
        except Exception:
            return 0
