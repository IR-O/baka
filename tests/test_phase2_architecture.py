import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.utils.db import (
    _get_conn,
    log_transaction,
    get_transaction_history,
    set_cooldown,
    check_cooldown,
    log_admin_action,
    get_admin_logs,
)
from modules.utils.storage import (
    get_user,
    update_user,
    atomic_add_balance,
    atomic_deduct_balance,
    atomic_transfer_balance,
    add_xp_with_limits,
    DEFAULT_USER,
)


class TestPhase2Architecture(unittest.TestCase):
    def setUp(self):
        self.test_user_a = 999901
        self.test_user_b = 999902
        update_user(self.test_user_a, balance=1000, gems=5.0, xp=100, level=1, xp_max=1000, daily_xp_earned=0, last_xp_date="")
        update_user(self.test_user_b, balance=500, gems=2.0, xp=50, level=1, xp_max=1000, daily_xp_earned=0, last_xp_date="")

    def test_database_tables_exist(self):
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        required = [
            "users", "groups", "chats", "transactions", "game_sessions",
            "game_statistics", "cards", "card_ownership", "dungeons",
            "guilds", "pets", "houses", "achievements", "missions", "events",
            "admin_logs", "cooldowns"
        ]
        for tbl in required:
            self.assertIn(tbl, tables, f"Missing table {tbl}")

    def test_default_user_schema_completeness(self):
        user = get_user(self.test_user_a)
        extended_keys = [
            "event_tokens", "premium_tokens", "daily_xp_earned",
            "total_games", "games_won", "games_lost", "house_level",
            "cards", "achievements", "inventory"
        ]
        for k in extended_keys:
            self.assertIn(k, user, f"Missing key {k} in user schema")

    def test_atomic_balance_operations(self):
        # Credit
        new_bal = atomic_add_balance(self.test_user_a, 250, currency="coins", reason="test_reward")
        self.assertEqual(new_bal, 1250)

        # Debit
        success = atomic_deduct_balance(self.test_user_a, 100, currency="coins", reason="test_spend")
        self.assertTrue(success)
        u = get_user(self.test_user_a)
        self.assertEqual(u["balance"], 1150)

        # Prevent negative balance
        fail = atomic_deduct_balance(self.test_user_a, 999999, currency="coins", reason="excessive_spend")
        self.assertFalse(fail)
        u = get_user(self.test_user_a)
        self.assertEqual(u["balance"], 1150)

    def test_atomic_transfer_balance(self):
        # Successful transfer with 10% tax
        ok, err, tax, received = atomic_transfer_balance(self.test_user_a, self.test_user_b, 200, tax_pct=0.10, reason="test_transfer")
        self.assertTrue(ok)
        self.assertEqual(tax, 20)
        self.assertEqual(received, 180)

        ua = get_user(self.test_user_a)
        ub = get_user(self.test_user_b)
        self.assertEqual(ua["balance"], 800)
        self.assertEqual(ub["balance"], 680)

        # Self-transfer should be blocked
        fail_self, err_self, _, _ = atomic_transfer_balance(self.test_user_a, self.test_user_a, 50)
        self.assertFalse(fail_self)
        self.assertIn("yourself", err_self)

    def test_cooldown_system(self):
        set_cooldown(self.test_user_a, "test_action", 5.0)
        is_cd, rem = check_cooldown(self.test_user_a, "test_action")
        self.assertTrue(is_cd)
        self.assertGreater(rem, 0.0)

        # Non-existent cooldown
        is_cd_fake, _ = check_cooldown(self.test_user_a, "unregistered_action")
        self.assertFalse(is_cd_fake)

    def test_transaction_history_audit(self):
        atomic_add_balance(self.test_user_a, 77, currency="coins", reason="Audit Test Entry")
        txs = get_transaction_history(self.test_user_a, limit=5)
        self.assertGreater(len(txs), 0)
        self.assertEqual(txs[0]["currency"], "coins")
        self.assertEqual(txs[0]["amount"], 77.0)

    def test_add_xp_with_limits(self):
        u, leveled = add_xp_with_limits(self.test_user_a, 1500, reason="game_win")
        self.assertGreater(u["level"], 1)
        self.assertTrue(leveled)


if __name__ == "__main__":
    unittest.main()
