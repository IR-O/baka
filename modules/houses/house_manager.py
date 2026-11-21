"""
Miko Telegram Gaming Platform - Virtual House Manager
Handles personal estates, room expansions, furniture marketplace, comfort score, and visitors.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import (
    get_user,
    atomic_deduct_balance,
    atomic_add_balance,
    add_xp,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn


@dataclass
class HouseTier:
    level: int
    name: str
    base_comfort: int
    rooms_count: int
    upgrade_coins: int
    upgrade_gems: int


HOUSE_TIERS: Dict[int, HouseTier] = {
    1: HouseTier(1, "Cozy Cottage 🏡", 50, 2, 0, 0),
    2: HouseTier(2, "Suburban Modern Villa 🏘️", 120, 3, 20000, 2),
    3: HouseTier(3, "Grand Royal Manor 🏰", 250, 4, 60000, 5),
    4: HouseTier(4, "Celestial Penthouse 🏙️✨", 500, 5, 150000, 15),
    5: HouseTier(5, "Olympus Sovereign Citadel 🏛️👑", 1000, 6, 400000, 40),
}


@dataclass
class FurnitureItem:
    id: str
    name: str
    room: str
    comfort_bonus: int
    cost_coins: int
    cost_gems: int


FURNITURE_CATALOG: Dict[str, FurnitureItem] = {
    "sofa": FurnitureItem("sofa", "Plush Velvet Sofa 🛋️", "Living Room", 15, 3000, 0),
    "gaming_desk": FurnitureItem("gaming_desk", "RGB Neon Gaming Station 🖥️⚡", "Gaming Room", 25, 8000, 0),
    "canopy_bed": FurnitureItem("canopy_bed", "Silk Canopy Bed 🛏️👑", "Master Bedroom", 35, 15000, 1),
    "chandelier": FurnitureItem("chandelier", "Gilded Crystal Chandelier 💎✨", "Living Room", 45, 25000, 2),
    "dragon_trophy": FurnitureItem("dragon_trophy", "Ancient Dragon Trophy Mount 🐲🏆", "Trophy Hall", 65, 50000, 5),
    "arc_reactor": FurnitureItem("arc_reactor", "Holographic Arc Core 🌌🔮", "Gaming Room", 120, 120000, 12),
}


class HouseManager:
    _instance: Optional[HouseManager] = None

    @classmethod
    def get_instance(cls) -> HouseManager:
        if cls._instance is None:
            cls._instance = HouseManager()
        return cls._instance

    def get_or_create_house(self, user_id: int) -> Dict[str, Any]:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, house_type, level, comfort, rooms_count, decor_score, updated_at
                FROM houses WHERE user_id = ?
            """, (str(user_id),))
            row = cur.fetchone()
            if row:
                return {
                    "user_id": int(row[0]),
                    "house_type": row[1],
                    "level": row[2],
                    "comfort": row[3],
                    "rooms_count": row[4],
                    "decor_score": row[5],
                    "updated_at": row[6],
                }

            # Initialize Level 1 Cozy Cottage
            tier1 = HOUSE_TIERS[1]
            with conn:
                conn.execute("""
                    INSERT INTO houses (user_id, house_type, level, comfort, rooms_count, decor_score)
                    VALUES (?, ?, 1, ?, ?, 0)
                """, (str(user_id), tier1.name, tier1.base_comfort, tier1.rooms_count))

            return {
                "user_id": user_id,
                "house_type": tier1.name,
                "level": 1,
                "comfort": tier1.base_comfort,
                "rooms_count": tier1.rooms_count,
                "decor_score": 0,
            }
        except Exception as e:
            print(f"Error fetching house: {e}")
            tier1 = HOUSE_TIERS[1]
            return {
                "user_id": user_id,
                "house_type": tier1.name,
                "level": 1,
                "comfort": tier1.base_comfort,
                "rooms_count": tier1.rooms_count,
                "decor_score": 0,
            }

    def upgrade_house(self, user_id: int) -> Tuple[bool, str]:
        house = self.get_or_create_house(user_id)
        current_lvl = house["level"]
        next_lvl = current_lvl + 1

        if next_lvl not in HOUSE_TIERS:
            return False, "🏛️ Your estate has reached the absolute maximum tier (Olympus Sovereign Citadel)!"

        next_tier = HOUSE_TIERS[next_lvl]
        with _STORAGE_LOCK:
            ud = get_user(user_id)
            if ud.get("balance", 0) < next_tier.upgrade_coins:
                return False, f"Upgrading to <b>{next_tier.name}</b> costs ${next_tier.upgrade_coins:,} coins. You have ${ud.get('balance', 0):,}."
            if next_tier.upgrade_gems > 0 and ud.get("gems", 0) < next_tier.upgrade_gems:
                return False, f"Upgrading requires {next_tier.upgrade_gems} 💎. You have {ud.get('gems', 0)} 💎."

            if not atomic_deduct_balance(user_id, next_tier.upgrade_coins, currency="coins", reason=f"House upgrade to Lv.{next_lvl}"):
                return False, "Coin transaction failed."

            if next_tier.upgrade_gems > 0:
                if not atomic_deduct_balance(user_id, next_tier.upgrade_gems, currency="gems", reason=f"House upgrade to Lv.{next_lvl}"):
                    atomic_add_balance(user_id, next_tier.upgrade_coins, currency="coins", reason="Refund failed upgrade")
                    return False, "Gem transaction failed."

            new_comfort = house["comfort"] + (next_tier.base_comfort - HOUSE_TIERS[current_lvl].base_comfort)
            try:
                conn = _get_conn()
                with conn:
                    conn.execute("""
                        UPDATE houses
                        SET level = ?, house_type = ?, comfort = ?, rooms_count = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (next_lvl, next_tier.name, new_comfort, next_tier.rooms_count, str(user_id)))

                add_xp(user_id, next_lvl * 500)
                return True, (
                    f"🎉 <b>ESTATE UPGRADED!</b>\n\n"
                    f"🏠 Your estate is now a <b>{next_tier.name}</b> (Tier {next_lvl})!\n"
                    f"✨ Total Comfort: <b>{new_comfort}</b> | 🚪 Rooms: <b>{next_tier.rooms_count}</b>\n"
                    f"🎁 Reward: +{next_lvl * 500} XP!"
                )
            except Exception as e:
                return False, f"Database error during upgrade: {e}"

    def buy_furniture(self, user_id: int, item_key: str) -> Tuple[bool, str]:
        clean_key = item_key.strip().lower().replace(" ", "_")
        item = FURNITURE_CATALOG.get(clean_key)
        if not item:
            available = ", ".join([f"<code>{k}</code> ({v.name})" for k, v in FURNITURE_CATALOG.items()])
            return False, f"Unknown furniture item. Available items:\n{available}"

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            if ud.get("balance", 0) < item.cost_coins:
                return False, f"Buying {item.name} costs ${item.cost_coins:,} coins. You have ${ud.get('balance', 0):,}."
            if item.cost_gems > 0 and ud.get("gems", 0) < item.cost_gems:
                return False, f"Buying {item.name} requires {item.cost_gems} 💎. You have {ud.get('gems', 0)} 💎."

            if not atomic_deduct_balance(user_id, item.cost_coins, currency="coins", reason=f"Bought furniture {item.name}"):
                return False, "Coin transaction failed."

            if item.cost_gems > 0:
                if not atomic_deduct_balance(user_id, item.cost_gems, currency="gems", reason=f"Bought furniture {item.name}"):
                    atomic_add_balance(user_id, item.cost_coins, currency="coins", reason="Refund furniture")
                    return False, "Gem transaction failed."

            try:
                conn = _get_conn()
                with conn:
                    conn.execute("""
                        INSERT INTO house_items (user_id, item_name, item_type, comfort_bonus, room, placed)
                        VALUES (?, ?, 'furniture', ?, ?, 1)
                    """, (str(user_id), item.name, item.comfort_bonus, item.room))

                    conn.execute("""
                        UPDATE houses
                        SET comfort = comfort + ?, decor_score = decor_score + ?
                        WHERE user_id = ?
                    """, (item.comfort_bonus, item.comfort_bonus, str(user_id)))

                add_xp(user_id, item.comfort_bonus * 10)
                return True, f"🛋️ You bought and placed <b>{item.name}</b> in your <b>{item.room}</b>!\n✨ Comfort +{item.comfort_bonus} | Decor Score +{item.comfort_bonus}."
            except Exception as e:
                return False, f"Database error: {e}"

    def get_house_items(self, user_id: int) -> List[Dict[str, Any]]:
        items = []
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, item_name, comfort_bonus, room, placed, acquired_at
                FROM house_items WHERE user_id = ? ORDER BY id DESC
            """, (str(user_id),))
            rows = cur.fetchall()
            for r in rows:
                items.append({
                    "id": r[0],
                    "item_name": r[1],
                    "comfort_bonus": r[2],
                    "room": r[3],
                    "placed": bool(r[4]),
                    "acquired_at": r[5],
                })
        except Exception as e:
            print(f"Error fetching house items: {e}")
        return items

    def get_top_houses(self, limit: int = 10) -> List[Dict[str, Any]]:
        houses = []
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, house_type, level, comfort, decor_score
                FROM houses ORDER BY comfort DESC, decor_score DESC LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            for idx, r in enumerate(rows, 1):
                uid = int(r[0])
                ud = get_user(uid)
                houses.append({
                    "rank": idx,
                    "user_id": uid,
                    "owner_name": ud.get("display_name") or ud.get("username", "Estate Owner"),
                    "house_type": r[1],
                    "level": r[2],
                    "comfort": r[3],
                    "decor_score": r[4],
                })
        except Exception as e:
            print(f"Error fetching top houses: {e}")
        return houses
