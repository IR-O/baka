"""
Miko Telegram Gaming Platform - Achievement Catalog
Defines 10 categories of achievements with hidden, rare, and tiered rewards.
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class AchievementDef:
    id: str
    category: str
    title: str
    description: str
    reward_coins: int
    reward_gems: float
    reward_xp: int
    max_progress: int
    is_hidden: bool = False


ACHIEVEMENT_CATALOG: List[AchievementDef] = [
    # 1. Gaming
    AchievementDef("game_first", "Gaming", "🎲 Rookie Roller", "Play your first mini-game", 1000, 0, 100, 1),
    AchievementDef("game_win_10", "Gaming", "🏆 Competitive Edge", "Win 10 mini-games", 10000, 2.0, 500, 10),
    AchievementDef("game_win_50", "Gaming", "👑 Gaming Deity", "Win 50 mini-games", 50000, 10.0, 2500, 50),

    # 2. Economy
    AchievementDef("eco_10k", "Economy", "💰 First Fortune", "Accumulate $10,000 in your wallet", 2000, 0, 150, 1),
    AchievementDef("eco_500k", "Economy", "🏦 Half-Millionaire", "Accumulate $500,000 in your wallet", 25000, 5.0, 1500, 1),
    AchievementDef("eco_gems_50", "Economy", "💎 Gem Baron", "Own at least 50 Gems", 50000, 15.0, 3000, 1),

    # 3. Social
    AchievementDef("soc_friend_1", "Social", "🤝 Handshake", "Make your first registered friend", 2500, 1.0, 200, 1),
    AchievementDef("soc_friend_5", "Social", "🌐 Social Butterfly", "Add 5 friends to your social circle", 10000, 3.0, 800, 5),

    # 4. Collection
    AchievementDef("col_cards_5", "Collection", "🃏 Deck Novice", "Collect 5 collectible trading cards", 5000, 1.0, 300, 5),
    AchievementDef("col_mythic", "Collection", "🌟 Chosen of Destiny", "Obtain a Mythic or Limited Edition card", 50000, 12.0, 2500, 1),

    # 5. Dungeon
    AchievementDef("dun_floor_3", "Dungeon", "🗡️ Delver", "Conquer 3 dungeon floors", 8000, 2.0, 600, 3),
    AchievementDef("dun_boss_slayer", "Dungeon", "☠️ Boss Nemesis", "Vanquish a ferocious Dungeon Boss", 25000, 5.0, 2000, 1),

    # 6. Guild
    AchievementDef("gld_member", "Guild", "🛡️ Banner Oath", "Found or join a Clan/Guild", 5000, 1.0, 400, 1),
    AchievementDef("gld_donate_50k", "Guild", "🏛️ Benefactor", "Donate $50,000 to guild treasury", 20000, 4.0, 1200, 50000),

    # 7. Pet
    AchievementDef("pet_adopt_1", "Pet", "🐾 Companion Bond", "Adopt your first virtual companion", 3000, 0, 250, 1),
    AchievementDef("pet_evolve_1", "Pet", "✨ Divine Awakening", "Evolve a pet to its ultimate form", 35000, 8.0, 2000, 1),

    # 8. House
    AchievementDef("hse_villa", "House", "🏡 Villa Aristocrat", "Upgrade house to Modern Villa (Tier 2)", 12000, 2.0, 750, 1),
    AchievementDef("hse_citadel", "House", "🏛️ Celestial Architect", "Reach Olympus Sovereign Citadel (Tier 5)", 100000, 25.0, 5000, 1),

    # 9. Daily Activity
    AchievementDef("dly_streak_7", "Daily Activity", "🔥 Unbroken Flame", "Maintain a 7-day daily login streak", 15000, 3.0, 1000, 7),

    # 10. Special Events
    AchievementDef("evt_festival", "Special Events", "🎉 Carnival Sovereign", "Participate in a limited-time festival", 10000, 2.0, 800, 1),

    # Hidden
    AchievementDef("hid_jackpot", "Gaming", "🍀 Golden Miracle", "Hit a 10x multiplier jackpot", 30000, 10.0, 1500, 1, is_hidden=True),
]
