import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.progression.level_manager import LevelManager, get_level_title
from modules.profiles.profile_manager import ProfileManager
from modules.utils.storage import update_user, get_user


class TestPhase4ProfilesProgression(unittest.TestCase):
    def setUp(self):
        self.user_id = 777701
        update_user(
            self.user_id,
            balance=10000,
            gems=5.0,
            event_tokens=20,
            level=1,
            xp=0,
            xp_max=1000,
            total_games=10,
            games_won=7,
            games_lost=3,
            daily_xp_earned=0,
            last_xp_date=None,
        )
        self.lm = LevelManager.get_instance()
        self.pm = ProfileManager.get_instance()

    def test_level_titles_and_curve(self):
        self.assertEqual(get_level_title(1), "🥉 Novice Adventurer")
        self.assertEqual(get_level_title(5), "🥈 Rising Challenger")
        self.assertEqual(get_level_title(10), "🥇 Veteran Duelist")
        self.assertEqual(get_level_title(20), "⚔️ Elite Champion")
        self.assertEqual(get_level_title(50), "👑 Grandmaster")
        self.assertEqual(get_level_title(100), "🌌 Immortal Legend")

        xp_lvl1 = self.lm.calculate_xp_required(1)
        xp_lvl2 = self.lm.calculate_xp_required(2)
        self.assertEqual(xp_lvl1, 1000)
        self.assertGreater(xp_lvl2, xp_lvl1)

    def test_xp_addition_and_level_up(self):
        u, did_lvl, rewards = self.lm.add_experience(self.user_id, 1200, reason="quest_reward")
        self.assertTrue(did_lvl)
        self.assertEqual(u["level"], 2)
        self.assertEqual(rewards["coins"], 2000)

        # Level rewards added to user balance
        u_after = get_user(self.user_id)
        self.assertEqual(u_after["balance"], 12000)

    def test_detailed_profile_generation(self):
        prof = self.pm.get_detailed_profile(self.user_id)
        self.assertEqual(prof["user_id"], self.user_id)
        self.assertEqual(prof["total_games"], 10)
        self.assertEqual(prof["games_won"], 7)
        self.assertEqual(prof["win_rate"], 70.0)
        self.assertIn("coins_rank", prof)

        text = self.pm.render_profile_text(prof)
        self.assertIn("FINANCES", text)
        self.assertIn("GAMING RECORD", text)
        self.assertIn("70.0%", text)

    def test_set_intro(self):
        ok, msg = self.pm.set_intro(self.user_id, "Testing custom player bio!")
        self.assertTrue(ok)
        u = get_user(self.user_id)
        self.assertEqual(u["intro_text"], "Testing custom player bio!")

    def test_xp_rankings(self):
        rankings = self.lm.get_xp_rankings(limit=5)
        self.assertGreater(len(rankings), 0)
        self.assertEqual(rankings[0]["rank"], 1)


if __name__ == "__main__":
    unittest.main()
