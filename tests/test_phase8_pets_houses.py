import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.utils.storage import update_user, get_user
from modules.pets.pet_manager import PetManager
from modules.pets.pet_catalog import PET_SPECIES_CATALOG
from modules.houses.house_manager import HouseManager, HOUSE_TIERS, FURNITURE_CATALOG


class TestPhase8PetsAndHouses(unittest.TestCase):
    def setUp(self):
        self.pm = PetManager.get_instance()
        self.hm = HouseManager.get_instance()
        self.user_id = 9901
        update_user(self.user_id, balance=500000, gems=50.0, level=10, xp=5000)
        from modules.utils.db import _get_conn
        conn = _get_conn()
        with conn:
            conn.execute("DELETE FROM houses WHERE user_id = ?", (str(self.user_id),))
            conn.execute("DELETE FROM house_items WHERE user_id = ?", (str(self.user_id),))
            conn.execute("DELETE FROM pets WHERE user_id = ?", (str(self.user_id),))

    def test_pet_adoption_and_actions(self):
        # Adopt a Fox named Kurama
        ok, msg, pet_data = self.pm.adopt_pet(self.user_id, "fox", "Kurama")
        self.assertTrue(ok)
        self.assertIsNotNone(pet_data)
        pet_id = pet_data["pet_id"]

        # Feed pet
        ok, msg = self.pm.feed_pet(self.user_id, pet_id)
        self.assertTrue(ok)

        # Play with pet
        ok, msg = self.pm.play_with_pet(self.user_id, pet_id)
        self.assertTrue(ok)

        # Train pet
        ok, msg = self.pm.train_pet(self.user_id, pet_id)
        self.assertTrue(ok)

        # Compete in tournament
        ok, msg = self.pm.pet_competition(self.user_id, pet_id)
        self.assertTrue(ok)

    def test_pet_evolution(self):
        ok, _, pet_data = self.pm.adopt_pet(self.user_id, "wolf", "Ghost")
        self.assertTrue(ok)
        pet_id = pet_data["pet_id"]

        # Cannot evolve below level 10
        ok, msg = self.pm.evolve_pet(self.user_id, pet_id)
        self.assertFalse(ok)

        # Manually level up to 10 for test
        from modules.utils.db import _get_conn
        conn = _get_conn()
        with conn:
            conn.execute("UPDATE pets SET level = 10 WHERE pet_id = ?", (pet_id,))

        ok, msg = self.pm.evolve_pet(self.user_id, pet_id)
        self.assertTrue(ok)
        self.assertIn("EVOLUTION", msg)

    def test_virtual_house_and_furniture(self):
        # House creation
        house = self.hm.get_or_create_house(self.user_id)
        self.assertIsNotNone(house)
        self.assertEqual(house["level"], 1)

        # Upgrade house to tier 2
        ok, msg = self.hm.upgrade_house(self.user_id)
        self.assertTrue(ok)
        house = self.hm.get_or_create_house(self.user_id)
        self.assertEqual(house["level"], 2)

        # Buy furniture
        ok, msg = self.hm.buy_furniture(self.user_id, "sofa")
        self.assertTrue(ok)

        items = self.hm.get_house_items(self.user_id)
        self.assertGreaterEqual(len(items), 1)

        # Top houses leaderboard
        top = self.hm.get_top_houses(limit=5)
        self.assertIsInstance(top, list)
        self.assertGreaterEqual(len(top), 1)


if __name__ == "__main__":
    unittest.main()
