"""
Miko Telegram Gaming Platform - Virtual Pet Manager
Handles pet adoption, feeding, playing, training, evolution, and competitions.
"""

from __future__ import annotations

import random
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple

from modules.pets.pet_catalog import PET_SPECIES_CATALOG, get_pet_species, PetSpecies
from modules.utils.storage import (
    get_user,
    atomic_deduct_balance,
    atomic_add_balance,
    add_xp,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn


class PetManager:
    _instance: Optional[PetManager] = None

    @classmethod
    def get_instance(cls) -> PetManager:
        if cls._instance is None:
            cls._instance = PetManager()
        return cls._instance

    def adopt_pet(self, user_id: int, species_id: str, custom_name: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        spec = get_pet_species(species_id)
        if not spec:
            available = ", ".join([f"<code>{k}</code> ({v.name})" for k, v in PET_SPECIES_CATALOG.items()])
            return False, f"Unknown species. Choose from:\n{available}", None

        name = custom_name.strip()[:24] if custom_name else spec.name

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            if ud.get("balance", 0) < spec.cost_coins:
                return False, f"You need ${spec.cost_coins:,} coins to adopt a {spec.name}. (You have ${ud.get('balance', 0):,})", None
            if spec.cost_gems > 0 and ud.get("gems", 0) < spec.cost_gems:
                return False, f"You need {spec.cost_gems} 💎 to adopt a {spec.name}. (You have {ud.get('gems', 0)} 💎)", None

            if not atomic_deduct_balance(user_id, spec.cost_coins, currency="coins", reason=f"Adopted pet {name}"):
                return False, "Failed to process coin payment.", None

            if spec.cost_gems > 0:
                if not atomic_deduct_balance(user_id, spec.cost_gems, currency="gems", reason=f"Adopted pet {name}"):
                    # Refund coins if gems deduction fails
                    atomic_add_balance(user_id, spec.cost_coins, currency="coins", reason="Refund failed adoption")
                    return False, "Failed to process gem payment.", None

            pet_id = f"pet_{uuid.uuid4().hex[:8]}"
            try:
                conn = _get_conn()
                with conn:
                    conn.execute("""
                        INSERT INTO pets
                        (pet_id, user_id, species, name, rarity, level, xp, hunger, happiness, stamina, evolved)
                        VALUES (?, ?, ?, ?, ?, 1, 0, 100, ?, ?, 0)
                    """, (pet_id, str(user_id), spec.id, name, spec.rarity, spec.base_happiness, spec.base_stamina))

                pet_data = {
                    "pet_id": pet_id,
                    "species": spec.id,
                    "name": name,
                    "rarity": spec.rarity,
                    "rarity_badge": spec.rarity_badge,
                    "level": 1,
                    "xp": 0,
                    "hunger": 100,
                    "happiness": spec.base_happiness,
                    "stamina": spec.base_stamina,
                    "evolved": 0,
                }
                return True, f"🐾 Congratulations! You adopted <b>{name}</b> the {spec.rarity_badge} {spec.name}!", pet_data
            except Exception as e:
                return False, f"Database error during adoption: {e}", None

    def get_user_pets(self, user_id: int) -> List[Dict[str, Any]]:
        pets = []
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT pet_id, species, name, rarity, level, xp, hunger, happiness, stamina, evolved, adopted_at
                FROM pets WHERE user_id = ? ORDER BY level DESC, rarity DESC
            """, (str(user_id),))
            rows = cur.fetchall()
            for r in rows:
                spec = PET_SPECIES_CATALOG.get(r[1])
                badge = spec.rarity_badge if spec else "⚪"
                pets.append({
                    "pet_id": r[0],
                    "species": r[1],
                    "name": r[2],
                    "rarity": r[3],
                    "rarity_badge": badge,
                    "level": r[4],
                    "xp": r[5],
                    "hunger": r[6],
                    "happiness": r[7],
                    "stamina": r[8],
                    "evolved": bool(r[9]),
                    "adopted_at": r[10],
                })
        except Exception as e:
            print(f"Error fetching pets: {e}")
        return pets

    def get_pet(self, pet_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            if user_id:
                cur.execute("""
                    SELECT pet_id, species, name, rarity, level, xp, hunger, happiness, stamina, evolved, user_id
                    FROM pets WHERE pet_id = ? AND user_id = ?
                """, (pet_id, str(user_id)))
            else:
                cur.execute("""
                    SELECT pet_id, species, name, rarity, level, xp, hunger, happiness, stamina, evolved, user_id
                    FROM pets WHERE pet_id = ?
                """, (pet_id,))
            r = cur.fetchone()
            if r:
                spec = PET_SPECIES_CATALOG.get(r[1])
                badge = spec.rarity_badge if spec else "⚪"
                return {
                    "pet_id": r[0],
                    "species": r[1],
                    "name": r[2],
                    "rarity": r[3],
                    "rarity_badge": badge,
                    "level": r[4],
                    "xp": r[5],
                    "hunger": r[6],
                    "happiness": r[7],
                    "stamina": r[8],
                    "evolved": bool(r[9]),
                    "user_id": int(r[10]),
                }
        except Exception as e:
            print(f"Error fetching pet: {e}")
        return None

    def feed_pet(self, user_id: int, pet_id: Optional[str] = None) -> Tuple[bool, str]:
        pets = self.get_user_pets(user_id)
        if not pets:
            return False, "You do not own any pets! Adopt one with <code>/adoptpet &lt;species&gt; [name]</code>."

        target = pets[0]
        if pet_id:
            for p in pets:
                if p["pet_id"] == pet_id:
                    target = p
                    break

        FEED_COST = 100
        ud = get_user(user_id)
        if ud.get("balance", 0) < FEED_COST:
            return False, f"Pet food costs ${FEED_COST} coins. You have ${ud.get('balance', 0):,}."

        if not atomic_deduct_balance(user_id, FEED_COST, currency="coins", reason=f"Fed pet {target['name']}"):
            return False, "Coin transaction failed."

        new_hunger = min(100, target["hunger"] + 40)
        new_happiness = min(100, target["happiness"] + 15)

        try:
            conn = _get_conn()
            with conn:
                conn.execute("UPDATE pets SET hunger = ?, happiness = ? WHERE pet_id = ?", (new_hunger, new_happiness, target["pet_id"]))
            return True, f"🍖 You fed <b>{target['name']}</b>! Hunger: {new_hunger}/100, Happiness: {new_happiness}/100."
        except Exception as e:
            return False, f"Database error: {e}"

    def play_with_pet(self, user_id: int, pet_id: Optional[str] = None) -> Tuple[bool, str]:
        pets = self.get_user_pets(user_id)
        if not pets:
            return False, "You do not own any pets!"

        target = pets[0]
        if pet_id:
            for p in pets:
                if p["pet_id"] == pet_id:
                    target = p
                    break

        if target["stamina"] < 20:
            return False, f"😴 <b>{target['name']}</b> is too exhausted to play! Let them rest (stamina: {target['stamina']}/100)."

        new_stamina = max(0, target["stamina"] - 20)
        new_happiness = min(100, target["happiness"] + 25)
        new_xp = target["xp"] + 25

        try:
            conn = _get_conn()
            with conn:
                conn.execute("UPDATE pets SET stamina = ?, happiness = ?, xp = ? WHERE pet_id = ?", (new_stamina, new_happiness, new_xp, target["pet_id"]))
            return True, f"🎾 You played fetch with <b>{target['name']}</b>! Happiness: {new_happiness}/100 (+25 XP)."
        except Exception as e:
            return False, f"Database error: {e}"

    def train_pet(self, user_id: int, pet_id: Optional[str] = None) -> Tuple[bool, str]:
        pets = self.get_user_pets(user_id)
        if not pets:
            return False, "You do not own any pets!"

        target = pets[0]
        if pet_id:
            for p in pets:
                if p["pet_id"] == pet_id:
                    target = p
                    break

        if target["stamina"] < 30 or target["hunger"] < 25:
            return False, f"⚠️ <b>{target['name']}</b> is too hungry or tired to train! (Hunger: {target['hunger']}/100, Stamina: {target['stamina']}/100)"

        new_stamina = max(0, target["stamina"] - 30)
        new_hunger = max(0, target["hunger"] - 25)
        xp_gain = random.randint(45, 75)
        total_xp = target["xp"] + xp_gain
        current_lvl = target["level"]

        # Level up threshold: level * 100
        req_xp = current_lvl * 100
        leveled_up = False
        if total_xp >= req_xp:
            current_lvl += 1
            total_xp -= req_xp
            leveled_up = True
            # Bonus player reward on pet level up!
            atomic_add_balance(user_id, current_lvl * 500, currency="coins", reason=f"Pet leveled up to {current_lvl}")
            add_xp(user_id, current_lvl * 100)

        try:
            conn = _get_conn()
            with conn:
                conn.execute("""
                    UPDATE pets
                    SET stamina = ?, hunger = ?, xp = ?, level = ?
                    WHERE pet_id = ?
                """, (new_stamina, new_hunger, total_xp, current_lvl, target["pet_id"]))

            res = f"🏋️ You trained <b>{target['name']}</b>! Gained +{xp_gain} Pet XP."
            if leveled_up:
                res += f"\n🌟 <b>LEVEL UP!</b> {target['name']} reached <b>Level {current_lvl}</b>! Bonus +${current_lvl * 500} coins!"
            return True, res
        except Exception as e:
            return False, f"Database error: {e}"

    def evolve_pet(self, user_id: int, pet_id: Optional[str] = None) -> Tuple[bool, str]:
        pets = self.get_user_pets(user_id)
        if not pets:
            return False, "You do not own any pets!"

        target = pets[0]
        if pet_id:
            for p in pets:
                if p["pet_id"] == pet_id:
                    target = p
                    break

        if target["evolved"]:
            return False, f"🌟 <b>{target['name']}</b> has already reached their ultimate evolved form!"

        if target["level"] < 10:
            return False, f"🔒 Evolution requires <b>Level 10</b>! (Current: Lv.{target['level']})"

        spec = PET_SPECIES_CATALOG.get(target["species"])
        if not spec:
            return False, "Unknown species."

        new_name = spec.evolved_name
        try:
            conn = _get_conn()
            with conn:
                conn.execute("""
                    UPDATE pets
                    SET evolved = 1, name = ?, happiness = 100, stamina = 200
                    WHERE pet_id = ?
                """, (new_name, target["pet_id"]))

            # Reward player with 5 Gems and 2000 XP
            atomic_add_balance(user_id, 5.0, currency="gems", reason=f"Evolved pet {new_name}")
            add_xp(user_id, 2000)
            return True, f"✨ <b>DIVINE EVOLUTION!</b>\n\nYour pet evolved into <b>{new_name}</b>!\n🎁 Rewards: +5 💎 Gems, +2,000 XP!"
        except Exception as e:
            return False, f"Database error during evolution: {e}"

    def pet_competition(self, user_id: int, pet_id: Optional[str] = None) -> Tuple[bool, str]:
        pets = self.get_user_pets(user_id)
        if not pets:
            return False, "You do not own any pets!"

        target = pets[0]
        if pet_id:
            for p in pets:
                if p["pet_id"] == pet_id:
                    target = p
                    break

        if target["stamina"] < 25:
            return False, f"😴 <b>{target['name']}</b> needs at least 25 stamina to compete! (Current: {target['stamina']}/100)"

        # Competition scoring based on pet level, happiness, and evolution
        pet_power = (target["level"] * 12) + int(target["happiness"] * 0.4) + (50 if target["evolved"] else 0)
        opp_power = random.randint(30, 160)

        # Deduct stamina
        new_stamina = max(0, target["stamina"] - 25)
        conn = _get_conn()
        with conn:
            conn.execute("UPDATE pets SET stamina = ? WHERE pet_id = ?", (new_stamina, target["pet_id"]))

        if pet_power >= opp_power:
            coin_reward = random.randint(1500, 3500)
            xp_reward = random.randint(150, 300)
            atomic_add_balance(user_id, coin_reward, currency="coins", reason="Pet tournament victory")
            add_xp(user_id, xp_reward)
            return True, (
                f"🏆 <b>PET TOURNAMENT CHAMPION!</b>\n\n"
                f"🐾 <b>{target['name']}</b> outshined the competition with a score of <b>{pet_power} vs {opp_power}</b>!\n"
                f"🎁 Prizes: +${coin_reward:,} coins, +{xp_reward} XP!"
            )
        else:
            consolation = 400
            atomic_add_balance(user_id, consolation, currency="coins", reason="Pet tournament runner-up")
            return True, (
                f"🥈 <b>PET TOURNAMENT RUNNER-UP</b>\n\n"
                f"🐾 <b>{target['name']}</b> scored <b>{pet_power}</b> (Opponent: {opp_power}).\n"
                f"🎁 Consolation: +${consolation} coins."
            )
