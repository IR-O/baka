import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.utils.storage import update_user, get_user
from modules.premium.premium_manager import PremiumManager, PREMIUM_TIERS


class TestPhase10Premium(unittest.TestCase):
    def setUp(self):
        self.pm = PremiumManager.get_instance()
        self.user_id = 9977
        update_user(self.user_id, balance=1000, gems=0.0, premium=False, premium_tier=None, premium_expiry=0)

    def test_grant_premium_and_status(self):
        # Initial: free player
        sub = self.pm.check_subscription(self.user_id)
        self.assertFalse(sub["is_premium"])

        # Grant Gold VIP for 30 days
        ok, msg = self.pm.grant_premium(self.user_id, tier_key="gold", days=30, source="UnitTest")
        self.assertTrue(ok)
        self.assertIn("Gold VIP", msg)

        sub2 = self.pm.check_subscription(self.user_id)
        self.assertTrue(sub2["is_premium"])
        self.assertEqual(sub2["tier_id"], "gold")
        self.assertGreaterEqual(sub2["days_left"], 29)

    def test_claim_daily_perks(self):
        # Grant Diamond Sovereign
        self.pm.grant_premium(self.user_id, tier_key="diamond", days=7, source="UnitTest")

        # Claim perk (5 gems)
        ok, msg = self.pm.claim_daily_perks(self.user_id)
        self.assertTrue(ok)
        self.assertIn("5.0 Gems", msg)

        ud = get_user(self.user_id)
        self.assertGreaterEqual(ud.get("gems", 0), 5.0)

        # Cannot claim twice on same day
        ok2, msg2 = self.pm.claim_daily_perks(self.user_id)
        self.assertFalse(ok2)
        self.assertIn("already claimed", msg2.lower())


if __name__ == "__main__":
    unittest.main()
