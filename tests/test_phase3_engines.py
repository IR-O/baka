import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.core.game_engine import (
    BaseGame,
    GameSession,
    CentralGamingEngine,
    GameDifficulty,
    SessionStatus,
)
from modules.core.economy_engine import EconomyEngine, MARKETPLACE_CATALOG
from modules.utils.storage import get_user, update_user


class MockMiniGame(BaseGame):
    def __init__(self):
        super().__init__(
            game_id="mock_duel",
            game_name="Mock Duel",
            description="A simple 2-player test game",
            min_players=2,
            max_players=2,
            default_stake=100.0,
            cooldown_seconds=3.0,
            timeout_seconds=60.0,
        )

    def initialize_session(self, session: GameSession) -> None:
        session.state = {"round": 1, "scores": {}}

    def process_action(self, session: GameSession, user_id: int, action: str, data: dict):
        if action == "score":
            session.state["scores"][str(user_id)] = data.get("points", 10)
            return True, "Score recorded", session.state
        return False, "Invalid action", session.state


class TestPhase3Engines(unittest.TestCase):
    def setUp(self):
        self.user1 = 888801
        self.user2 = 888802
        update_user(self.user1, balance=5000, gems=10.0, event_tokens=0, xp=100, level=1, inventory={}, games_won=0, games_lost=0, total_games=0, daily_streak=0, last_daily=None, weekly_rewards_claimed=None, referred_by=None)
        update_user(self.user2, balance=3000, gems=5.0, event_tokens=0, xp=50, level=1, inventory={}, games_won=0, games_lost=0, total_games=0, daily_streak=0, last_daily=None, weekly_rewards_claimed=None, referred_by=None)

        self.gaming_engine = CentralGamingEngine.get_instance()
        self.economy_engine = EconomyEngine.get_instance()

        if not self.gaming_engine.get_game("mock_duel"):
            self.gaming_engine.register_game(MockMiniGame())

    def test_game_engine_lifecycle(self):
        # 1. Create session
        session, err = self.gaming_engine.create_session(
            game_id="mock_duel",
            chat_id=-100112233,
            host_id=self.user1,
            host_name="PlayerOne",
            stake=100.0,
            difficulty=GameDifficulty.NORMAL,
        )
        self.assertIsNotNone(session)
        self.assertEqual(session.status, SessionStatus.WAITING)
        self.assertEqual(len(session.players), 1)

        # Host stake deducted
        u1 = get_user(self.user1)
        self.assertEqual(u1["balance"], 4900)

        # 2. Join session
        ok, join_msg = self.gaming_engine.join_session(session.session_id, self.user2, "PlayerTwo")
        self.assertTrue(ok)
        self.assertEqual(len(session.players), 2)
        u2 = get_user(self.user2)
        self.assertEqual(u2["balance"], 2900)

        # 3. Process action
        game = self.gaming_engine.get_game("mock_duel")
        val, msg, state = game.process_action(session, self.user1, "score", {"points": 50})
        self.assertTrue(val)
        self.assertEqual(state["scores"][str(self.user1)], 50)

        # 4. Finalize game
        payouts = self.gaming_engine.finalize_game(session.session_id, winner_id=self.user1)
        self.assertIn("coins", payouts)
        self.assertGreater(payouts["coins"], 0)

        u1_after = get_user(self.user1)
        self.assertGreater(u1_after["balance"], 4900)
        self.assertEqual(u1_after["games_won"], 1)

    def test_economy_daily_and_weekly_rewards(self):
        # Daily
        ok, msg, rewards = self.economy_engine.claim_daily_reward(self.user1)
        self.assertTrue(ok)
        self.assertIn("coins", rewards)

        # Immediate re-claim blocked
        ok2, msg2, _ = self.economy_engine.claim_daily_reward(self.user1)
        self.assertFalse(ok2)
        self.assertIn("already claimed", msg2)

        # Weekly
        ok_w, msg_w, r_w = self.economy_engine.claim_weekly_reward(self.user1)
        self.assertTrue(ok_w)
        self.assertIn("coins", r_w)
        self.assertIn("gems", r_w)

    def test_marketplace_buy_and_sell(self):
        initial_bal = get_user(self.user2)["balance"]
        potion_price = MARKETPLACE_CATALOG["health_potion"]["buy_price"]
        sell_price = MARKETPLACE_CATALOG["health_potion"]["sell_price"]

        # Buy 2 potions
        ok, msg = self.economy_engine.buy_item(self.user2, "health_potion", count=2)
        self.assertTrue(ok)

        u2 = get_user(self.user2)
        self.assertEqual(u2["balance"], initial_bal - (potion_price * 2))
        self.assertEqual(u2["inventory"]["health_potion"], 2)

        # Sell 1 potion
        ok_sell, msg_sell = self.economy_engine.sell_item(self.user2, "health_potion", count=1)
        self.assertTrue(ok_sell)

        u2_after = get_user(self.user2)
        self.assertEqual(u2_after["balance"], initial_bal - (potion_price * 2) + sell_price)
        self.assertEqual(u2_after["inventory"]["health_potion"], 1)

    def test_referral_system(self):
        ref_code = f"REF{self.user1}"
        ok, msg = self.economy_engine.process_referral(self.user2, ref_code)
        self.assertTrue(ok)

        # Re-applying should fail
        ok2, msg2 = self.economy_engine.process_referral(self.user2, ref_code)
        self.assertFalse(ok2)

    def test_economy_metrics(self):
        metrics = self.economy_engine.calculate_economy_metrics()
        self.assertGreater(metrics["total_users"], 0)
        self.assertGreater(metrics["total_coins"], 0)


if __name__ == "__main__":
    unittest.main()
