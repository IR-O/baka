"""
Miko Telegram Gaming Platform - Achievement Manager
Tracks player achievements, handles unlock rewards, hidden criteria, and rankings.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple

from modules.achievements.achievement_catalog import ACHIEVEMENT_CATALOG, AchievementDef
from modules.utils.storage import (
    get_user,
    atomic_add_balance,
    add_xp,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn


class AchievementManager:
    _instance: Optional[AchievementManager] = None

    @classmethod
    def get_instance(cls) -> AchievementManager:
        if cls._instance is None:
            cls._instance = AchievementManager()
            cls._instance._ensure_seeded()
        return cls._instance

    def _ensure_seeded(self):
        try:
            conn = _get_conn()
            with conn:
                for a in ACHIEVEMENT_CATALOG:
                    conn.execute("""
                        INSERT OR REPLACE INTO achievements
                        (achievement_id, category, title, description, reward_coins, reward_gems, reward_xp, max_progress, is_hidden)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        a.id, a.category, a.title, a.description,
                        a.reward_coins, a.reward_gems, a.reward_xp,
                        a.max_progress, int(a.is_hidden)
                    ))
        except Exception as e:
            print(f"Error seeding achievements: {e}")

    def record_progress(self, user_id: int, achievement_id: str, increment: int = 1) -> Tuple[bool, Optional[str]]:
        ach_def = next((a for a in ACHIEVEMENT_CATALOG if a.id == achievement_id), None)
        if not ach_def:
            return False, None

        with _STORAGE_LOCK:
            try:
                conn = _get_conn()
                cur = conn.cursor()
                cur.execute("""
                    SELECT current_progress, completed
                    FROM player_achievements
                    WHERE user_id = ? AND achievement_id = ?
                """, (str(user_id), achievement_id))
                row = cur.fetchone()

                if row and row[1]:
                    # Already completed
                    return False, None

                current_prog = (row[0] if row else 0) + increment
                is_completed = current_prog >= ach_def.max_progress

                with conn:
                    if is_completed:
                        conn.execute("""
                            INSERT INTO player_achievements (user_id, achievement_id, current_progress, completed, unlocked_at)
                            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                            ON CONFLICT(user_id, achievement_id) DO UPDATE SET
                                current_progress = excluded.current_progress,
                                completed = 1,
                                unlocked_at = CURRENT_TIMESTAMP
                        """, (str(user_id), achievement_id, current_prog))
                    else:
                        conn.execute("""
                            INSERT INTO player_achievements (user_id, achievement_id, current_progress, completed)
                            VALUES (?, ?, ?, 0)
                            ON CONFLICT(user_id, achievement_id) DO UPDATE SET
                                current_progress = excluded.current_progress
                        """, (str(user_id), achievement_id, current_prog))

                if is_completed:
                    # Grant rewards
                    if ach_def.reward_coins > 0:
                        atomic_add_balance(user_id, ach_def.reward_coins, currency="coins", reason=f"Achievement {ach_def.title}")
                    if ach_def.reward_gems > 0:
                        atomic_add_balance(user_id, ach_def.reward_gems, currency="gems", reason=f"Achievement {ach_def.title}")
                    if ach_def.reward_xp > 0:
                        add_xp(user_id, ach_def.reward_xp)

                    reward_str = f"+${ach_def.reward_coins:,} coins"
                    if ach_def.reward_gems > 0:
                        reward_str += f", +{ach_def.reward_gems} 💎"
                    reward_str += f", +{ach_def.reward_xp} XP"

                    unlock_text = (
                        f"🏆 <b>ACHIEVEMENT UNLOCKED!</b>\n\n"
                        f"🎖️ <b>{ach_def.title}</b> ({ach_def.category})\n"
                        f"📜 <i>{ach_def.description}</i>\n"
                        f"🎁 <b>Rewards Received:</b> {reward_str}!"
                    )
                    return True, unlock_text

                return False, None
            except Exception as e:
                print(f"Error updating achievement: {e}")
                return False, None

    def get_user_achievements(self, user_id: int) -> Dict[str, Any]:
        user_achievements = {}
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT achievement_id, current_progress, completed, unlocked_at
                FROM player_achievements WHERE user_id = ?
            """, (str(user_id),))
            for r in cur.fetchall():
                user_achievements[r[0]] = {
                    "progress": r[1],
                    "completed": bool(r[2]),
                    "unlocked_at": r[3],
                }
        except Exception as e:
            print(f"Error fetching achievements: {e}")

        unlocked = []
        in_progress = []
        hidden_count = 0

        for a in ACHIEVEMENT_CATALOG:
            user_data = user_achievements.get(a.id, {"progress": 0, "completed": False, "unlocked_at": None})
            if user_data["completed"]:
                unlocked.append({
                    "id": a.id,
                    "title": a.title,
                    "category": a.category,
                    "description": a.description,
                    "unlocked_at": user_data["unlocked_at"],
                })
            elif a.is_hidden:
                hidden_count += 1
            else:
                in_progress.append({
                    "id": a.id,
                    "title": a.title,
                    "category": a.category,
                    "description": a.description,
                    "progress": user_data["progress"],
                    "max_progress": a.max_progress,
                })

        return {
            "total_unlocked": len(unlocked),
            "total_available": len(ACHIEVEMENT_CATALOG),
            "unlocked": unlocked,
            "in_progress": in_progress,
            "hidden_locked_count": hidden_count,
        }

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        leaders = []
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, COUNT(achievement_id) as total_achieved
                FROM player_achievements
                WHERE completed = 1
                GROUP BY user_id
                ORDER BY total_achieved DESC
                LIMIT ?
            """, (limit,))
            for idx, r in enumerate(cur.fetchall(), 1):
                uid = int(r[0])
                ud = get_user(uid)
                leaders.append({
                    "rank": idx,
                    "user_id": uid,
                    "name": ud.get("display_name") or ud.get("username", "Champion"),
                    "count": r[1],
                })
        except Exception as e:
            print(f"Error getting achievement leaderboard: {e}")
        return leaders
