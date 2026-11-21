"""
Miko Telegram Gaming Platform - Mission & Event Manager
Handles daily and weekly quests, automatic reset dates, claimable rewards, and seasonal event campaigns.
"""

from __future__ import annotations

import datetime
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import (
    get_user,
    atomic_add_balance,
    add_xp,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn


DEFAULT_MISSIONS = [
    {
        "id": "daily_play",
        "category": "daily",
        "description": "Play 3 mini-games in chat",
        "target": 3,
        "reward_coins": 1500,
        "reward_gems": 0.0,
        "reward_xp": 100,
        "reward_tokens": 1,
    },
    {
        "id": "daily_win",
        "category": "daily",
        "description": "Claim victory in at least 1 game",
        "target": 1,
        "reward_coins": 2500,
        "reward_gems": 1.0,
        "reward_xp": 150,
        "reward_tokens": 2,
    },
    {
        "id": "daily_feed",
        "category": "daily",
        "description": "Feed your virtual pet companion",
        "target": 1,
        "reward_coins": 1000,
        "reward_gems": 0.0,
        "reward_xp": 80,
        "reward_tokens": 1,
    },
    {
        "id": "daily_crawl",
        "category": "daily",
        "description": "Explore a room in the Dungeon RPG",
        "target": 1,
        "reward_coins": 3000,
        "reward_gems": 0.0,
        "reward_xp": 200,
        "reward_tokens": 2,
    },
    {
        "id": "weekly_wins",
        "category": "weekly",
        "description": "Win 10 mini-games this week",
        "target": 10,
        "reward_coins": 20000,
        "reward_gems": 5.0,
        "reward_xp": 1500,
        "reward_tokens": 10,
    },
    {
        "id": "weekly_packs",
        "category": "weekly",
        "description": "Open 3 collectible card packs",
        "target": 3,
        "reward_coins": 25000,
        "reward_gems": 8.0,
        "reward_xp": 2000,
        "reward_tokens": 12,
    },
]


class MissionManager:
    _instance: Optional[MissionManager] = None

    @classmethod
    def get_instance(cls) -> MissionManager:
        if cls._instance is None:
            cls._instance = MissionManager()
            cls._instance._ensure_seeded()
        return cls._instance

    def _ensure_seeded(self):
        try:
            conn = _get_conn()
            with conn:
                for m in DEFAULT_MISSIONS:
                    conn.execute("""
                        INSERT OR REPLACE INTO missions
                        (mission_id, category, description, target_count, reward_coins, reward_gems, reward_xp, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """, (m["id"], m["category"], m["description"], m["target"], m["reward_coins"], m["reward_gems"], m["reward_xp"]))
        except Exception as e:
            print(f"Error seeding missions: {e}")

    def _get_reset_date(self, category: str) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        if category == "weekly":
            return now.strftime("%Y-W%W")
        return now.strftime("%Y-%m-%d")

    def progress_mission(self, user_id: int, mission_id: str, increment: int = 1) -> bool:
        m_def = next((m for m in DEFAULT_MISSIONS if m["id"] == mission_id), None)
        if not m_def:
            return False

        reset_date = self._get_reset_date(m_def["category"])
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT progress, completed, claimed
                FROM player_missions
                WHERE user_id = ? AND mission_id = ? AND reset_date = ?
            """, (str(user_id), mission_id, reset_date))
            row = cur.fetchone()

            if row and row[1]:
                # Already completed
                return False

            current = (row[0] if row else 0) + increment
            completed = 1 if current >= m_def["target"] else 0

            with conn:
                conn.execute("""
                    INSERT INTO player_missions (user_id, mission_id, progress, completed, claimed, reset_date)
                    VALUES (?, ?, ?, ?, 0, ?)
                    ON CONFLICT(user_id, mission_id, reset_date) DO UPDATE SET
                        progress = excluded.progress,
                        completed = excluded.completed
                """, (str(user_id), mission_id, current, completed, reset_date))
            return bool(completed)
        except Exception as e:
            print(f"Error progressing mission: {e}")
            return False

    def get_user_missions(self, user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        result = {"daily": [], "weekly": []}
        try:
            conn = _get_conn()
            cur = conn.cursor()
            for m in DEFAULT_MISSIONS:
                reset_date = self._get_reset_date(m["category"])
                cur.execute("""
                    SELECT progress, completed, claimed
                    FROM player_missions
                    WHERE user_id = ? AND mission_id = ? AND reset_date = ?
                """, (str(user_id), m["id"], reset_date))
                row = cur.fetchone()

                prog = row[0] if row else 0
                comp = bool(row[1]) if row else False
                claimed = bool(row[2]) if row else False

                entry = {
                    "id": m["id"],
                    "description": m["description"],
                    "category": m["category"],
                    "progress": min(prog, m["target"]),
                    "target": m["target"],
                    "completed": comp,
                    "claimed": claimed,
                    "reward_coins": m["reward_coins"],
                    "reward_gems": m["reward_gems"],
                    "reward_xp": m["reward_xp"],
                    "reward_tokens": m["reward_tokens"],
                }
                result[m["category"]].append(entry)
        except Exception as e:
            print(f"Error fetching user missions: {e}")
        return result

    def claim_mission(self, user_id: int, mission_id: str) -> Tuple[bool, str]:
        m_def = next((m for m in DEFAULT_MISSIONS if m["id"] == mission_id), None)
        if not m_def:
            return False, "Mission not found."

        reset_date = self._get_reset_date(m_def["category"])
        with _STORAGE_LOCK:
            try:
                conn = _get_conn()
                cur = conn.cursor()
                cur.execute("""
                    SELECT progress, completed, claimed
                    FROM player_missions
                    WHERE user_id = ? AND mission_id = ? AND reset_date = ?
                """, (str(user_id), mission_id, reset_date))
                row = cur.fetchone()

                if not row or not row[1]:
                    return False, "This mission is not yet completed! Keep playing to complete it."
                if row[2]:
                    return False, "You have already claimed this mission reward for the current cycle!"

                with conn:
                    conn.execute("""
                        UPDATE player_missions SET claimed = 1
                        WHERE user_id = ? AND mission_id = ? AND reset_date = ?
                    """, (str(user_id), mission_id, reset_date))

                # Payout rewards
                atomic_add_balance(user_id, m_def["reward_coins"], currency="coins", reason=f"Claimed mission {m_def['id']}")
                if m_def["reward_gems"] > 0:
                    atomic_add_balance(user_id, m_def["reward_gems"], currency="gems", reason=f"Claimed mission {m_def['id']}")
                if m_def["reward_tokens"] > 0:
                    atomic_add_balance(user_id, m_def["reward_tokens"], currency="event_tokens", reason=f"Claimed mission {m_def['id']}")
                add_xp(user_id, m_def["reward_xp"])

                reward_str = f"+${m_def['reward_coins']:,} coins"
                if m_def["reward_gems"] > 0:
                    reward_str += f", +{m_def['reward_gems']} 💎"
                if m_def["reward_tokens"] > 0:
                    reward_str += f", +{m_def['reward_tokens']} 🎟️ Event Tokens"
                reward_str += f", +{m_def['reward_xp']} XP"

                return True, f"🎉 <b>MISSION CLAIMED!</b>\n\nReward: <b>{reward_str}</b>!"
            except Exception as e:
                return False, f"Database error claiming mission: {e}"

    def get_active_events(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "celestial_carnival",
                "title": "🎡 Celestial Arcade Festival",
                "description": "Double Event Tokens & +50% XP across all mini-games and dungeon raids!",
                "multiplier": 1.5,
                "status": "Active Now 🟢",
            },
            {
                "id": "void_rush",
                "title": "🌌 Void Incursion Weekend",
                "description": "Rare card pack drop rates boosted by 2x!",
                "multiplier": 2.0,
                "status": "Active Now 🟢",
            }
        ]
