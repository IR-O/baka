"""
Miko Telegram Gaming Platform - Games Group C
Implements:
11. Number Guess (numberguess)
12. Trivia Battle (trivia)
13. Emoji Quiz (emojiquiz)
14. Chess Mini (chess)
15. Checkers (checkers)
"""

from __future__ import annotations

import random
from typing import Dict, Any, List, Optional, Tuple

from modules.core.game_engine import BaseGame


# ==============================================================================
# 11. NUMBER GUESS
# ==============================================================================
class NumberGuessGame(BaseGame):
    def __init__(self):
        super().__init__("numberguess", "Number Guess 🔢🎯", min_players=1, max_players=1, default_stake=500)

    def start_session(self, max_num: int = 100) -> Dict[str, Any]:
        return {
            "target": random.randint(1, max_num),
            "attempts": 0,
            "max_attempts": 7,
            "max_num": max_num,
        }

    def guess(self, state: Dict[str, Any], val: int) -> Tuple[bool, str, bool]:
        state["attempts"] += 1
        target = state["target"]

        if val == target:
            return True, f"🎉 <b>BINGO!</b> You guessed the number <b>{target}</b> in {state['attempts']} attempts!", True

        if state["attempts"] >= state["max_attempts"]:
            return False, f"💀 <b>Game Over!</b> You ran out of attempts. The secret number was <b>{target}</b>.", True

        remaining = state["max_attempts"] - state["attempts"]
        hint = "📈 <b>Higher!</b>" if val < target else "📉 <b>Lower!</b>"
        return False, f"{hint} ({remaining} attempts remaining)", False


# ==============================================================================
# 12. TRIVIA BATTLE
# ==============================================================================
class TriviaBattleGame(BaseGame):
    QUESTIONS = [
        {
            "q": "What is the capital city of Australia?",
            "options": ["Sydney", "Melbourne", "Canberra", "Brisbane"],
            "ans": 2,
        },
        {
            "q": "Which programming language was created by Guido van Rossum?",
            "options": ["Ruby", "Python", "Rust", "Java"],
            "ans": 1,
        },
        {
            "q": "In Greek mythology, who is the God of the Sea?",
            "options": ["Zeus", "Hades", "Poseidon", "Ares"],
            "ans": 2,
        },
        {
            "q": "What is the highest-grossing video game franchise of all time?",
            "options": ["Call of Duty", "Pokémon", "Super Mario", "Grand Theft Auto"],
            "ans": 1,
        },
        {
            "q": "Which chemical element has the atomic symbol 'Au'?",
            "options": ["Silver", "Gold", "Argon", "Platinum"],
            "ans": 1,
        },
        {
            "q": "How many bones are in the adult human body?",
            "options": ["206", "195", "214", "250"],
            "ans": 0,
        },
    ]

    def __init__(self):
        super().__init__("trivia", "Trivia Battle 🧠🏆", min_players=1, max_players=2, default_stake=1000)

    def get_question(self) -> Dict[str, Any]:
        return random.choice(self.QUESTIONS)


