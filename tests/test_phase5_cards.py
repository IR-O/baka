import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.cards.card_catalog import CARDS_CATALOG, PACK_DEFINITIONS, CardRarity
from modules.cards.card_manager import CardManager
from modules.utils.storage import update_user, get_user


class TestPhase5Cards(unittest.TestCase):
    def setUp(self):
        self.user_a = 666601
        self.user_b = 666602
        update_user(self.user_a, balance=50000, gems=10.0, xp=100, level=5)
        update_user(self.user_b, balance=10000, gems=2.0, xp=50, level=2)
        from modules.utils.db import _get_conn
        conn = _get_conn()
        with conn:
            conn.execute("DELETE FROM card_ownership WHERE user_id IN (?, ?)", (str(self.user_a), str(self.user_b)))
        self.cm = CardManager.get_instance()

    def test_rarity_catalog(self):
        rarities = {c["rarity"] for c in CARDS_CATALOG.values()}
        expected_rarities = [
            CardRarity.COMMON,
            CardRarity.UNCOMMON,
            CardRarity.RARE,
            CardRarity.EPIC,
            CardRarity.LEGENDARY,
            CardRarity.MYTHIC,
            CardRarity.LIMITED_EDITION,
        ]
        for r in expected_rarities:
            self.assertIn(r, rarities, f"Missing cards with rarity {r}")

    def test_open_pack_and_ownership(self):
        ok, msg, drawn = self.cm.open_pack(self.user_a, "bronze")
        self.assertTrue(ok)
        self.assertEqual(len(drawn), 3)

        cards = self.cm.get_user_cards(self.user_a)
        self.assertGreater(len(cards), 0)

    def test_upgrade_card(self):
        # Give a card directly
        self.cm._add_card_to_user(self.user_a, "c_goblin_scout")
        cards_before = self.cm.get_user_cards(self.user_a)
        card_before = next(c for c in cards_before if c["card_id"] == "c_goblin_scout")
        initial_atk = card_before["attack"]

        ok, msg = self.cm.upgrade_card(self.user_a, "c_goblin_scout")
        self.assertTrue(ok)

        cards_after = self.cm.get_user_cards(self.user_a)
        card_after = next(c for c in cards_after if c["card_id"] == "c_goblin_scout")
        self.assertEqual(card_after["level"], 2)
        self.assertGreater(card_after["attack"], initial_atk)

    def test_gift_card(self):
        self.cm._add_card_to_user(self.user_a, "u_pyro_imp")
        ok, msg = self.cm.gift_card(self.user_a, self.user_b, "u_pyro_imp")
        self.assertTrue(ok)

        cards_b = self.cm.get_user_cards(self.user_b)
        self.assertTrue(any(c["card_id"] == "u_pyro_imp" for c in cards_b))

    def test_simulate_card_duel(self):
        self.cm._add_card_to_user(self.user_a, "r_thunder_knight")
        duel = self.cm.simulate_card_duel(self.user_a, "r_thunder_knight", user_b_id=0)
        self.assertIn("winner_a", duel)
        self.assertIn("battle_log", duel)
        self.assertGreater(len(duel["battle_log"]), 0)


if __name__ == "__main__":
    unittest.main()
