import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.utils.storage import update_user, get_user
from modules.achievements.achievement_manager import AchievementManager
from modules.missions.mission_manager import MissionManager


class TestPhase9AchievementsAndMissions(unittest.TestCase):
    def setUp(self):
        self.am = AchievementManager.get_instance()
        self.mm = MissionManager.get_instance()
        self.user_id = 9955
        update_user(self.user_id, balance=1000, gems=0.0, level=1, xp=0)
        from modules.utils.db import _get_conn
        conn = _get_conn()
        with conn:
            conn.execute("DELETE FROM player_achievements WHERE user_id = ?", (str(self.user_id),))
            conn.execute("DELETE FROM player_missions WHERE user_id = ?", (str(self.user_id),))

    def test_achievement_progress_and_unlock(self):
        # Progress rookie roller (max 1)
        unlocked, text = self.am.record_progress(self.user_id, "game_first", increment=1)
        self.assertTrue(unlocked)
        self.assertIsNotNone(text)
        self.assertIn("ACHIEVEMENT UNLOCKED", text)

        # Verify reward dispensed (+1000 coins, +100 XP)
        ud = get_user(self.user_id)
        self.assertGreaterEqual(ud.get("balance", 0), 2000)
        self.assertGreaterEqual(ud.get("xp", 0), 100)

        # Cannot re-unlock
        unlocked2, _ = self.am.record_progress(self.user_id, "game_first", increment=1)
        self.assertFalse(unlocked2)

    def test_achievement_views_and_leaderboard(self):
        data = self.am.get_user_achievements(self.user_id)
        self.assertIn("unlocked", data)
        self.assertIn("in_progress", data)
        self.assertGreaterEqual(data["total_available"], 10)

        leaders = self.am.get_leaderboard(limit=5)
        self.assertIsInstance(leaders, list)

    def test_mission_progress_and_claiming(self):
        # Progress daily_feed mission (target 1)
        comp = self.mm.progress_mission(self.user_id, "daily_feed", increment=1)
        self.assertTrue(comp)

        # Claim reward
        ok, msg = self.mm.claim_mission(self.user_id, "daily_feed")
        self.assertTrue(ok)
        self.assertIn("CLAIMED", msg)

        # Cannot double-claim
        ok2, msg2 = self.mm.claim_mission(self.user_id, "daily_feed")
        self.assertFalse(ok2)
        self.assertIn("already claimed", msg2.lower())

    def test_events_listing(self):
        events = self.mm.get_active_events()
        self.assertIsInstance(events, list)
        self.assertGreaterEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
