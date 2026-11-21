"""
Miko Telegram Gaming Platform - AI Gaming Copilot & Assistant
Provides game rules explanations, contextual recommendations, command help,
and security guardrails ensuring AI cannot modify database state or economy.
"""

from __future__ import annotations

import re
import html
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import get_user


GAME_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "poker": {
        "title": "🃏 Texas Hold'em Poker (/poker)",
        "rules": "Two players are dealt hole cards and contest communal flop, turn, and river cards. Standard 5-card poker rankings apply (High Card < Pair < Two Pair < Three of a Kind < Straight < Flush < Full House < Four of a Kind < Straight Flush < Royal Flush).",
        "tip": "Bet aggressively with strong pocket pairs; fold marginal kickers on coordinated boards."
    },
    "roulette": {
        "title": "🎰 European Roulette (/roulette)",
        "rules": "Place bets on Red/Black, Even/Odd (1:1 payout), dozens (2:1 payout), or exact numbers (35:1 payout). A spinning wheel determines the winning number (0-36).",
        "tip": "Outside bets (Red/Black) carry the highest win probability (48.6%)."
    },
    "bluff": {
        "title": "🎭 Bluff / Liar's Dice (/bluff)",
        "rules": "Bid escalating card ranks in sequence. Players can challenge a previous bid as a bluff. If challenged and the bidder was bluffing, the challenger wins the pot!",
        "tip": "Mix honest plays with calculated bluffs to keep opponents guessing."
    },
    "cards": {
        "title": "⚔️ Collectible Card Duels (/cardduel)",
        "rules": "Summon fantasy cards from your deck. Cards feature elemental affinities (Fire > Earth > Air > Water > Fire) and level stats. Element advantages deal 35% bonus damage!",
        "tip": "Upgrade your cards using duplicates and coins to gain extra HP and Attack."
    },
    "dungeon": {
        "title": "🗡️ Turn-Based Dungeon RPG (/dungeon, /explore, /attack)",
        "rules": "Descend into dark catacombs, defeat monsters and elite bosses, loot epic weapons and armor, and drink health potions to survive.",
        "tip": "Equip high-rarity armor from drops to boost your defense before fighting bosses."
    },
    "pets": {
        "title": "🐾 Virtual Pets & Tournaments (/pets, /trainpet, /petbattle)",
        "rules": "Adopt animal companions, feed and train them to raise happiness and stamina, and enter pet tournaments for coin and gem prizes.",
        "tip": "Reach Level 10 to evolve your pet into its ultimate divine celestial form!"
    },
    "wordquiz": {
        "title": "🔤 Word Quiz & Word Grid (/quiz, /wordgrid)",
        "rules": "Solve unscrambles, find hidden words on a 4x4 letter grid, or answer trivia before other players in group chat.",
        "tip": "Speed is key! Answers must be typed directly into chat as plain text."
    },
}


class AIGamingCopilot:
    _instance: Optional[AIGamingCopilot] = None

    @classmethod
    def get_instance(cls) -> AIGamingCopilot:
        if cls._instance is None:
            cls._instance = AIGamingCopilot()
        return cls._instance

    def explain_game(self, game_key: str) -> Optional[str]:
        clean = game_key.strip().lower().replace("/", "")
        for k, info in GAME_EXPLANATIONS.items():
            if k in clean or clean in k:
                return (
                    f"🎮 <b>GAME GUIDE: {info['title']}</b>\n\n"
                    f"📜 <b>Rules:</b>\n{info['rules']}\n\n"
                    f"💡 <b>Pro Strategy Tip:</b>\n<i>{info['tip']}</i>"
                )
        return None

    def recommend_games(self, user_id: int) -> str:
        ud = get_user(user_id)
        balance = ud.get("balance", 0)
        level = ud.get("level", 1)

        recommendations = []
        if balance < 2000:
            recommendations.append("• 🔤 <b>Word Quiz & Word Grid</b> — Zero entry cost, high coin payouts!")
            recommendations.append("• 🎁 <b>Daily Streak & Missions</b> (<code>/daily</code>, <code>/missions</code>) — Free funds to build your bankroll.")
        elif balance < 50000:
            recommendations.append("• 🃏 <b>Texas Hold'em Poker</b> (<code>/poker</code>) — Strategic skill rewards.")
            recommendations.append("• 🗡️ <b>Dungeon RPG</b> (<code>/dungeon</code>) — Battle monsters for loot and XP.")
            recommendations.append("• 🐾 <b>Adopt a Pet</b> (<code>/adoptpet fox</code>) — Train a loyal companion.")
        else:
            recommendations.append("• 🎰 <b>High-Stakes Roulette</b> (<code>/roulette</code>) — Bet big on outside chances.")
            recommendations.append("• 🌟 <b>Mythic Card Packs</b> (<code>/openpack mythic</code>) — Hunt for S-tier cards.")
            recommendations.append("• 🏰 <b>Found a Guild</b> (<code>/createguild</code>) — Lead a clan to glory.")

        p_name = ud.get("display_name") or ud.get("username") or "Player"
        return (
            f"🤖 <b>AI COPILOT RECOMMENDATION FOR {html.escape(str(p_name))}</b>\n"
            f"💼 Bankroll: <b>${balance:,} coins</b> | Level: <b>{level}</b>\n\n"
            "✨ <b>Recommended Modes For You:</b>\n" + "\n".join(recommendations)
        )

    def guardrail_check(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Enforces strict security rules: Prevents prompt injection, balance modification,
        or privileged admin execution via AI.
        """
        lower = prompt.lower()
        forbidden_patterns = [
            r"\b(give|add|set|grant|transfer|steal|hack|mod)\b.*?\b(coins?|balance|gems?|money|stars?|admin|sudo)\b",
            r"\b(drop table|select \*|insert into|delete from|update users)\b",
            r"\b(ignore all previous instructions|bypass security|system prompt override)\b",
        ]

        for pat in forbidden_patterns:
            if re.search(pat, lower):
                return False, "🛡️ <b>Security Guardrail:</b> The AI Copilot cannot modify player balances, execute database commands, or alter system permissions."

        return True, None
