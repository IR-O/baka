import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.new_games.group_a import TicTacToeGame, RockPaperScissorsGame, ConnectFourGame, HangmanGame, WordleGame
from modules.new_games.group_b import MemoryMatchGame, SudokuGame, MinesweeperGame, BlackjackGame, HigherLowerGame
from modules.new_games.group_c import NumberGuessGame, TriviaBattleGame, EmojiQuizGame, ChessGame, CheckersGame
from modules.new_games.group_d import BattleshipGame, QuizTournamentGame, MultiplayerWordBattleGame, ReactionChallengeGame, DailyPuzzleChallenge, LudoDiceRaceGame


class TestPhase13Games(unittest.TestCase):
    def test_group_a_games(self):
        # 1. Tic Tac Toe
        ttt = TicTacToeGame()
        b = ttt.new_board()
        b[0] = b[1] = b[2] = "X"
        self.assertEqual(ttt.check_winner(b), "X")
        b2 = ["X", "O", "X", "X", "O", "O", "O", "X", "X"]
        self.assertEqual(ttt.check_winner(b2), "DRAW")

        # 2. Rock Paper Scissors
        rps = RockPaperScissorsGame()
        self.assertEqual(rps.determine_winner("rock", "scissors"), "WIN")
        self.assertEqual(rps.determine_winner("rock", "paper"), "LOSE")
        self.assertEqual(rps.determine_winner("spock", "spock"), "DRAW")
        self.assertEqual(rps.determine_winner("spock", "scissors"), "WIN")

        # 3. Connect Four
        c4 = ConnectFourGame()
        c4_b = c4.new_board()
        c4.drop_piece(c4_b, 0, "🔴")
        c4.drop_piece(c4_b, 1, "🔴")
        c4.drop_piece(c4_b, 2, "🔴")
        c4.drop_piece(c4_b, 3, "🔴")
        self.assertEqual(c4.check_winner(c4_b), "🔴")

        # 4. Hangman
        hm = HangmanGame()
        state = hm.start_hangman_session()
        state["word"] = "TEST"
        ok, _, won = hm.guess_letter(state, "T")
        self.assertTrue(ok)
        self.assertFalse(won)
        ok, _, won = hm.guess_letter(state, "E")
        ok, _, won = hm.guess_letter(state, "S")
        self.assertTrue(won)

        # 5. Wordle
        wdl = WordleGame()
        w_state = wdl.start_wordle_session()
        w_state["target_word"] = "SHINE"
        ok, line, over = wdl.evaluate_guess(w_state, "SHINE")
        self.assertTrue(ok)
        self.assertTrue(over)
        self.assertIn("🟩🟩🟩🟩🟩", line)

    def test_group_b_games(self):
        # 6. Memory Match
        mem = MemoryMatchGame()
        m_state = mem.start_memory_session()
        self.assertEqual(m_state["pairs_left"], 6)

        # 7. Sudoku Mini
        sdk = SudokuGame()
        s_state = sdk.start_sudoku_session()
        r_str = sdk.render_grid(s_state["current"])
        self.assertIn("┌───┬───┐", r_str)

        # 8. Minesweeper
        ms = MinesweeperGame()
        ms_state = ms.start_minesweeper_session()
        self.assertEqual(ms_state["safe_remaining"], 21)

        # 9. Blackjack
        bj = BlackjackGame()
        hand = [{"val": 11, "rank": "A"}, {"val": 10, "rank": "K"}]
        self.assertEqual(bj.hand_value(hand), 21)
        hand_bust = [{"val": 10, "rank": "K"}, {"val": 10, "rank": "Q"}, {"val": 5, "rank": "5"}]
        self.assertEqual(bj.hand_value(hand_bust), 25)

        # 10. Higher or Lower
        hl = HigherLowerGame()
        hl_state = hl.start_session()
        hl_state["current_val"] = 2
        ok, msg, over = hl.guess(hl_state, "higher")
        self.assertIn("Card was", msg)

    def test_group_c_games(self):
        # 11. Number Guess
        ng = NumberGuessGame()
        n_state = ng.start_session(100)
        n_state["target"] = 50
        won, msg, done = ng.guess(n_state, 25)
        self.assertFalse(won)
        self.assertIn("Higher", msg)
        won, msg, done = ng.guess(n_state, 50)
        self.assertTrue(won)
        self.assertTrue(done)

        # 12. Trivia
        trv = TriviaBattleGame()
        q = trv.get_question()
        self.assertIn("q", q)
        self.assertEqual(len(q["options"]), 4)

        # 13. Emoji Quiz
        eq = EmojiQuizGame()
        p = {"emojis": "🦁 👑", "answer": "THE LION KING", "hint": "Disney"}
        self.assertTrue(eq.check_answer(p, "lion king"))

        # 14. Chess Puzzle
        chs = ChessGame()
        p_chs = chs.PUZZLES[0]
        self.assertTrue(chs.verify_move(p_chs, "Qxf7#"))

        # 15. Checkers
        chk = CheckersGame()
        b_chk = chk.new_board()
        reds, whites = chk.count_pieces(b_chk)
        self.assertEqual(reds, 12)
        self.assertEqual(whites, 12)

    def test_group_d_games_and_ludo(self):
        # 16. Battleship
        bs = BattleshipGame()
        bs_state = bs.start_battleship_session()
        ship = list(bs_state["ships"])[0]
        hit, msg, all_sunk = bs.fire_shell(bs_state, ship[0] + 1, ship[1] + 1)
        self.assertTrue(hit)
        self.assertIn("DIRECT HIT", msg)

        # 17. Quiz Tourney
        qt = QuizTournamentGame()
        payout = qt.calculate_tournament_payout(streak=2, base_stake=1000)
        self.assertEqual(payout, 2500)

        # 18. Word Battle
        wb = MultiplayerWordBattleGame()
        wb_state = {"root_word": "TELEGRAM", "accepted_words": set(), "scores": {}}
        ok, msg, pts = wb.submit_subword(wb_state, 1234, "GREAT")
        self.assertTrue(ok)
        self.assertGreater(pts, 0)

        # 19. Reaction Challenge
        rc = ReactionChallengeGame()
        rank, prize = rc.evaluate_reaction_speed(150.0)
        self.assertIn("Rank S", rank)

        # 20. Daily Puzzle
        dp = DailyPuzzleChallenge()
        puzzle = dp.get_todays_puzzle()
        self.assertIn("riddle", puzzle)
        self.assertTrue(dp.check_solution(puzzle["ans"]))

        # 21. Ludo Dice Race
        ludo = LudoDiceRaceGame()
        l_state = ludo.start_ludo_session([5001])
        roll, msg, won = ludo.advance_player(l_state, 5001)
        self.assertGreaterEqual(roll, 1)
        self.assertLessEqual(roll, 6)
        self.assertIn("Rolled a", msg)


if __name__ == "__main__":
    unittest.main()
