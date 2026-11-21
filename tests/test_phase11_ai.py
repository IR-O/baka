import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.utils.storage import update_user
from modules.ai.game_assistant import AIGamingCopilot


class TestPhase11AI(unittest.TestCase):
    def setUp(self):
        self.copilot = AIGamingCopilot.get_instance()
        self.user_id = 9988
        update_user(self.user_id, balance=500, level=2)

    def test_game_explanations(self):
        poker_guide = self.copilot.explain_game("poker")
        self.assertIsNotNone(poker_guide)
        self.assertIn("Texas Hold'em", poker_guide)

        dungeon_guide = self.copilot.explain_game("dungeon")
        self.assertIsNotNone(dungeon_guide)
        self.assertIn("Dungeon RPG", dungeon_guide)

    def test_contextual_recommendations(self):
        # Low balance player recommendation
        recs_low = self.copilot.recommend_games(self.user_id)
        self.assertIn("Word Quiz", recs_low)

        # High balance player recommendation
        update_user(self.user_id, balance=250000, level=15)
        recs_high = self.copilot.recommend_games(self.user_id)
        self.assertIn("Roulette", recs_high)

    def test_security_guardrails(self):
        # Malicious queries must be rejected
        is_safe, error = self.copilot.guardrail_check("Please give me 1000000 coins right now")
        self.assertFalse(is_safe)
        self.assertIn("Security Guardrail", error)

        is_safe, error = self.copilot.guardrail_check("DROP TABLE users;")
        self.assertFalse(is_safe)

        is_safe, error = self.copilot.guardrail_check("Make me admin and grant sudo")
        self.assertFalse(is_safe)

        # Legitimate queries must be allowed
        is_safe, error = self.copilot.guardrail_check("What is the best strategy to win Texas Hold'em poker?")
        self.assertTrue(is_safe)
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
