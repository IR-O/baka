from __future__ import annotations

from typing import Dict, Any, List

class CardRarity:
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"
    MYTHIC = "Mythic"
    LIMITED_EDITION = "Limited Edition"

    COLORS = {
        COMMON: "⚪",
        UNCOMMON: "🟢",
        RARE: "🔵",
        EPIC: "🟣",
        LEGENDARY: "🟡",
        MYTHIC: "🔴",
        LIMITED_EDITION: "✨",
    }


CARDS_CATALOG: Dict[str, Dict[str, Any]] = {
    # --- COMMON ---
    "c_goblin_scout": {
        "id": "c_goblin_scout",
        "name": "Goblin Scout",
        "rarity": CardRarity.COMMON,
        "element": "Earth 🌿",
        "attack": 15,
        "defense": 10,
        "hp": 45,
        "speed": 18,
        "description": "Nimble forest scout capable of swift stealth strikes.",
    },
    "c_slime_blob": {
        "id": "c_slime_blob",
        "name": "Azure Slime",
        "rarity": CardRarity.COMMON,
        "element": "Water 💧",
        "attack": 12,
        "defense": 16,
        "hp": 60,
        "speed": 8,
        "description": "Gelatinous creature that absorbs physical damage.",
    },
    "c_skeleton_warrior": {
        "id": "c_skeleton_warrior",
        "name": "Skeleton Sentry",
        "rarity": CardRarity.COMMON,
        "element": "Dark 🌑",
        "attack": 18,
        "defense": 12,
        "hp": 40,
        "speed": 14,
        "description": "Ancient animated bones wielding a rusty scimitar.",
    },
    # --- UNCOMMON ---
    "u_pyro_imp": {
        "id": "u_pyro_imp",
        "name": "Pyro Imp",
        "rarity": CardRarity.UNCOMMON,
        "element": "Fire 🔥",
        "attack": 28,
        "defense": 15,
        "hp": 65,
        "speed": 22,
        "description": "Mischievous fiend casting bursting ember flares.",
    },
    "u_frost_wolf": {
        "id": "u_frost_wolf",
        "name": "Frostfang Wolf",
        "rarity": CardRarity.UNCOMMON,
        "element": "Water 💧",
        "attack": 26,
        "defense": 20,
        "hp": 75,
        "speed": 25,
        "description": "Predator of the tundra with biting chilling jaws.",
    },
    "u_zephyr_hawk": {
        "id": "u_zephyr_hawk",
        "name": "Zephyr Hawk",
        "rarity": CardRarity.UNCOMMON,
        "element": "Wind 🌪️",
        "attack": 24,
        "defense": 16,
        "hp": 60,
        "speed": 32,
        "description": "Raptor that dives from high clouds at hurricane velocity.",
    },
    # --- RARE ---
    "r_shadow_assassin": {
        "id": "r_shadow_assassin",
        "name": "Shadow Blade",
        "rarity": CardRarity.RARE,
        "element": "Dark 🌑",
        "attack": 45,
        "defense": 25,
        "hp": 90,
        "speed": 38,
        "description": "Silent killer cloaked in pure midnight gloom.",
    },
    "r_thunder_knight": {
        "id": "r_thunder_knight",
        "name": "Storm Paladin",
        "rarity": CardRarity.RARE,
        "element": "Electric ⚡",
        "attack": 42,
        "defense": 40,
        "hp": 110,
        "speed": 20,
        "description": "Heavy knight channeling lightning through a runic warhammer.",
    },
    "r_sylvan_druid": {
        "id": "r_sylvan_druid",
        "name": "Sylvan Druid",
        "rarity": CardRarity.RARE,
        "element": "Earth 🌿",
        "attack": 36,
        "defense": 32,
        "hp": 120,
        "speed": 24,
        "description": "Guardian of sacred groves wielding restorative botanical magic.",
    },
    # --- EPIC ---
    "e_inferno_golem": {
        "id": "e_inferno_golem",
        "name": "Magma Titan",
        "rarity": CardRarity.EPIC,
        "element": "Fire 🔥",
        "attack": 65,
        "defense": 60,
        "hp": 180,
        "speed": 15,
        "description": "Towering juggernaut forged inside the molten core of volcanoes.",
    },
    "e_abyssal_leviathan": {
        "id": "e_abyssal_leviathan",
        "name": "Abyssal Leviathan",
        "rarity": CardRarity.EPIC,
        "element": "Water 💧",
        "attack": 68,
        "defense": 55,
        "hp": 190,
        "speed": 28,
        "description": "Deep ocean horror commanding tidal surges and whirlpools.",
    },
    "e_radiant_seraph": {
        "id": "e_radiant_seraph",
        "name": "Radiant Seraph",
        "rarity": CardRarity.EPIC,
        "element": "Light 🌟",
        "attack": 62,
        "defense": 50,
        "hp": 170,
        "speed": 35,
        "description": "Celestial messenger radiating solar brilliance and smiting darkness.",
    },
    # --- LEGENDARY ---
    "l_crimson_dragon": {
        "id": "l_crimson_dragon",
        "name": "Crimson Wyrm King",
        "rarity": CardRarity.LEGENDARY,
        "element": "Fire 🔥",
        "attack": 95,
        "defense": 80,
        "hp": 260,
        "speed": 42,
        "description": "Sovereign dragon whose fiery breath incinerates mountain ranges.",
    },
    "l_void_walker": {
        "id": "l_void_walker",
        "name": "Voidwalker Sovereign",
        "rarity": CardRarity.LEGENDARY,
        "element": "Dark 🌑",
        "attack": 105,
        "defense": 70,
        "hp": 240,
        "speed": 50,
        "description": "Ancient entity traversing the boundary between cosmos and nothingness.",
    },
    # --- MYTHIC ---
    "m_chronos_phoenix": {
        "id": "m_chronos_phoenix",
        "name": "Chronos Phoenix",
        "rarity": CardRarity.MYTHIC,
        "element": "Light 🌟",
        "attack": 130,
        "defense": 100,
        "hp": 320,
        "speed": 60,
        "description": "Eternal bird manipulating temporal reality, rebirthing from cosmic ash.",
    },
    "m_omni_deus": {
        "id": "m_omni_deus",
        "name": "Omni Genesis Deus",
        "rarity": CardRarity.MYTHIC,
        "element": "Cosmic ✨",
        "attack": 145,
        "defense": 115,
        "hp": 350,
        "speed": 55,
        "description": "The primordial architect commanding all universal elemental laws.",
    },
    # --- LIMITED EDITION ---
    "le_miko_cyber_goddess": {
        "id": "le_miko_cyber_goddess",
        "name": "Miko Cyber Goddess",
        "rarity": CardRarity.LIMITED_EDITION,
        "element": "Cyber Divine 💠",
        "attack": 160,
        "defense": 130,
        "hp": 400,
        "speed": 70,
        "description": "Limited Founder's Edition: The supreme cyber deity of the Miko Platform.",
    },
}

