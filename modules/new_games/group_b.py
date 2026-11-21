"""
Miko Telegram Gaming Platform - Games Group B
Implements:
6. Memory Match (memory)
7. Sudoku (sudoku)
8. Minesweeper-style Puzzle (minesweeper)
9. Blackjack (blackjack)
10. Higher or Lower (higherlower)
"""

from __future__ import annotations

import random
from typing import Dict, Any, List, Optional, Tuple

from modules.core.game_engine import BaseGame


# ==============================================================================
# 6. MEMORY MATCH
# ==============================================================================
class MemoryMatchGame(BaseGame):
    EMOJIS = ["🦁", "🐯", "🐼", "🦊", "🐸", "🐙", "🦄", "🐲"]

    def __init__(self):
        super().__init__("memory", "Memory Match 🃏🧠", min_players=1, max_players=1, default_stake=1000)

    def start_memory_session(self) -> Dict[str, Any]:
        chosen = self.EMOJIS[:6]
        deck = chosen * 2
        random.shuffle(deck)
        return {
            "deck": deck,
            "revealed": [False] * len(deck),
            "matched": [False] * len(deck),
            "moves": 0,
            "pairs_left": len(chosen),
        }

    def flip_tiles(self, state: Dict[str, Any], idx1: int, idx2: int) -> Tuple[bool, str, bool]:
        if idx1 == idx2 or idx1 >= len(state["deck"]) or idx2 >= len(state["deck"]):
            return False, "Invalid tile selection.", False

        if state["matched"][idx1] or state["matched"][idx2]:
            return False, "Those tiles are already matched!", False

        state["moves"] += 1
        t1 = state["deck"][idx1]
        t2 = state["deck"][idx2]

        if t1 == t2:
            state["matched"][idx1] = True
            state["matched"][idx2] = True
            state["pairs_left"] -= 1
            is_win = (state["pairs_left"] == 0)
            return True, f"🎉 <b>Match Found!</b> {t1} == {t2}", is_win
        else:
            return False, f"❌ No match: {t1} vs {t2}", False


# ==============================================================================
# 7. SUDOKU MINI
# ==============================================================================
class SudokuGame(BaseGame):
    PUZZLES_4X4 = [
        {
            "grid": [
                [1, 0, 3, 0],
                [0, 0, 0, 2],
                [0, 1, 0, 0],
                [0, 3, 0, 4]
            ],
            "solution": [
                [1, 2, 3, 4],
                [3, 4, 1, 2],
                [4, 1, 2, 3],
                [2, 3, 4, 1]
            ]
        },
        {
            "grid": [
                [0, 3, 4, 0],
                [4, 0, 0, 2],
                [1, 0, 0, 4],
                [0, 4, 2, 0]
            ],
            "solution": [
                [2, 3, 4, 1],
                [4, 1, 3, 2],
                [1, 2, 0, 4],
                [3, 4, 2, 1]
            ]
        }
    ]

    def __init__(self):
        super().__init__("sudoku", "Sudoku Mini 🔢", min_players=1, max_players=1, default_stake=500)

    def start_sudoku_session(self) -> Dict[str, Any]:
        p = random.choice(self.PUZZLES_4X4)
        import copy
        return {
            "current": copy.deepcopy(p["grid"]),
            "initial": copy.deepcopy(p["grid"]),
            "solution": p["solution"],
        }

    def place_number(self, state: Dict[str, Any], r: int, c: int, val: int) -> Tuple[bool, str, bool]:
        if r < 1 or r > 4 or c < 1 or c > 4 or val < 1 or val > 4:
            return False, "Row, Col, and Value must be between 1 and 4.", False

        r_idx, c_idx = r - 1, c - 1
        if state["initial"][r_idx][c_idx] != 0:
            return False, "Cannot overwrite initial clue numbers!", False

        state["current"][r_idx][c_idx] = val
        # Check if complete
        is_solved = all(
            state["current"][i][j] == state["solution"][i][j]
            for i in range(4) for j in range(4)
        )
        return True, f"Placed {val} at Row {r}, Col {c}.", is_solved

    def render_grid(self, grid: List[List[int]]) -> str:
        lines = ["┌───┬───┐"]
        for i, row in enumerate(grid):
            nums = [str(x) if x != 0 else "·" for x in row]
            lines.append(f"│ {' '.join(nums[:2])} │ {' '.join(nums[2:])} │")
            if i == 1:
                lines.append("├───┼───┤")
        lines.append("└───┴───┘")
        return "\n".join(lines)