# ==============================================================================
# 13. EMOJI QUIZ
# ==============================================================================
class EmojiQuizGame(BaseGame):
    PUZZLES = [
        {"emojis": "🦁 👑", "answer": "THE LION KING", "hint": "Disney Animated Classic"},
        {"emojis": "🕷️ 👨", "answer": "SPIDER-MAN", "hint": "Marvel Superhero"},
        {"emojis": "🚢 ❄️ 💔", "answer": "TITANIC", "hint": "1997 James Cameron Epic"},
        {"emojis": "🧙‍♂️ 💍 🌋", "answer": "LORD OF THE RINGS", "hint": "Tolkien Fantasy Epic"},
        {"emojis": "🦇 👨 🃏", "answer": "BATMAN", "hint": "The Dark Knight vs Joker"},
        {"emojis": "⚡ 👓 🧙", "answer": "HARRY POTTER", "hint": "The Boy Who Lived"},
        {"emojis": "🦕 🦖 🏝️", "answer": "JURASSIC PARK", "hint": "Prehistoric Dinosaur Island"},
        {"emojis": "👻 🚫 🔫", "answer": "GHOSTBUSTERS", "hint": "Who you gonna call?"},
    ]

    def __init__(self):
        super().__init__("emojiquiz", "Emoji Pop Quiz 🎬🧩", min_players=1, max_players=1, default_stake=500)

    def get_puzzle(self) -> Dict[str, str]:
        return random.choice(self.PUZZLES)

    def check_answer(self, puzzle: Dict[str, str], guess: str) -> bool:
        clean_g = guess.strip().upper().replace(" ", "").replace("-", "")
        clean_a = puzzle["answer"].replace(" ", "").replace("-", "")
        return clean_g == clean_a or clean_g in clean_a


# ==============================================================================
# 14. CHESS PUZZLE (MATE IN 1)
# ==============================================================================
class ChessGame(BaseGame):
    PUZZLES = [
        {
            "fen_desc": "White: Queen at h5, Bishop at c4 | Black: King at e8, Pawn at f7",
            "prompt": "White to move: Find the Scholar's Mate-in-1 checkmate move!",
            "solution": "Qxf7#",
            "aliases": ["QXF7", "Q F7", "QUEEN F7", "QxF7"],
            "board": "8/5p2/8/7Q/2B5/8/8/4K2k w - - 0 1"
        },
        {
            "fen_desc": "White: Rook at a1, Rook at b1 | Black: King at a8 (Back Rank)",
            "prompt": "White to move: Execute the Back-Rank Checkmate!",
            "solution": "Ra8#",
            "aliases": ["RA8", "R A8", "ROOK A8"],
            "board": "k7/8/8/8/8/8/8/R1R1K3 w - - 0 1"
        },
        {
            "fen_desc": "White: Knight at f7, Queen at g8 | Black: King at h8 (Smothered Mate)",
            "prompt": "White to move: Deliver the classic Smothered Mate with Knight!",
            "solution": "Nf7#",
            "aliases": ["NF7", "N F7", "KNIGHT F7"],
            "board": "6rk/5N2/8/8/8/8/8/4K3 w - - 0 1"
        }
    ]

    def __init__(self):
        super().__init__("chess", "Chess Blitz Tactic ♟️👑", min_players=1, max_players=1, default_stake=1000)

    def get_puzzle(self) -> Dict[str, Any]:
        return random.choice(self.PUZZLES)

    def verify_move(self, puzzle: Dict[str, Any], move_str: str) -> bool:
        clean = move_str.strip().upper().replace("#", "").replace("+", "").replace(" ", "")
        for a in puzzle["aliases"]:
            if clean == a.replace("#", "").replace("+", "").replace(" ", ""):
                return True
        return False


# ==============================================================================
# 15. CHECKERS
# ==============================================================================
class CheckersGame(BaseGame):
    def __init__(self):
        super().__init__("checkers", "Checkers / Draughts 🔴⚪", min_players=1, max_players=2, default_stake=1000)

    def new_board(self) -> List[List[str]]:
        # 8x8 checkers board
        board = [["⬛" if (r + c) % 2 == 1 else "⬜" for c in range(8)] for r in range(8)]
        # Place red on top 3 dark squares
        for r in range(3):
            for c in range(8):
                if (r + c) % 2 == 1:
                    board[r][c] = "🔴"
        # Place white on bottom 3 dark squares
        for r in range(5, 8):
            for c in range(8):
                if (r + c) % 2 == 1:
                    board[r][c] = "⚪"
        return board

    def count_pieces(self, board: List[List[str]]) -> Tuple[int, int]:
        reds = sum(row.count("🔴") + row.count("👑") for row in board)
        whites = sum(row.count("⚪") + row.count("⭐") for row in board)
        return reds, whites
