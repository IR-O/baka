import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.dungeon.dungeon_engine import DungeonEngine
from modules.dungeon.dungeon_catalog import DUNGEON_LOCATIONS, WEAPONS_CATALOG, ARMOR_CATALOG
from modules.utils.storage import update_user, get_user


class TestPhase6Dungeon(unittest.TestCase):
    def setUp(self):
        self.user_id = 555501
        update_user(self.user_id, balance=5000, level=10, xp=100)
        self.engine = DungeonEngine.get_instance()

    def test_dungeon_profile_and_stats(self):
        prof = self.engine.get_or_create_rpg_profile(self.user_id)
        self.assertIn("hp", prof)
        self.assertIn("weapon", prof)
        eff = self.engine.get_effective_stats(prof)
        self.assertGreater(eff["atk"], prof["attack"])

    def test_dungeon_run_lifecycle(self):
        ok, msg, run = self.engine.start_run(self.user_id, "catacombs")
        self.assertTrue(ok)
        self.assertEqual(run["floor"], 1)

        # Explore floor
        ok_exp, msg_exp, run_exp = self.engine.explore_floor(self.user_id)
        self.assertTrue(ok_exp)

        # Attack if enemy spawned, or explore again
        active_run = self.engine.get_active_run(self.user_id)
        if active_run and active_run.get("current_enemy"):
            ok_atk, msg_atk, _ = self.engine.attack_enemy(self.user_id)
            self.assertTrue(ok_atk)

    def test_potion_and_equip(self):
        # Equip weapon
        ok_w, msg_w = self.engine.equip_gear(self.user_id, "Steel Broadsword")
        self.assertTrue(ok_w)
        prof = self.engine.get_or_create_rpg_profile(self.user_id)
        self.assertEqual(prof["weapon"], "Steel Broadsword")

        # Equip armor
        ok_a, msg_a = self.engine.equip_gear(self.user_id, "Iron Plate")
        self.assertTrue(ok_a)
        prof2 = self.engine.get_or_create_rpg_profile(self.user_id)
        self.assertEqual(prof2["armor"], "Iron Plate")

        # Drink potion
        ok_p, msg_p = self.engine.use_potion(self.user_id)
        self.assertTrue(ok_p)


if __name__ == "__main__":
    unittest.main()
