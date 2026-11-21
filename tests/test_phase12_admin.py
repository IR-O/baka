import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.utils.storage import update_user, get_user
from modules.utils.db import get_owner_id, add_sudo_user
from modules.management.admin_dashboard import AdminDashboard


class TestPhase12Admin(unittest.TestCase):
    def setUp(self):
        self.ad = AdminDashboard.get_instance()
        self.owner_id = get_owner_id()
        self.target_user = 9991
        update_user(self.target_user, balance=1000, gems=0.0, warns=0, banned=False)

    def test_authorization_and_overview(self):
        # Non-admin is rejected
        self.assertFalse(self.ad.is_authorized(99999999))
        # Owner is authorized
        self.assertTrue(self.ad.is_authorized(self.owner_id))

        # Overview data
        overview = self.ad.get_system_overview()
        self.assertIn("total_users", overview)
        self.assertIn("total_coins", overview)
        self.assertIn("total_game_sessions", overview)

    def test_moderation_warn_and_ban(self):
        # Warn 1
        ok, msg = self.ad.warn_user(self.owner_id, self.target_user, "Toxic speech")
        self.assertTrue(ok)
        ud = get_user(self.target_user)
        self.assertEqual(ud.get("warns"), 1)
        self.assertFalse(ud.get("banned"))

        # Warn 2
        self.ad.warn_user(self.owner_id, self.target_user, "Spamming")
        # Warn 3 -> triggers auto-ban!
        ok3, msg3 = self.ad.warn_user(self.owner_id, self.target_user, "Exploiting")
        self.assertTrue(ok3)
        self.assertIn("BANNED", msg3)
        ud = get_user(self.target_user)
        self.assertTrue(ud.get("banned"))

        # Unban user
        ok_unban, _ = self.ad.unban_user(self.owner_id, self.target_user)
        self.assertTrue(ok_unban)
        ud = get_user(self.target_user)
        self.assertFalse(ud.get("banned"))
        self.assertEqual(ud.get("warns"), 0)

    def test_economy_modification(self):
        # Admin give 5000 coins
        ok, msg = self.ad.eco_modify(self.owner_id, self.target_user, "give", 5000, "coins")
        self.assertTrue(ok)
        ud = get_user(self.target_user)
        self.assertEqual(ud.get("balance"), 6000)

        # Admin take 2000 coins
        ok, msg = self.ad.eco_modify(self.owner_id, self.target_user, "take", 2000, "coins")
        self.assertTrue(ok)
        ud = get_user(self.target_user)
        self.assertEqual(ud.get("balance"), 4000)

        # Admin set balance
        ok, msg = self.ad.eco_modify(self.owner_id, self.target_user, "set", 15000, "coins")
        self.assertTrue(ok)
        ud = get_user(self.target_user)
        self.assertEqual(ud.get("balance"), 15000)

    def test_maintenance_mode(self):
        # Enable maintenance
        ok, msg = self.ad.set_maintenance(self.owner_id, True)
        self.assertTrue(ok)
        self.assertTrue(self.ad.is_maintenance())

        # Disable maintenance
        ok, msg = self.ad.set_maintenance(self.owner_id, False)
        self.assertTrue(ok)
        self.assertFalse(self.ad.is_maintenance())


if __name__ == "__main__":
    unittest.main()
