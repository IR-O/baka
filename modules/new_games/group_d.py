"""
Miko Telegram Gaming Platform - Games Group D
Implements:
16. Battleship (battleship)
17. Quiz Tournament (quiztourney)
18. Multiplayer Word Battle (wordbattle)
19. Reaction Challenge (reaction)
20. Daily Puzzle Challenge (dailypuzzle)
+ Complete Interactive Ludo Dice Race (ludo)
"""

from __future__ import annotations

import random
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple

from modules.core.game_engine import BaseGame


# ==============================================================================
# 16. BATTLESHIP
# ==============================================================================
class BattleshipGame(BaseGame):
    GRID_SIZE = 5
    FLEET_SIZE = 3

    def __init__(self):
        super().__init__("battleship", "Battleship Radar 🚢🌊", min_players=1, max_players=2, default_stake=1000)

    def start_battleship_session(self) -> Dict[str, Any]:
        all_cells = [(r, c) for r in range(self.GRID_SIZE) for c in range(self.GRID_SIZE)]
        ships = set(random.sample(all_cells, self.FLEET_SIZE))
        grid = [["🌊" for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]
        return {
            "ships": ships,
            "hits": set(),
            "misses": set(),
            "grid": grid,
            "shots": 0,
            "max_shots": 10,
        }

    def fire_shell(self, state: Dict[str, Any], r: int, c: int) -> Tuple[bool, str, bool]:
        if r < 1 or r > self.GRID_SIZE or c < 1 or c > self.GRID_SIZE:
            return False, f"Coordinates must be between 1 and {self.GRID_SIZE}.", False

        r_idx, c_idx = r - 1, c - 1
        pos = (r_idx, c_idx)

        if pos in state["hits"] or pos in state["misses"]:
            return False, f"You already fired at Row {r}, Col {c}!", False

        state["shots"] += 1
        if pos in state["ships"]:
            state["hits"].add(pos)
            state["grid"][r_idx][c_idx] = "💥"
            all_sunk = (len(state["hits"]) == len(state["ships"]))
            return True, f"🔥 <b>DIRECT HIT!</b> Sunk enemy warship at ({r}, {c})!", all_sunk
        else:
            state["misses"].add(pos)
            state["grid"][r_idx][c_idx] = "⭕"
            out_of_ammo = (state["shots"] >= state["max_shots"])
            return False, f"🌊 <i>Splash!</i> Missed at ({r}, {c}). Ammo left: {state['max_shots'] - state['shots']}", out_of_ammo

    def render_radar(self, state: Dict[str, Any]) -> str:
        lines = ["   1  2  3  4  5"]
        for r in range(self.GRID_SIZE):
            lines.append(f"{r+1} " + " ".join(state["grid"][r]))
        return "\n".join(lines)


# ==============================================================================
# 17. QUIZ TOURNAMENT
# ==============================================================================
class QuizTournamentGame(BaseGame):
    def __init__(self):
        super().__init__("quiztourney", "Grand Quiz Tournament 🏆👑", min_players=1, max_players=4, default_stake=1500)

    def calculate_tournament_payout(self, streak: int, base_stake: int) -> int:
        multiplier = 1.0 + (streak * 0.75)
        return int(base_stake * multiplier)


# ==============================================================================
# 18. MULTIPLAYER WORD BATTLE
# ==============================================================================
class MultiplayerWordBattleGame(BaseGame):
    ROOT_WORDS = ["TELEGRAM", "ASTRONOMY", "CREATIVITY", "PLATFORM", "ADVENTURE", "CHAMPION"]

    def __init__(self):
        super().__init__("wordbattle", "Word Battle Clash ⚔️🔤", min_players=1, max_players=4, default_stake=1000)

    def start_battle(self) -> Dict[str, Any]:
        root = random.choice(self.ROOT_WORDS)
        return {
            "root_word": root,
            "accepted_words": set(),
            "scores": {},
        }

    def submit_subword(self, state: Dict[str, Any], user_id: int, word: str) -> Tuple[bool, str, int]:
        clean = word.upper().strip()
        if len(clean) < 3:
            return False, "Word must be at least 3 letters long.", 0

        if clean in state["accepted_words"]:
            return False, f"Word '{clean}' was already claimed by another player!", 0

        # Verify anagram containment
        root_counts = {}
        for c in state["root_word"]:
            root_counts[c] = root_counts.get(c, 0) + 1

        for c in clean:
            if c not in root_counts or root_counts[c] <= 0:
                return False, f"Letter '{c}' cannot be formed from {state['root_word']}.", 0
            root_counts[c] -= 1

        state["accepted_words"].add(clean)
        pts = len(clean) * 10
        state["scores"][user_id] = state["scores"].get(user_id, 0) + pts
        return True, f"✅ Valid word <b>{clean}</b>! (+{pts} points)", pts


# ==============================================================================
# 19. REACTION CHALLENGE
# ==============================================================================
class ReactionChallengeGame(BaseGame):
    def __init__(self):
        super().__init__("reaction", "Reflex Speed Challenge ⚡⏱️", min_players=1, max_players=2, default_stake=500)

    def evaluate_reaction_speed(self, delay_ms: float) -> Tuple[str, int]:
        if delay_ms < 180:
            return "⚡ Superhuman Cyber Reflexes! (Rank S)", 300
        elif delay_ms < 300:
            return "🏎️ Lightning Fast Reflexes! (Rank A)", 200
        elif delay_ms < 500:
            return "🏃 Great Reaction Time! (Rank B)", 100
        else:
            return "🐢 Room for improvement! (Rank C)", 50


# ==============================================================================
# 20. DAILY PUZZLE CHALLENGE
# ==============================================================================
class DailyPuzzleChallenge(BaseGame):
    PUZZLES_DAILY = [
        {"riddle": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "ans": "ECHO"},
        {"riddle": "The more of this there is, the less you see. What is it?", "ans": "DARKNESS"},
        {"riddle": "What has keys, but no locks; space, but no room; and you can enter, but never go in?", "ans": "KEYBOARD"},
        {"riddle": "What has hands, but cannot clap?", "ans": "CLOCK"},
        {"riddle": "What can travel all around the world while remaining stuck in a corner?", "ans": "STAMP"},
        {"riddle": "What gets wetter the more it dries?", "ans": "TOWEL"},
        {"riddle": "What has a head and a tail that will never meet?", "ans": "COIN"},
    ]

    def __init__(self):
        super().__init__("dailypuzzle", "Daily Conundrum Challenge 🧩📅", min_players=1, max_players=1, default_stake=0)

    def get_todays_puzzle(self) -> Dict[str, str]:
        today_str = time.strftime("%Y-%m-%d", time.gmtime())
        idx = int(hashlib.md5(today_str.encode()).hexdigest(), 16) % len(self.PUZZLES_DAILY)
        return self.PUZZLES_DAILY[idx]

    def check_solution(self, guess: str) -> bool:
        todays = self.get_todays_puzzle()
        clean_g = guess.strip().upper().replace("A ", "").replace("AN ", "").replace("THE ", "")
        return clean_g == todays["ans"] or todays["ans"] in clean_g


# ==============================================================================
# 21. COMPLETE INTERACTIVE LUDO DICE RACE
# ==============================================================================
class LudoDiceRaceGame(BaseGame):
    """
    Complete interactive Ludo Dice Race.
    Tokens advance from Base (0) around a 52-tile track to Home (52).
    Rolling a 6 grants bonus moves and releases tokens from Base yard.
    """
    TRACK_LEN = 52

    def __init__(self):
        super().__init__("ludo", "Ludo Dice Circuit 🎲🏁", min_players=1, max_players=4, default_stake=1000)

    def start_ludo_session(self, player_ids: List[int]) -> Dict[str, Any]:
        player_colors = ["🔴 Red", "🟢 Green", "🟡 Yellow", "🔵 Blue"]
        players_data = {}
        for idx, pid in enumerate(player_ids[:4]):
            players_data[pid] = {
                "color": player_colors[idx],
                "tokens": [0, 0],  # 2 tokens per player for snappy, fun chat gameplay
                "home_tokens": 0,
            }
        return {
            "players": players_data,
            "turn_order": player_ids[:4],
            "turn_idx": 0,
            "last_roll": None,
            "log": [],
        }

    def roll_dice(self) -> int:
        return random.randint(1, 6)

    def advance_player(self, state: Dict[str, Any], player_id: int) -> Tuple[int, str, bool]:
        pdata = state["players"][player_id]
        roll = self.roll_dice()
        state["last_roll"] = roll

        # Advance lowest token
        token_idx = 0 if pdata["tokens"][0] <= pdata["tokens"][1] else 1
        curr_pos = pdata["tokens"][token_idx]

        if curr_pos == 0:
            if roll == 6:
                pdata["tokens"][token_idx] = 1
                msg = f"🎲 Rolled a <b>6</b>! Released a token from the yard onto the circuit!"
            else:
                msg = f"🎲 Rolled a <b>{roll}</b>. (Need a 6 to exit the yard)"
        else:
            new_pos = curr_pos + roll
            if new_pos >= self.TRACK_LEN:
                pdata["tokens"][token_idx] = self.TRACK_LEN
                pdata["home_tokens"] += 1
                msg = f"🎲 Rolled a <b>{roll}</b>! 🏁 <b>TOKEN REACHED HOME BASE!</b>"
            else:
                pdata["tokens"][token_idx] = new_pos
                msg = f"🎲 Rolled a <b>{roll}</b>! Advanced token to Track #{new_pos}."

        is_winner = (pdata["home_tokens"] >= 2)
        state["log"].append(f"{pdata['color']}: {msg}")
        return roll, msg, is_winner
