"""
Miko Telegram Gaming Platform - Games Group A
Implements:
1. Tic Tac Toe (tictactoe)
2. Rock Paper Scissors (rps)
3. Connect Four (connect4)
4. Hangman (hangman)
5. Wordle-style Word Game (wordle)
"""

from __future__ import annotations

import random
import time
from typing import Dict, Any, List, Optional, Tuple

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from modules.core.game_engine import BaseGame, GameSession, CentralGamingEngine
from modules.utils.storage import atomic_add_balance, atomic_deduct_balance, add_xp, get_user


# ==============================================================================
# 1. TIC TAC TOE
# ==============================================================================
class TicTacToeGame(BaseGame):
    def __init__(self):
        super().__init__("tictactoe", "Tic Tac Toe ⭕❌", min_players=1, max_players=2, default_stake=500)

    def new_board(self) -> List[str]:
        return [" "] * 9

    def check_winner(self, board: List[str]) -> Optional[str]:
        wins = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Cols
            (0, 4, 8), (2, 4, 6),              # Diags
        ]
        for a, b, c in wins:
            if board[a] != " " and board[a] == board[b] == board[c]:
                return board[a]
        if " " not in board:
            return "DRAW"
        return None

    def get_ai_move(self, board: List[str]) -> int:
        # Check if AI can win
        for i in range(9):
            if board[i] == " ":
                board[i] = "O"
                if self.check_winner(board) == "O":
                    board[i] = " "
                    return i
                board[i] = " "

        # Check if player could win and block
        for i in range(9):
            if board[i] == " ":
                board[i] = "X"
                if self.check_winner(board) == "X":
                    board[i] = " "
                    return i
                board[i] = " "

        # Center or corners
        if board[4] == " ":
            return 4
        corners = [i for i in [0, 2, 6, 8] if board[i] == " "]
        if corners:
            return random.choice(corners)
        empty = [i for i, v in enumerate(board) if v == " "]
        return random.choice(empty) if empty else 0

    def render_keyboard(self, session_id: str, board: List[str], game_over: bool = False) -> InlineKeyboardMarkup:
        rows = []
        icons = {"X": "❌", "O": "⭕", " ": "⬜"}
        for r in range(3):
            btn_row = []
            for c in range(3):
                idx = r * 3 + c
                symbol = icons[board[idx]]
                cb_data = f"ttt_move:{session_id}:{idx}" if (not game_over and board[idx] == " ") else "ttt_noop"
                btn_row.append(InlineKeyboardButton(symbol, callback_data=cb_data))
            rows.append(btn_row)
        return InlineKeyboardMarkup(rows)


# ==============================================================================
# 2. ROCK PAPER SCISSORS
# ==============================================================================
class RockPaperScissorsGame(BaseGame):
    RULES = {
        "rock": ["scissors", "lizard"],
        "paper": ["rock", "spock"],
        "scissors": ["paper", "lizard"],
        "lizard": ["spock", "paper"],
        "spock": ["scissors", "rock"],
    }
    ICONS = {
        "rock": "🪨 Rock",
        "paper": "📄 Paper",
        "scissors": "✂️ Scissors",
        "lizard": "🦎 Lizard",
        "spock": "🖖 Spock",
    }

    def __init__(self):
        super().__init__("rps", "Rock Paper Scissors 🪨📄✂️", min_players=1, max_players=2, default_stake=1000)

    def determine_winner(self, move_a: str, move_b: str) -> str:
        if move_a == move_b:
            return "DRAW"
        if move_b in self.RULES.get(move_a, []):
            return "WIN"
        return "LOSE"


# ==============================================================================
# 3. CONNECT FOUR
# ==============================================================================
class ConnectFourGame(BaseGame):
    ROWS = 6
    COLS = 7

    def __init__(self):
        super().__init__("connect4", "Connect Four 🔴🟡", min_players=1, max_players=2, default_stake=1000)

    def new_board(self) -> List[List[str]]:
        return [["⚪" for _ in range(self.COLS)] for _ in range(self.ROWS)]

    def drop_piece(self, board: List[List[str]], col: int, piece: str) -> Optional[int]:
        if col < 0 or col >= self.COLS or board[0][col] != "⚪":
            return None
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][col] == "⚪":
                board[r][col] = piece
                return r
        return None

    def check_winner(self, board: List[List[str]]) -> Optional[str]:
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                p = board[r][c]
                if p != "⚪" and p == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return p

        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                p = board[r][c]
                if p != "⚪" and p == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return p

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                p = board[r][c]
                if p != "⚪" and p == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return p

        # Diagonal \
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                p = board[r][c]
                if p != "⚪" and p == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return p

        # Check full (Draw)
        if all(board[0][c] != "⚪" for c in range(self.COLS)):
            return "DRAW"
        return None

    def render_board(self, board: List[List[str]]) -> str:
        grid_lines = ["1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣"]
        for row in board:
            grid_lines.append(" ".join(row))
        return "\n".join(grid_lines)


