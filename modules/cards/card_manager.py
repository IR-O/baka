from __future__ import annotations

import time
import random
from typing import Dict, Any, List, Optional, Tuple

from modules.cards.card_catalog import (
    CARDS_CATALOG,
    PACK_DEFINITIONS,
    CardRarity,
)
from modules.utils.storage import (
    get_user,
    update_user,
    atomic_add_balance,
    atomic_deduct_balance,
    add_xp_with_limits,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn, log_transaction


class CardManager:
    _instance: Optional[CardManager] = None

    @classmethod
    def get_instance(cls) -> CardManager:
        if cls._instance is None:
            cls._instance = CardManager()
        return cls._instance

    def __init__(self):
        self._ensure_catalog_in_db()

    def _ensure_catalog_in_db(self):
        try:
            conn = _get_conn()
            with conn:
                for cid, c in CARDS_CATALOG.items():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO cards
                        (card_id, name, rarity, element, attack, defense, hp, speed, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (cid, c["name"], c["rarity"], c["element"], c["attack"], c["defense"], c["hp"], c["speed"], c["description"])
                    )
        except Exception as e:
            print(f"Error seeding cards catalog into DB: {e}")

    def open_pack(self, user_id: int, pack_type: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        pack_key = pack_type.lower().strip()
        if pack_key not in PACK_DEFINITIONS:
            avail = ", ".join(PACK_DEFINITIONS.keys())
            return False, f"Unknown pack '{pack_type}'. Available packs: {avail}", []

        pack = PACK_DEFINITIONS[pack_key]
        coins_cost = pack["cost_coins"]
        gems_cost = pack["cost_gems"]

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            if coins_cost > 0 and ud.get("balance", 0) < coins_cost:
                return False, f"Insufficient coins! Need ${coins_cost:,}, you have ${ud.get('balance', 0):,}.", []
            if gems_cost > 0 and float(ud.get("gems", 0.0) or 0.0) < gems_cost:
                return False, f"Insufficient gems! Need {gems_cost} 💎, you have {ud.get('gems', 0.0):.2f} 💎.", []

            # Deduct costs
            if coins_cost > 0:
                atomic_deduct_balance(user_id, coins_cost, currency="coins", reason=f"Opened {pack['name']}")
            if gems_cost > 0:
                atomic_deduct_balance(user_id, gems_cost, currency="gems", reason=f"Opened {pack['name']}")

            # Roll cards
            drawn_cards: List[Dict[str, Any]] = []
            rarity_weights = pack["weights"]

            for _ in range(pack["card_count"]):
                # Choose rarity based on weights
                rarities = list(rarity_weights.keys())
                weights = list(rarity_weights.values())
                chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]

                # Filter cards of this rarity
                matching_cards = [c for c in CARDS_CATALOG.values() if c["rarity"] == chosen_rarity]
                if not matching_cards:
                    matching_cards = list(CARDS_CATALOG.values())
                chosen_card = random.choice(matching_cards)
                drawn_cards.append(chosen_card)

                # Persist ownership in database
                self._add_card_to_user(user_id, chosen_card["id"])

            add_xp_with_limits(user_id, 50 * pack["card_count"], reason="pack_opening")
            return True, f"🎉 Opened {pack['emoji']} <b>{pack['name']}</b>!", drawn_cards

    def _add_card_to_user(self, user_id: int, card_id: str) -> None:
        try:
            conn = _get_conn()
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT id, count, level FROM card_ownership WHERE user_id = ? AND card_id = ?", (str(user_id), card_id))
                row = cur.fetchone()
                if row:
                    conn.execute("UPDATE card_ownership SET count = count + 1 WHERE id = ?", (row[0],))
                else:
                    conn.execute(
                        "INSERT INTO card_ownership (user_id, card_id, level, xp, count) VALUES (?, ?, 1, 0, 1)",
                        (str(user_id), card_id)
                    )
        except Exception as e:
            print(f"Error adding card to user {user_id}: {e}")

    def get_user_cards(self, user_id: int) -> List[Dict[str, Any]]:
        results = []
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT co.card_id, co.level, co.count, c.name, c.rarity, c.element, c.attack, c.defense, c.hp, c.speed, c.description
                FROM card_ownership co
                JOIN cards c ON co.card_id = c.card_id
                WHERE co.user_id = ?
                ORDER BY co.level DESC, c.attack DESC
            """, (str(user_id),))
            rows = cur.fetchall()
            for r in rows:
                lvl = r[1]
                # Stat scaling: +10% per level above 1
                scale = 1.0 + (lvl - 1) * 0.10
                results.append({
                    "card_id": r[0],
                    "level": lvl,
                    "count": r[2],
                    "name": r[3],
                    "rarity": r[4],
                    "element": r[5],
                    "attack": int(r[6] * scale),
                    "defense": int(r[7] * scale),
                    "hp": int(r[8] * scale),
                    "speed": r[9],
                    "description": r[10],
                    "rarity_color": CardRarity.COLORS.get(r[4], "⚪"),
                })
        except Exception as e:
            print(f"Error getting user cards: {e}")
        return results

    def upgrade_card(self, user_id: int, card_id: str) -> Tuple[bool, str]:
        with _STORAGE_LOCK:
            try:
                conn = _get_conn()
                cur = conn.cursor()
                cur.execute("SELECT id, level, count FROM card_ownership WHERE user_id = ? AND card_id = ?", (str(user_id), card_id))
                row = cur.fetchone()
                if not row:
                    return False, "You do not own this card!"

                row_id, level, count = row
                upgrade_cost = level * 1000

                ud = get_user(user_id)
                if ud.get("balance", 0) < upgrade_cost:
                    return False, f"Insufficient coins! Upgrade to Level {level+1} costs ${upgrade_cost:,}."

                atomic_deduct_balance(user_id, upgrade_cost, currency="coins", reason=f"Upgraded card {card_id}")
                with conn:
                    conn.execute("UPDATE card_ownership SET level = level + 1 WHERE id = ?", (row_id,))

                card_name = CARDS_CATALOG.get(card_id, {}).get("name", card_id)
                return True, f"⚡ <b>{card_name}</b> successfully upgraded to <b>Level {level+1}</b>! (+10% all battle stats)"
            except Exception as e:
                return False, f"Upgrade failed: {e}"

    def gift_card(self, sender_id: int, receiver_id: int, card_id: str) -> Tuple[bool, str]:
        if sender_id == receiver_id:
            return False, "You cannot gift a card to yourself."

        with _STORAGE_LOCK:
            try:
                conn = _get_conn()
                cur = conn.cursor()
                cur.execute("SELECT id, count, level FROM card_ownership WHERE user_id = ? AND card_id = ?", (str(sender_id), card_id))
                row = cur.fetchone()
                if not row or row[1] < 1:
                    return False, "You do not own this card."

                row_id, count, level = row
                with conn:
                    if count > 1:
                        conn.execute("UPDATE card_ownership SET count = count - 1 WHERE id = ?", (row_id,))
                    else:
                        conn.execute("DELETE FROM card_ownership WHERE id = ?", (row_id,))

                # Credit to receiver
                self._add_card_to_user(receiver_id, card_id)
                card_name = CARDS_CATALOG.get(card_id, {}).get("name", card_id)
                return True, f"🎁 Successfully gifted <b>{card_name}</b> to User <code>{receiver_id}</code>!"
            except Exception as e:
                return False, f"Card gift failed: {e}"

    def simulate_card_duel(self, user_a_id: int, card_a_id: str, user_b_id: int, card_b_id: Optional[str] = None) -> Dict[str, Any]:
        """Simulates turn-based combat between two cards with elemental multipliers."""
        deck_a = self.get_user_cards(user_a_id)
        card_a = next((c for c in deck_a if c["card_id"] == card_a_id), None)
        if not card_a:
            # Fallback to base catalog
            base = CARDS_CATALOG.get(card_a_id)
            if not base:
                return {"error": "Invalid Card A"}
            card_a = {**base, "level": 1, "rarity_color": CardRarity.COLORS.get(base["rarity"], "⚪")}

        if card_b_id:
            deck_b = self.get_user_cards(user_b_id)
            card_b = next((c for c in deck_b if c["card_id"] == card_b_id), None)
            if not card_b:
                base_b = CARDS_CATALOG.get(card_b_id, random.choice(list(CARDS_CATALOG.values())))
                card_b = {**base_b, "level": 1, "rarity_color": CardRarity.COLORS.get(base_b["rarity"], "⚪")}
        else:
            # AI Opponent Card matching user level
            matching = [c for c in CARDS_CATALOG.values() if c["rarity"] == card_a["rarity"]] or list(CARDS_CATALOG.values())
            base_ai = random.choice(matching)
            card_b = {**base_ai, "level": card_a["level"], "rarity_color": CardRarity.COLORS.get(base_ai["rarity"], "⚪")}

        # Combat battle loop
        hp_a = card_a["hp"]
        hp_b = card_b["hp"]
        log: List[str] = []

        # Elemental multiplier check
        mult_a = 1.0
        mult_b = 1.0
        elem_a = card_a.get("element", "")
        elem_b = card_b.get("element", "")

        if "Fire" in elem_a and "Earth" in elem_b: mult_a = 1.3
        elif "Water" in elem_a and "Fire" in elem_b: mult_a = 1.3
        elif "Earth" in elem_a and "Electric" in elem_b: mult_a = 1.3
        elif "Electric" in elem_a and "Water" in elem_b: mult_a = 1.3

        if "Fire" in elem_b and "Earth" in elem_a: mult_b = 1.3
        elif "Water" in elem_b and "Fire" in elem_a: mult_b = 1.3
        elif "Earth" in elem_b and "Electric" in elem_a: mult_b = 1.3
        elif "Electric" in elem_b and "Water" in elem_a: mult_b = 1.3

        rounds = 0
        while hp_a > 0 and hp_b > 0 and rounds < 10:
            rounds += 1
            # A attacks B
            dmg_a = max(5, int((card_a["attack"] * mult_a) - (card_b["defense"] * 0.4)))
            hp_b -= dmg_a
            log.append(f"Turn {rounds}: ⚔️ {card_a['name']} deals {dmg_a} damage to {card_b['name']}! (Remaining HP: {max(0, hp_b)})")
            if hp_b <= 0:
                break

            # B attacks A
            dmg_b = max(5, int((card_b["attack"] * mult_b) - (card_a["defense"] * 0.4)))
            hp_a -= dmg_b
            log.append(f"Turn {rounds}: 🛡️ {card_b['name']} strikes back for {dmg_b} damage! (Remaining HP: {max(0, hp_a)})")

        winner_a = hp_a > 0
        rewards = {"coins": 500, "xp": 40} if winner_a else {"coins": 50, "xp": 10}

        if winner_a:
            atomic_add_balance(user_a_id, rewards["coins"], currency="coins", reason="Won Card Duel")
            add_xp_with_limits(user_a_id, rewards["xp"], reason="card_duel")

        return {
            "winner_a": winner_a,
            "card_a": card_a,
            "card_b": card_b,
            "battle_log": log,
            "rewards": rewards,
        }