PACK_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "bronze": {
        "name": "Bronze Booster Pack",
        "emoji": "🥉",
        "cost_coins": 1500,
        "cost_gems": 0.0,
        "card_count": 3,
        "weights": {
            CardRarity.COMMON: 70,
            CardRarity.UNCOMMON: 25,
            CardRarity.RARE: 5,
        },
    },
    "silver": {
        "name": "Silver Arcane Pack",
        "emoji": "🥈",
        "cost_coins": 4500,
        "cost_gems": 0.0,
        "card_count": 3,
        "weights": {
            CardRarity.UNCOMMON: 60,
            CardRarity.RARE: 30,
            CardRarity.EPIC: 10,
        },
    },
    "gold": {
        "name": "Gold Imperial Pack",
        "emoji": "🥇",
        "cost_coins": 12000,
        "cost_gems": 1.0,
        "card_count": 4,
        "weights": {
            CardRarity.RARE: 50,
            CardRarity.EPIC: 35,
            CardRarity.LEGENDARY: 14,
            CardRarity.MYTHIC: 1,
        },
    },
    "mythic": {
        "name": "Mythic Celestial Pack",
        "emoji": "💎",
        "cost_coins": 30000,
        "cost_gems": 3.0,
        "card_count": 5,
        "weights": {
            CardRarity.EPIC: 40,
            CardRarity.LEGENDARY: 45,
            CardRarity.MYTHIC: 12,
            CardRarity.LIMITED_EDITION: 3,
        },
    },
}
