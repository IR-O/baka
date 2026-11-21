"""
Miko Telegram Gaming Platform - Virtual Pet Catalog
Defines pet species, rarities, evolution paths, and base statistics.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class PetSpecies:
    id: str
    name: str
    rarity: str
    rarity_badge: str
    cost_coins: int
    cost_gems: int
    base_happiness: int
    base_stamina: int
    evolved_name: str
    description: str


PET_SPECIES_CATALOG: Dict[str, PetSpecies] = {
    "fox": PetSpecies(
        id="fox",
        name="Silver Fox",
        rarity="Common",
        rarity_badge="⚪",
        cost_coins=2500,
        cost_gems=0,
        base_happiness=90,
        base_stamina=100,
        evolved_name="Nine-Tails Kitsune 🦊✨",
        description="Agile and cunning woodland creature with keen senses."
    ),
    "wolf": PetSpecies(
        id="wolf",
        name="Timber Wolf",
        rarity="Common",
        rarity_badge="⚪",
        cost_coins=3500,
        cost_gems=0,
        base_happiness=85,
        base_stamina=120,
        evolved_name="Fenrir Alpha Wolf 🐺⚡",
        description="Fierce and loyal protector of the northern wildlands."
    ),
    "owl": PetSpecies(
        id="owl",
        name="Mystic Owl",
        rarity="Uncommon",
        rarity_badge="🟢",
        cost_coins=8000,
        cost_gems=1,
        base_happiness=95,
        base_stamina=110,
        evolved_name="Celestial Archon Owl 🦉🔮",
        description="Observant nocturnal raptor capable of sensing magical auras."
    ),
    "cybercat": PetSpecies(
        id="cybercat",
        name="Cyber Kitten",
        rarity="Rare",
        rarity_badge="🔵",
        cost_coins=18000,
        cost_gems=3,
        base_happiness=100,
        base_stamina=130,
        evolved_name="Quantum Neon Tiger 🐯⚡",
        description="Bio-engineered robotic feline glowing with synthwave neon energy."
    ),
    "phoenix": PetSpecies(
        id="phoenix",
        name="Ember Phoenix",
        rarity="Epic",
        rarity_badge="🟣",
        cost_coins=45000,
        cost_gems=8,
        base_happiness=100,
        base_stamina=150,
        evolved_name="Solar Sovereign Phoenix 🦅🔥",
        description="Legendary avian forged in eternal holy fire, granting luck in games."
    ),
    "dragon": PetSpecies(
        id="dragon",
        name="Astral Wyrmling",
        rarity="Mythic",
        rarity_badge="🟡",
        cost_coins=100000,
        cost_gems=25,
        base_happiness=100,
        base_stamina=200,
        evolved_name="Cataclysmic Void Dragon 🐲🌌",
        description="An ancient cosmic powerhouse ruling celestial astral planes."
    ),
}


def get_pet_species(key: str) -> Optional[PetSpecies]:
    clean = key.strip().lower().replace(" ", "").replace("_", "")
    for k, v in PET_SPECIES_CATALOG.items():
        if k == clean or v.name.lower().replace(" ", "") == clean:
            return v
    return None
