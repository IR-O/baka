from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import (
    get_user,
    update_user,
    get_all_users,
    atomic_add_balance,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn

# Title brackets by level
LEVEL_TITLES: List[Tuple[int, str]] = [
    (100, "🌌 Immortal Legend"),
    (75, "⚡ Mythic Sovereign"),
    (50, "👑 Grandmaster"),
    (30, "🔮 Master of Games"),
    (20, "⚔️ Elite Champion"),
    (10, "🥇 Veteran Duelist"),
    (5, "🥈 Rising Challenger"),
    (1, "🥉 Novice Adventurer"),
]


def get_level_title(level: int) -> str:
    for min_lvl, title in LEVEL_TITLES:
        if level >= min_lvl:
            return title
    return "🥉 Novice Adventurer"


class LevelManager:
    _instance: Optional[LevelManager] = None

    @classmethod
    def get_instance(cls) -> LevelManager:
        if cls._instance is None:
            cls._instance = LevelManager()
        return cls._instance

    @staticmethod
    def calculate_xp_required(level: int) -> int:
        """Configurable XP progression curve: Base 1000 with 1.35x scaling."""
        return int(1000 * (1.35 ** max(0, level - 1)))

    def add_experience(self, user_id: int, amount: int, reason: str = "") -> Tuple[Dict[str, Any], bool, Dict[str, Any]]:
        """
        Adds XP considering daily limits.
        Returns: (user_doc, did_level_up, level_rewards)
        """
        if amount <= 0:
            return get_user(user_id), False, {}

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            today_str = datetime.now().strftime("%Y-%m-%d")
            last_date = ud.get("last_xp_date")
            daily_earned = ud.get("daily_xp_earned", 0)

            if last_date != today_str:
                daily_earned = 0
                last_date = today_str

            DAILY_CAP = 10000 if ud.get("premium") else 5000
            allowed_xp = max(0, min(amount, DAILY_CAP - daily_earned))
            if allowed_xp <= 0:
                return ud, False, {}

            daily_earned += allowed_xp
            curr_xp = (ud.get("xp") or 0) + allowed_xp
            curr_level = ud.get("level") or 1
            xp_max = ud.get("xp_max") or self.calculate_xp_required(curr_level)

            did_level_up = False
            total_reward_coins = 0
            total_reward_gems = 0.0
            total_reward_tokens = 0

            while curr_xp >= xp_max:
                curr_xp -= xp_max
                curr_level += 1
                xp_max = self.calculate_xp_required(curr_level)
                did_level_up = True

                # Calculate rewards per level attained
                lvl_coins = curr_level * 1000
                lvl_gems = round(0.1 * (curr_level // 5), 2)
                lvl_tokens = 5

                total_reward_coins += lvl_coins
                total_reward_gems += lvl_gems
                total_reward_tokens += lvl_tokens

            if did_level_up:
                atomic_add_balance(user_id, total_reward_coins, currency="coins", reason=f"Level-up reward: Level {curr_level}")
                if total_reward_gems > 0:
                    atomic_add_balance(user_id, total_reward_gems, currency="gems", reason=f"Level-up reward: Level {curr_level}")
                if total_reward_tokens > 0:
                    atomic_add_balance(user_id, total_reward_tokens, currency="event_tokens", reason=f"Level-up reward: Level {curr_level}")

            updated_user = update_user(
                user_id,
                xp=curr_xp,
                level=curr_level,
                xp_max=xp_max,
                daily_xp_earned=daily_earned,
                last_xp_date=today_str,
            )

            rewards = {
                "level": curr_level,
                "title": get_level_title(curr_level),
                "coins": total_reward_coins,
                "gems": total_reward_gems,
                "tokens": total_reward_tokens,
            }
            return updated_user or ud, did_level_up, rewards

    def get_xp_rankings(self, limit: int = 10) -> List[Dict[str, Any]]:
        users = get_all_users()
        ranked = sorted(
            users.items(),
            key=lambda x: (x[1].get("level", 1) * 1000000) + x[1].get("xp", 0),
            reverse=True
        )[:limit]

        results = []
        for rank, (uid, info) in enumerate(ranked, 1):
            name = info.get("display_name") or info.get("username") or f"User {uid}"
            results.append({
                "rank": rank,
                "user_id": int(uid),
                "name": name,
                "level": info.get("level", 1),
                "xp": info.get("xp", 0),
                "title": get_level_title(info.get("level", 1)),
                "premium": info.get("premium", False),
            })
        return results
