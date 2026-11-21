from __future__ import annotations

from typing import Dict, Any, List

DUNGEON_LOCATIONS: Dict[str, Dict[str, Any]] = {
    "catacombs": {
        "id": "catacombs",
        "name": "Whispering Catacombs",
        "emoji": "🌲",
        "min_level": 1,
        "max_floors": 5,
        "difficulty": "Easy",
        "boss": {
            "name": "Goblin King Gorthok",
            "emoji": "👑👹",
            "hp": 220,
            "attack": 25,
            "defense": 15,
            "speed": 14,
            "coin_reward": 3000,
            "gem_reward": 0.2,
            "xp_reward": 250,
            "drop": "Steel Broadsword",
        },
        "monsters": [
            {"name": "Dungeon Bat", "hp": 40, "attack": 12, "defense": 6, "speed": 18, "xp": 25, "coins": 80},
            {"name": "Tomb Skeleton", "hp": 65, "attack": 18, "defense": 10, "speed": 12, "xp": 45, "coins": 140},
            {"name": "Cavern Spider", "hp": 55, "attack": 20, "defense": 8, "speed": 16, "xp": 40, "coins": 120},
        ],
    },
    "caverns": {
        "id": "caverns",
        "name": "Molten Caverns",
        "emoji": "🌋",
        "min_level": 10,
        "max_floors": 7,
        "difficulty": "Normal",
        "boss": {
            "name": "Magma Colossus Ignis",
            "emoji": "🔥🗿",
            "hp": 550,
            "attack": 55,
            "defense": 40,
            "speed": 10,
            "coin_reward": 8000,
            "gem_reward": 0.6,
            "xp_reward": 600,
            "drop": "Mithril Hauberk",
        },
        "monsters": [
            {"name": "Fire Salamander", "hp": 110, "attack": 34, "defense": 22, "speed": 22, "xp": 80, "coins": 250},
            {"name": "Lava Slime", "hp": 140, "attack": 28, "defense": 30, "speed": 10, "xp": 75, "coins": 220},
            {"name": "Obsidian Hound", "hp": 125, "attack": 42, "defense": 20, "speed": 26, "xp": 95, "coins": 300},
        ],
    },
    "spire": {
        "id": "spire",
        "name": "Frozen Spire",
        "emoji": "❄️",
        "min_level": 25,
        "max_floors": 10,
        "difficulty": "Hard",
        "boss": {
            "name": "Frost Wraith Queen Yvraine",
            "emoji": "❄️👑",
            "hp": 1200,
            "attack": 90,
            "defense": 65,
            "speed": 35,
            "coin_reward": 20000,
            "gem_reward": 1.5,
            "xp_reward": 1500,
            "drop": "Dragon Slayer Blade",
        },
        "monsters": [
            {"name": "Glacier Golem", "hp": 260, "attack": 60, "defense": 50, "speed": 12, "xp": 180, "coins": 600},
            {"name": "Blizzard Harpy", "hp": 200, "attack": 72, "defense": 35, "speed": 38, "xp": 210, "coins": 750},
            {"name": "Ice Revenant", "hp": 240, "attack": 68, "defense": 45, "speed": 24, "xp": 200, "coins": 700},
        ],
    },
    "void": {
        "id": "void",
        "name": "Abyssal Void Vault",
        "emoji": "🌑",
        "min_level": 50,
        "max_floors": 15,
        "difficulty": "Expert",
        "boss": {
            "name": "Void Dragon Malakor",
            "emoji": "🐉🌌",
            "hp": 3000,
            "attack": 160,
            "defense": 120,
            "speed": 45,
            "coin_reward": 60000,
            "gem_reward": 5.0,
            "xp_reward": 5000,
            "drop": "Celestial Edge",
        },
        "monsters": [
            {"name": "Void Walker", "hp": 450, "attack": 110, "defense": 70, "speed": 40, "xp": 450, "coins": 1800},
            {"name": "Cosmic Behemoth", "hp": 650, "attack": 125, "defense": 95, "speed": 20, "xp": 550, "coins": 2200},
            {"name": "Abyssal Sorcerer", "hp": 400, "attack": 140, "defense": 60, "speed": 45, "xp": 500, "coins": 2000},
        ],
    },
}

WEAPONS_CATALOG: Dict[str, Dict[str, Any]] = {
    "Wooden Sword": {"atk": 10, "spd": 2, "cost": 0},
    "Steel Broadsword": {"atk": 28, "spd": 5, "cost": 3500},
    "Storm Pike": {"atk": 48, "spd": 8, "cost": 9000},
    "Mithril Hauberk Blade": {"atk": 65, "spd": 10, "cost": 18000},
    "Dragon Slayer Blade": {"atk": 95, "spd": 14, "cost": 40000},
    "Celestial Edge": {"atk": 150, "spd": 20, "cost": 100000},
}

ARMOR_CATALOG: Dict[str, Dict[str, Any]] = {
    "Leather Tunic": {"def": 8, "hp": 25, "cost": 0},
    "Iron Plate": {"def": 22, "hp": 60, "cost": 3000},
    "Mithril Hauberk": {"def": 42, "hp": 120, "cost": 12000},
    "Dragon Scale Aegis": {"def": 75, "hp": 220, "cost": 35000},
    "Divine Robes": {"def": 120, "hp": 400, "cost": 90000},
}
