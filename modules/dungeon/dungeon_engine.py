from __future__ import annotations

import time
import random
from typing import Dict, Any, List, Optional, Tuple

from modules.dungeon.dungeon_catalog import (
    DUNGEON_LOCATIONS,
    WEAPONS_CATALOG,
    ARMOR_CATALOG,
)
from modules.utils.storage import (
    get_user,
    update_user,
    atomic_add_balance,
    add_xp_with_limits,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn


class DungeonEngine:
    _instance: Optional[DungeonEngine] = None

    def __init__(self):
        # In-memory active runs: {user_id: run_state}
        self._active_runs: Dict[int, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> DungeonEngine:
        if cls._instance is None:
            cls._instance = DungeonEngine()
        return cls._instance

    def get_or_create_rpg_profile(self, user_id: int) -> Dict[str, Any]:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT level, hp, max_hp, attack, defense, speed, weapon, armor, potions, dungeon_tier, completed_floors
                FROM dungeon_profiles WHERE user_id = ?
            """, (str(user_id),))
            row = cur.fetchone()
            if row:
                return {
                    "user_id": user_id,
                    "level": row[0],
                    "hp": row[1],
                    "max_hp": row[2],
                    "attack": row[3],
                    "defense": row[4],
                    "speed": row[5],
                    "weapon": row[6],
                    "armor": row[7],
                    "potions": row[8],
                    "dungeon_tier": row[9],
                    "completed_floors": row[10],
                }

            # Initialize profile based on overall user level
            ud = get_user(user_id)
            lvl = ud.get("level", 1)
            base_hp = 100 + (lvl - 1) * 15
            base_atk = 20 + (lvl - 1) * 4
            base_def = 10 + (lvl - 1) * 3
            base_spd = 12

            with conn:
                conn.execute("""
                    INSERT INTO dungeon_profiles
                    (user_id, level, hp, max_hp, attack, defense, speed, weapon, armor, potions, dungeon_tier, completed_floors)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Wooden Sword', 'Leather Tunic', 3, 1, 0)
                """, (str(user_id), lvl, base_hp, base_hp, base_atk, base_def, base_spd))

            return {
                "user_id": user_id,
                "level": lvl,
                "hp": base_hp,
                "max_hp": base_hp,
                "attack": base_atk,
                "defense": base_def,
                "speed": base_spd,
                "weapon": "Wooden Sword",
                "armor": "Leather Tunic",
                "potions": 3,
                "dungeon_tier": 1,
                "completed_floors": 0,
            }
        except Exception as e:
            print(f"Error fetching RPG profile: {e}")
            return {
                "user_id": user_id,
                "level": 1,
                "hp": 100,
                "max_hp": 100,
                "attack": 25,
                "defense": 15,
                "speed": 12,
                "weapon": "Wooden Sword",
                "armor": "Leather Tunic",
                "potions": 3,
                "dungeon_tier": 1,
                "completed_floors": 0,
            }

    def get_effective_stats(self, profile: Dict[str, Any]) -> Dict[str, int]:
        weapon = WEAPONS_CATALOG.get(profile.get("weapon", "Wooden Sword"), {"atk": 10, "spd": 2})
        armor = ARMOR_CATALOG.get(profile.get("armor", "Leather Tunic"), {"def": 8, "hp": 25})

        tot_atk = profile["attack"] + weapon.get("atk", 0)
        tot_def = profile["defense"] + armor.get("def", 0)
        tot_spd = profile["speed"] + weapon.get("spd", 0)
        tot_max_hp = profile["max_hp"] + armor.get("hp", 0)

        return {
            "atk": tot_atk,
            "def": tot_def,
            "spd": tot_spd,
            "max_hp": tot_max_hp,
        }

    def start_run(self, user_id: int, dungeon_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        loc_key = dungeon_id.lower().strip()
        if loc_key not in DUNGEON_LOCATIONS:
            avail = ", ".join(DUNGEON_LOCATIONS.keys())
            return False, f"Unknown dungeon '{dungeon_id}'. Available: {avail}", {}

        location = DUNGEON_LOCATIONS[loc_key]
        prof = self.get_or_create_rpg_profile(user_id)

        if prof["level"] < location["min_level"]:
            return False, f"⚠️ You need to be at least Level {location['min_level']} to enter {location['name']}! (Current: Lv.{prof['level']})", {}

        eff = self.get_effective_stats(prof)
        run_state = {
            "dungeon_id": loc_key,
            "name": location["name"],
            "emoji": location["emoji"],
            "floor": 1,
            "max_floors": location["max_floors"],
            "hp": eff["max_hp"] if prof["hp"] <= 0 else min(eff["max_hp"], prof["hp"]),
            "max_hp": eff["max_hp"],
            "potions": prof["potions"],
            "current_enemy": None,
            "loot_coins": 0,
            "loot_xp": 0,
            "started_at": time.time(),
        }
        self._active_runs[user_id] = run_state
        return True, f"⚔️ Entered <b>{location['emoji']} {location['name']}</b> (Floor 1/{location['max_floors']})! Use /explore to advance.", run_state

    def get_active_run(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self._active_runs.get(user_id)

    def explore_floor(self, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        run = self._active_runs.get(user_id)
        if not run:
            return False, "You are not currently in a dungeon! Use /dungeon to enter one.", {}

        # If already engaged in combat
        if run.get("current_enemy"):
            enemy = run["current_enemy"]
            return False, f"⚠️ You are currently in battle with <b>{enemy['name']}</b> ({enemy['hp']} HP)! Use /attack or /potion.", run

        loc = DUNGEON_LOCATIONS[run["dungeon_id"]]
        is_boss_floor = run["floor"] >= run["max_floors"]

        if is_boss_floor:
            # Spawn Boss!
            boss_info = dict(loc["boss"])
            run["current_enemy"] = {
                "name": boss_info["name"],
                "emoji": boss_info.get("emoji", "👹"),
                "hp": boss_info["hp"],
                "max_hp": boss_info["hp"],
                "attack": boss_info["attack"],
                "defense": boss_info["defense"],
                "speed": boss_info["speed"],
                "is_boss": True,
                "reward_coins": boss_info["coin_reward"],
                "reward_gems": boss_info["gem_reward"],
                "reward_xp": boss_info["xp_reward"],
                "drop": boss_info["drop"],
            }
            msg = (
                f"🚨 <b>BOSS CHAMBER REACHED! (Floor {run['floor']}/{run['max_floors']})</b>\n\n"
                f"The ground trembles as {run['current_enemy']['emoji']} <b>{run['current_enemy']['name']}</b> appears!\n"
                f"❤️ Boss HP: <b>{run['current_enemy']['hp']}</b> | ⚔️ ATK: {run['current_enemy']['attack']}\n\n"
                "👉 Use <code>/attack</code> to engage or <code>/potion</code> to heal!"
            )
            return True, msg, run

        # Standard floor room encounter roll
        roll = random.random()
        if roll < 0.60:
            # Monster encounter
            raw_mon = random.choice(loc["monsters"])
            run["current_enemy"] = {
                "name": raw_mon["name"],
                "emoji": "👾",
                "hp": raw_mon["hp"],
                "max_hp": raw_mon["hp"],
                "attack": raw_mon["attack"],
                "defense": raw_mon["defense"],
                "speed": raw_mon["speed"],
                "is_boss": False,
                "reward_coins": raw_mon["coins"],
                "reward_xp": raw_mon["xp"],
            }
            enemy = run["current_enemy"]
            msg = (
                f"⚔️ <b>MONSTER ENCOUNTER! (Floor {run['floor']})</b>\n\n"
                f"A wild <b>{enemy['name']}</b> blocks your path!\n"
                f"❤️ Enemy HP: <b>{enemy['hp']}</b> | ⚔️ ATK: {enemy['attack']}\n"
                f"Your HP: <b>{run['hp']}/{run['max_hp']}</b>\n\n"
                "👉 Use <code>/attack</code> to strike or <code>/potion</code> to heal!"
            )
            return True, msg, run

        elif roll < 0.80:
            # Treasure chest
            coins_found = random.randint(150, 450)
            run["loot_coins"] += coins_found
            potion_found = random.random() < 0.35
            if potion_found:
                run["potions"] += 1
            pot_txt = " and found a 🧪 <b>Healing Potion</b>!" if potion_found else "!"
            msg = f"🎁 <b>Treasure Room!</b> You discovered an ancient chest containing <b>${coins_found:,} coins</b>{pot_txt}"
            # Advance floor
            run["floor"] += 1
            return True, msg, run

        else:
            # Healing spring
            healed = min(run["max_hp"] - run["hp"], 40)
            run["hp"] += healed
            run["floor"] += 1
            msg = f"⛲ <b>Healing Spring!</b> Pure enchanted water restores <b>+{healed} HP</b>! (Current HP: {run['hp']}/{run['max_hp']})\nYou descend to Floor {run['floor']}."
            return True, msg, run

    def attack_enemy(self, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        run = self._active_runs.get(user_id)
        if not run or not run.get("current_enemy"):
            return False, "You are not in combat! Use /explore to advance.", {}

        enemy = run["current_enemy"]
        prof = self.get_or_create_rpg_profile(user_id)
        eff = self.get_effective_stats(prof)

        # Player strikes
        dmg_roll = random.uniform(0.9, 1.15)
        player_dmg = max(8, int((eff["atk"] * dmg_roll) - (enemy["defense"] * 0.35)))
        enemy["hp"] -= player_dmg

        transcript = [f"⚔️ You struck {enemy['name']} for <b>{player_dmg} damage</b>! ({max(0, enemy['hp'])} HP left)"]

        # Check enemy defeat
        if enemy["hp"] <= 0:
            coins = enemy.get("reward_coins", 100)
            xp = enemy.get("reward_xp", 50)
            run["loot_coins"] += coins
            run["loot_xp"] += xp
            run["current_enemy"] = None

            if enemy.get("is_boss"):
                # Boss Slain!
                gems = enemy.get("reward_gems", 0.0)
                drop_item = enemy.get("drop")
                atomic_add_balance(user_id, run["loot_coins"], currency="coins", reason=f"Dungeon {run['name']} Cleared")
                if gems > 0:
                    atomic_add_balance(user_id, gems, currency="gems", reason=f"Dungeon Boss {enemy['name']}")
                add_xp_with_limits(user_id, run["loot_xp"], reason="dungeon_boss_clear")

                # Equip or award drop
                drop_txt = f"\n💎 <b>Legendary Drop:</b> Discovered <b>{drop_item}</b>!" if drop_item else ""
                self._record_boss_victory(user_id, enemy["name"])
                del self._active_runs[user_id]

                congrats = (
                    f"🏆 <b>DUNGEON CLEARED! BOSS DEFEATED!</b>\n\n"
                    f"You have vanquished <b>{enemy['name']}</b>!\n"
                    f"💰 Total Loot: <b>${run['loot_coins']:,} coins</b>\n"
                    f"💎 Gems: <b>+{gems} 💎</b>\n"
                    f"⭐ XP Gained: <b>+{run['loot_xp']:,} XP</b>{drop_txt}\n\n"
                    "🎉 You return to town as a conquering hero!"
                )
                return True, congrats, {}

            # Advance floor
            run["floor"] += 1
            win_msg = (
                f"\n".join(transcript) +
                f"\n\n✨ <b>{enemy['name']} defeated!</b> (+${coins} coins, +{xp} XP)\n"
                f"You step forward into <b>Floor {run['floor']}/{run['max_floors']}</b>. Use /explore!"
            )
            return True, win_msg, run

        # Enemy counter-attack
        counter_dmg = max(5, int(enemy["attack"] - (eff["def"] * 0.35)))
        run["hp"] -= counter_dmg
        transcript.append(f"💥 {enemy['name']} lashed back dealing <b>{counter_dmg} damage</b>! (Your HP: {max(0, run['hp'])}/{run['max_hp']})")

        # Check player defeat
        if run["hp"] <= 0:
            del self._active_runs[user_id]
            defeat_msg = (
                f"\n".join(transcript) +
                "\n\n💀 <b>YOU HAVE FALLEN IN BATTLE!</b>\n"
                "Your party rescued you and carried you back to safety.\n"
                "Use <code>/potion</code> to heal and equip stronger armor!"
            )
            return True, defeat_msg, {}

        return True, "\n".join(transcript), run

    def use_potion(self, user_id: int) -> Tuple[bool, str]:
        run = self._active_runs.get(user_id)
        if not run:
            prof = self.get_or_create_rpg_profile(user_id)
            if prof["potions"] <= 0:
                return False, "You don't have any potions left! Buy more at /marketplace."
            with _get_conn() as conn:
                conn.execute("UPDATE dungeon_profiles SET potions = potions - 1, hp = max_hp WHERE user_id = ?", (str(user_id),))
            return True, "🧪 Drank potion! Restored HP to maximum."

        if run["potions"] <= 0:
            return False, "You have 0 potions remaining in this dungeon run!"

        run["potions"] -= 1
        healed = min(run["max_hp"] - run["hp"], 65)
        run["hp"] += healed
        return True, f"🧪 Drank Healing Potion! Restored <b>+{healed} HP</b> (Current: {run['hp']}/{run['max_hp']}). Potions left: {run['potions']}."

    def flee_dungeon(self, user_id: int) -> Tuple[bool, str]:
        run = self._active_runs.get(user_id)
        if not run:
            return False, "You are not currently in a dungeon."

        # Keep 70% of accumulated coins
        saved_coins = int(run["loot_coins"] * 0.7)
        if saved_coins > 0:
            atomic_add_balance(user_id, saved_coins, currency="coins", reason="Dungeon retreat")

        del self._active_runs[user_id]
        return True, f"🏃 Retreated safely from the dungeon! Secured <b>${saved_coins:,} coins</b> from your run."

    def equip_gear(self, user_id: int, item_name: str) -> Tuple[bool, str]:
        item_clean = item_name.strip()
        prof = self.get_or_create_rpg_profile(user_id)

        if item_clean in WEAPONS_CATALOG:
            with _get_conn() as conn:
                conn.execute("UPDATE dungeon_profiles SET weapon = ? WHERE user_id = ?", (item_clean, str(user_id)))
            return True, f"⚔️ Successfully equipped weapon: <b>{item_clean}</b> (+{WEAPONS_CATALOG[item_clean]['atk']} ATK)!"

        if item_clean in ARMOR_CATALOG:
            with _get_conn() as conn:
                conn.execute("UPDATE dungeon_profiles SET armor = ? WHERE user_id = ?", (item_clean, str(user_id)))
            return True, f"🛡️ Successfully equipped armor: <b>{item_clean}</b> (+{ARMOR_CATALOG[item_clean]['def']} DEF)!"

        return False, f"Unknown equipment '{item_name}'."

    def _record_boss_victory(self, user_id: int, boss_name: str) -> None:
        try:
            conn = _get_conn()
            with conn:
                conn.execute("UPDATE dungeon_profiles SET completed_floors = completed_floors + 1 WHERE user_id = ?", (str(user_id),))
        except Exception as e:
            print(f"Error recording boss victory: {e}")