# ==============================================================================
# 8. MINESWEEPER
# ==============================================================================
class MinesweeperGame(BaseGame):
    SIZE = 5
    MINES = 4

    def __init__(self):
        super().__init__("minesweeper", "Minesweeper 💣", min_players=1, max_players=1, default_stake=1000)

    def start_minesweeper_session(self) -> Dict[str, Any]:
        all_cells = [(r, c) for r in range(self.SIZE) for c in range(self.SIZE)]
        mine_cells = set(random.sample(all_cells, self.MINES))

        # Build count grid
        counts = [[0 for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if (r, c) in mine_cells:
                    counts[r][c] = -1
                else:
                    adj = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if (dr != 0 or dc != 0) and (r + dr, c + dc) in mine_cells:
                                adj += 1
                    counts[r][c] = adj

        return {
            "counts": counts,
            "mine_cells": mine_cells,
            "revealed": [[False for _ in range(self.SIZE)] for _ in range(self.SIZE)],
            "safe_remaining": (self.SIZE * self.SIZE) - self.MINES,
        }

    def reveal(self, state: Dict[str, Any], r: int, c: int) -> Tuple[bool, str, bool]:
        if r < 0 or r >= self.SIZE or c < 0 or c >= self.SIZE:
            return False, "Coordinates out of bounds.", False

        if state["revealed"][r][c]:
            return False, "Cell already revealed.", False

        state["revealed"][r][c] = True

        if (r, c) in state["mine_cells"]:
            return False, "💥 <b>BOOM!</b> You uncovered a naval mine!", True  # Game over (lost)

        state["safe_remaining"] -= 1
        num = state["counts"][r][c]
        won = (state["safe_remaining"] == 0)
        return True, f"Safe! Adjacent mines: <b>{num}</b>", won

    def render_board(self, state: Dict[str, Any], show_mines: bool = False) -> str:
        icons = {0: "🟦", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", -1: "💣"}
        lines = ["   1  2  3  4  5"]
        for r in range(self.SIZE):
            row_symbols = []
            for c in range(self.SIZE):
                if state["revealed"][r][c] or (show_mines and (r, c) in state["mine_cells"]):
                    val = state["counts"][r][c]
                    row_symbols.append(icons.get(val, "·"))
                else:
                    row_symbols.append("🟫")
            lines.append(f"{r+1} " + "".join(row_symbols))
        return "\n".join(lines)


# ==============================================================================
# 9. BLACKJACK
# ==============================================================================
class BlackjackGame(BaseGame):
    SUITS = ["♠️", "♥️", "♦️", "♣️"]
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self):
        super().__init__("blackjack", "Blackjack 21 ♠️♦️", min_players=1, max_players=1, default_stake=1000)

    def draw_card(self) -> Dict[str, Any]:
        rank = random.choice(self.RANKS)
        suit = random.choice(self.SUITS)
        if rank in ["J", "Q", "K"]:
            val = 10
        elif rank == "A":
            val = 11
        else:
            val = int(rank)
        return {"rank": rank, "suit": suit, "val": val, "name": f"{rank}{suit}"}

    def hand_value(self, hand: List[Dict[str, Any]]) -> int:
        total = sum(c["val"] for c in hand)
        aces = sum(1 for c in hand if c["rank"] == "A")
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def start_blackjack(self) -> Dict[str, Any]:
        p_hand = [self.draw_card(), self.draw_card()]
        d_hand = [self.draw_card(), self.draw_card()]
        return {
            "player_hand": p_hand,
            "dealer_hand": d_hand,
            "player_val": self.hand_value(p_hand),
            "dealer_val": self.hand_value(d_hand),
            "state": "PLAYING",
        }

    def hit(self, game_state: Dict[str, Any]) -> Tuple[int, bool]:
        game_state["player_hand"].append(self.draw_card())
        val = self.hand_value(game_state["player_hand"])
        game_state["player_val"] = val
        busted = (val > 21)
        if busted:
            game_state["state"] = "BUST"
        return val, busted

    def stand(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        d_hand = game_state["dealer_hand"]
        while self.hand_value(d_hand) < 17:
            d_hand.append(self.draw_card())

        d_val = self.hand_value(d_hand)
        p_val = game_state["player_val"]

        if d_val > 21 or p_val > d_val:
            result = "WIN"
        elif p_val == d_val:
            result = "PUSH"
        else:
            result = "LOSE"

        game_state["dealer_val"] = d_val
        game_state["state"] = result
        return game_state


# ==============================================================================
# 10. HIGHER OR LOWER
# ==============================================================================
class HigherLowerGame(BaseGame):
    def __init__(self):
        super().__init__("higherlower", "Higher or Lower ⬆️⬇️", min_players=1, max_players=1, default_stake=1000)

    def draw_card_val(self) -> Tuple[int, str]:
        val = random.randint(2, 14)
        names = {11: "J", 12: "Q", 13: "K", 14: "A"}
        name = names.get(val, str(val))
        suit = random.choice(["♠️", "♥️", "♦️", "♣️"])
        return val, f"{name}{suit}"

    def start_session(self) -> Dict[str, Any]:
        val, card_str = self.draw_card_val()
        return {
            "current_val": val,
            "current_card": card_str,
            "streak": 0,
            "multiplier": 1.0,
        }

    def guess(self, state: Dict[str, Any], choice: str) -> Tuple[bool, str, bool]:
        next_val, next_card = self.draw_card_val()
        curr = state["current_val"]
        choice = choice.lower().strip()

        is_higher = next_val > curr
        is_lower = next_val < curr

        correct = (choice == "higher" and is_higher) or (choice == "lower" and is_lower) or (next_val == curr)

        old_card = state["current_card"]
        state["current_val"] = next_val
        state["current_card"] = next_card

        if correct:
            state["streak"] += 1
            state["multiplier"] = round(1.0 + (state["streak"] * 0.5), 1)
            return True, f"✅ <b>CORRECT!</b> Card was <b>{next_card}</b> (Streak: {state['streak']}x, {state['multiplier']}x Payout)", False
        else:
            return False, f"❌ <b>WRONG!</b> Card was <b>{next_card}</b>. Game Over!", True