# ==============================================================================
# 4. HANGMAN
# ==============================================================================
class HangmanGame(BaseGame):
    WORDS = {
        "Animals": ["ELEPHANT", "CHEETAH", "PENGUIN", "KANGAROO", "DOLPHIN", "CHAMELEON"],
        "Tech": ["PYTHON", "DATABASE", "TELEGRAM", "COMPILER", "ALGORITHM", "ENCRYPTION"],
        "Gaming": ["NINTENDO", "WARCRAFT", "MINECRAFT", "VALORANT", "FORTNITE", "ASSASSIN"],
        "Mythology": ["VALKYRIE", "PEGASUS", "POSEIDON", "MINOTAUR", "CERBERUS", "RAGNAROK"],
    }
    GALLOWS = [
        "  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========",
        "  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========",
        "  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========",
        "  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========",
        "  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========",
        "  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========",
        "  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========",
    ]

    def __init__(self):
        super().__init__("hangman", "Hangman 🪢", min_players=1, max_players=1, default_stake=500)

    def start_hangman_session(self) -> Dict[str, Any]:
        category = random.choice(list(self.WORDS.keys()))
        word = random.choice(self.WORDS[category])
        return {
            "category": category,
            "word": word,
            "guessed": [],
            "wrong_strikes": 0,
            "max_strikes": 6,
        }

    def guess_letter(self, state: Dict[str, Any], letter: str) -> Tuple[bool, str, bool]:
        clean_letter = letter.upper()[:1]
        if clean_letter in state["guessed"]:
            return False, f"You already guessed '{clean_letter}'!", False

        state["guessed"].append(clean_letter)
        if clean_letter in state["word"]:
            # Check win
            won = all(c in state["guessed"] for c in state["word"])
            return True, f"🎯 Correct letter '{clean_letter}'!", won
        else:
            state["wrong_strikes"] += 1
            lost = state["wrong_strikes"] >= state["max_strikes"]
            return False, f"❌ Wrong letter '{clean_letter}'!", lost

    def get_display_word(self, state: Dict[str, Any]) -> str:
        return " ".join([c if c in state["guessed"] else "＿" for c in state["word"]])


# ==============================================================================
# 5. WORDLE
# ==============================================================================
class WordleGame(BaseGame):
    WORDS = [
        "CRANE", "SLATE", "AUDIO", "GHOST", "TIGER", "FLAME", "STORM",
        "BRAIN", "FROST", "SWORD", "MAGIC", "VIPER", "CLOUD", "LUCKY",
        "SHINE", "PRISM", "NOBLE", "ROYAL", "SPACE", "POWER", "ANGEL",
    ]

    def __init__(self):
        super().__init__("wordle", "Wordle Challenge 🟩🟨", min_players=1, max_players=1, default_stake=1000)

    def start_wordle_session(self) -> Dict[str, Any]:
        return {
            "target_word": random.choice(self.WORDS),
            "attempts": [],
            "max_attempts": 6,
        }

    def evaluate_guess(self, state: Dict[str, Any], guess: str) -> Tuple[bool, str, bool]:
        clean = guess.upper().strip()
        if len(clean) != 5 or not clean.isalpha():
            return False, "⚠️ Guess must be a 5-letter word!", False

        target = state["target_word"]
        feedback = []
        target_counts = {}
        for c in target:
            target_counts[c] = target_counts.get(c, 0) + 1

        res_tiles = ["⬜"] * 5
        # First pass: green matches
        for i in range(5):
            if clean[i] == target[i]:
                res_tiles[i] = "🟩"
                target_counts[clean[i]] -= 1

        # Second pass: yellow matches
        for i in range(5):
            if res_tiles[i] == "⬜" and clean[i] in target and target_counts.get(clean[i], 0) > 0:
                res_tiles[i] = "🟨"
                target_counts[clean[i]] -= 1

        row_str = f"{clean}  " + "".join(res_tiles)
        state["attempts"].append(row_str)

        won = (clean == target)
        lost = (len(state["attempts"]) >= state["max_attempts"] and not won)
        return True, row_str, (won or lost)
