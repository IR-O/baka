"""
Miko Telegram Gaming Platform - 20 New Games Telegram Command Handlers
Provides full start commands, input validation, state management, reward calculation, and replay.
"""

from __future__ import annotations

import html
import random
import time
from typing import Dict, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from modules.new_games.group_a import TicTacToeGame, RockPaperScissorsGame, ConnectFourGame, HangmanGame, WordleGame
from modules.new_games.group_b import MemoryMatchGame, SudokuGame, MinesweeperGame, BlackjackGame, HigherLowerGame
from modules.new_games.group_c import NumberGuessGame, TriviaBattleGame, EmojiQuizGame, ChessGame, CheckersGame
from modules.new_games.group_d import BattleshipGame, QuizTournamentGame, MultiplayerWordBattleGame, ReactionChallengeGame, DailyPuzzleChallenge, LudoDiceRaceGame

from modules.utils.storage import atomic_add_balance, atomic_deduct_balance, add_xp, get_user

# Active game state storage for chat sessions
_SESSIONS: Dict[str, Dict[str, Any]] = {}

ttt_engine = TicTacToeGame()
rps_engine = RockPaperScissorsGame()
c4_engine = ConnectFourGame()
hangman_engine = HangmanGame()
wordle_engine = WordleGame()

memory_engine = MemoryMatchGame()
sudoku_engine = SudokuGame()
mines_engine = MinesweeperGame()
bj_engine = BlackjackGame()
hl_engine = HigherLowerGame()

num_engine = NumberGuessGame()
trivia_engine = TriviaBattleGame()
emoji_engine = EmojiQuizGame()
chess_engine = ChessGame()
checkers_engine = CheckersGame()

bs_engine = BattleshipGame()
tourney_engine = QuizTournamentGame()
wb_engine = MultiplayerWordBattleGame()
react_engine = ReactionChallengeGame()
daily_engine = DailyPuzzleChallenge()
ludo_engine = LudoDiceRaceGame()


# 1. TIC TAC TOE
async def cmd_tictactoe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    pos = int(args[0]) if (args and args[0].isdigit() and 1 <= int(args[0]) <= 9) else None

    sess_key = f"ttt_{user.id}"
    board = _SESSIONS.get(sess_key, ttt_engine.new_board())

    if pos is None:
        _SESSIONS[sess_key] = ttt_engine.new_board()
        board = _SESSIONS[sess_key]
        text = (
            f"⭕❌ <b>TIC TAC TOE vs MIKO AI</b>\n\n"
            "Choose a cell from 1 to 9:\n"
            "<code>1 | 2 | 3</code>\n"
            "<code>4 | 5 | 6</code>\n"
            "<code>7 | 8 | 9</code>\n\n"
            "👉 Move with: <code>/tictactoe &lt;1-9&gt;</code>"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    idx = pos - 1
    if board[idx] != " ":
        await update.message.reply_text("⚠️ Cell already taken! Pick another.", parse_mode="HTML")
        return

    # Player move
    board[idx] = "X"
    winner = ttt_engine.check_winner(board)

    if winner == "X":
        del _SESSIONS[sess_key]
        atomic_add_balance(user.id, 1000, currency="coins", reason="Won TicTacToe")
        add_xp(user.id, 100)
        await update.message.reply_text("🎉 <b>VICTORY!</b> You beat the AI at Tic Tac Toe!\n🎁 Reward: +$1,000 coins, +100 XP!", parse_mode="HTML")
        return
    elif winner == "DRAW":
        del _SESSIONS[sess_key]
        await update.message.reply_text("🤝 <b>DRAW GAME!</b> Good match!", parse_mode="HTML")
        return

    # AI move
    ai_idx = ttt_engine.get_ai_move(board)
    board[ai_idx] = "O"
    winner2 = ttt_engine.check_winner(board)

    board_view = "\n".join([
        f"{board[0] or '1'} | {board[1] or '2'} | {board[2] or '3'}",
        f"{board[3] or '4'} | {board[4] or '5'} | {board[5] or '6'}",
        f"{board[6] or '7'} | {board[7] or '8'} | {board[8] or '9'}"
    ])

    if winner2 == "O":
        del _SESSIONS[sess_key]
        await update.message.reply_text(f"💀 AI placed O at #{ai_idx+1} and won!\n\n<code>{board_view}</code>\nTry again: <code>/tictactoe</code>", parse_mode="HTML")
    else:
        _SESSIONS[sess_key] = board
        await update.message.reply_text(f"🤖 AI placed O at #{ai_idx+1}.\n\n<code>{board_view}</code>\nYour turn: <code>/tictactoe &lt;1-9&gt;</code>", parse_mode="HTML")


# 2. ROCK PAPER SCISSORS
async def cmd_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("🪨📄✂️ Usage: <code>/rps &lt;rock|paper|scissors|lizard|spock&gt; [stake]</code>", parse_mode="HTML")
        return

    p_move = args[0].lower().strip()
    if p_move not in rps_engine.RULES:
        await update.message.reply_text(f"⚠️ Invalid choice. Pick from: <code>{', '.join(rps_engine.RULES.keys())}</code>", parse_mode="HTML")
        return

    stake = int(args[1]) if len(args) > 1 and args[1].isdigit() else 500
    ud = get_user(user.id)
    if ud.get("balance", 0) < stake:
        await update.message.reply_text(f"⚠️ You need ${stake:,} coins to play.")
        return

    ai_move = random.choice(list(rps_engine.RULES.keys()))
    res = rps_engine.determine_winner(p_move, ai_move)

    p_icon = rps_engine.ICONS.get(p_move, p_move)
    ai_icon = rps_engine.ICONS.get(ai_move, ai_move)

    if res == "WIN":
        atomic_add_balance(user.id, stake, currency="coins", reason="Won RPS")
        add_xp(user.id, 50)
        msg = f"🎉 <b>YOU WON!</b>\n\n👤 You: {p_icon}\n🤖 Miko: {ai_icon}\n🎁 Reward: +${stake:,} coins, +50 XP!"
    elif res == "LOSE":
        atomic_deduct_balance(user.id, stake, currency="coins", reason="Lost RPS")
        msg = f"💀 <b>YOU LOST!</b>\n\n👤 You: {p_icon}\n🤖 Miko: {ai_icon}\n💸 Lost: -${stake:,} coins."
    else:
        msg = f"🤝 <b>TIE GAME!</b>\n\nBoth picked {p_icon}!"

    await update.message.reply_text(msg, parse_mode="HTML")


# 3. CONNECT FOUR
async def cmd_connect4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    col = int(args[0]) if (args and args[0].isdigit()) else None

    sess_key = f"c4_{user.id}"
    board = _SESSIONS.get(sess_key, c4_engine.new_board())

    if col is None or col < 1 or col > 7:
        _SESSIONS[sess_key] = c4_engine.new_board()
        board_str = c4_engine.render_board(_SESSIONS[sess_key])
        await update.message.reply_text(
            f"🔴🟡 <b>CONNECT FOUR</b>\n\n{board_str}\n\n👉 Drop a piece with: <code>/connect4 &lt;1-7&gt;</code>",
            parse_mode="HTML"
        )
        return

    # Drop piece (🔴 for player)
    row = c4_engine.drop_piece(board, col - 1, "🔴")
    if row is None:
        await update.message.reply_text("⚠️ Column is full! Pick another column.", parse_mode="HTML")
        return

    winner = c4_engine.check_winner(board)
    if winner == "🔴":
        del _SESSIONS[sess_key]
        atomic_add_balance(user.id, 2000, currency="coins", reason="Won Connect Four")
        add_xp(user.id, 150)
        await update.message.reply_text(f"🎉 <b>CONNECT FOUR!</b> You won!\n\n{c4_engine.render_board(board)}\n\n🎁 Reward: +$2,000 coins, +150 XP!", parse_mode="HTML")
        return

    # AI move (🟡)
    ai_col = random.choice([c for c in range(7) if board[0][c] == "⚪"])
    c4_engine.drop_piece(board, ai_col, "🟡")
    winner2 = c4_engine.check_winner(board)

    if winner2 == "🟡":
        del _SESSIONS[sess_key]
        await update.message.reply_text(f"💀 AI connected 4 and won!\n\n{c4_engine.render_board(board)}\n\nTry again: <code>/connect4</code>", parse_mode="HTML")
    else:
        _SESSIONS[sess_key] = board
        await update.message.reply_text(f"🤖 AI dropped in column {ai_col+1}.\n\n{c4_engine.render_board(board)}\n\nYour turn: <code>/connect4 &lt;1-7&gt;</code>", parse_mode="HTML")


# 4. HANGMAN
async def cmd_hangman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"hm_{user.id}"

    if not args:
        state = hangman_engine.start_hangman_session()
        _SESSIONS[sess_key] = state
        disp = hangman_engine.get_display_word(state)
        await update.message.reply_text(
            f"🪢 <b>HANGMAN</b> ({state['category']})\n\n"
            f"<pre>{hangman_engine.GALLOWS[0]}</pre>\n\n"
            f"Word: <b>{disp}</b>\n\n"
            "👉 Guess a letter: <code>/hangman &lt;letter&gt;</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        await update.message.reply_text("⚠️ Start a new game with <code>/hangman</code> first!", parse_mode="HTML")
        return

    letter = args[0]
    ok, note, game_over = hangman_engine.guess_letter(state, letter)
    gallows = hangman_engine.GALLOWS[state["wrong_strikes"]]
    disp = hangman_engine.get_display_word(state)

    if game_over:
        del _SESSIONS[sess_key]
        if ok:
            atomic_add_balance(user.id, 1500, currency="coins", reason="Won Hangman")
            add_xp(user.id, 120)
            await update.message.reply_text(f"🎉 <b>VICTORY!</b> You solved the word <b>{state['word']}</b>!\n🎁 Reward: +$1,500 coins, +120 XP!", parse_mode="HTML")
        else:
            await update.message.reply_text(f"💀 <b>HANGED!</b> The word was <b>{state['word']}</b>.\n<pre>{gallows}</pre>", parse_mode="HTML")
    else:
        await update.message.reply_text(
            f"{note}\n<pre>{gallows}</pre>\nWord: <b>{disp}</b>\nGuessed: {', '.join(state['guessed'])}\nNext guess: <code>/hangman &lt;letter&gt;</code>",
            parse_mode="HTML"
        )


# 5. WORDLE
async def cmd_wordle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"wdl_{user.id}"

    if not args:
        state = wordle_engine.start_wordle_session()
        _SESSIONS[sess_key] = state
        await update.message.reply_text(
            "🟩🟨 <b>WORDLE DAILY</b>\n\n"
            "Guess the secret 5-letter word in 6 tries!\n"
            "🟩 = Correct spot | 🟨 = In word, wrong spot | ⬜ = Not in word\n\n"
            "👉 Guess with: <code>/wordle &lt;5_letter_word&gt;</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        state = wordle_engine.start_wordle_session()
        _SESSIONS[sess_key] = state

    ok, line, game_over = wordle_engine.evaluate_guess(state, args[0])
    if not ok:
        await update.message.reply_text(line, parse_mode="HTML")
        return

    board_view = "\n".join(state["attempts"])
    if game_over:
        del _SESSIONS[sess_key]
        if "🟩🟩🟩🟩🟩" in line:
            atomic_add_balance(user.id, 2500, currency="coins", reason="Solved Wordle")
            add_xp(user.id, 200)
            await update.message.reply_text(f"🎉 <b>GENIUS!</b> Solved in {len(state['attempts'])}/6 tries!\n\n{board_view}\n\n🎁 Reward: +$2,500 coins, +200 XP!", parse_mode="HTML")
        else:
            await update.message.reply_text(f"💀 Out of attempts! The word was <b>{state['target_word']}</b>.\n\n{board_view}", parse_mode="HTML")
    else:
        rem = state["max_attempts"] - len(state["attempts"])
        await update.message.reply_text(f"<b>Wordle Board:</b>\n{board_view}\n\n<i>{rem} attempts remaining. Next: /wordle &lt;word&gt;</i>", parse_mode="HTML")


# 6. MEMORY MATCH
async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"mem_{user.id}"

    if not args or len(args) < 2:
        state = memory_engine.start_memory_session()
        _SESSIONS[sess_key] = state
        await update.message.reply_text(
            "🃏🧠 <b>MEMORY MATCH</b>\n\n"
            "Find all 6 pairs in a 12-card grid (Index 1 to 12)!\n"
            "👉 Flip 2 cards: <code>/memory &lt;idx1&gt; &lt;idx2&gt;</code>\n"
            "Example: <code>/memory 1 5</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        await update.message.reply_text("⚠️ Start a new game with <code>/memory</code> first.")
        return

    try:
        i1 = int(args[0]) - 1
        i2 = int(args[1]) - 1
    except ValueError:
        await update.message.reply_text("⚠️ Please enter two numbers from 1 to 12.")
        return

    ok, note, is_win = memory_engine.flip_tiles(state, i1, i2)
    if is_win:
        del _SESSIONS[sess_key]
        atomic_add_balance(user.id, 3000, currency="coins", reason="Won Memory Match")
        add_xp(user.id, 250)
        await update.message.reply_text(f"{note}\n\n🎉 <b>SUPER MEMORY!</b> You matched all pairs in {state['moves']} moves!\n🎁 Reward: +$3,000 coins, +250 XP!", parse_mode="HTML")
    else:
        grid_disp = " ".join([state["deck"][i] if state["matched"][i] else f"[{i+1}]" for i in range(len(state["deck"]))])
        await update.message.reply_text(f"{note}\n\nBoard: {grid_disp}\nPairs left: {state['pairs_left']}\nNext: <code>/memory &lt;id1&gt; &lt;id2&gt;</code>", parse_mode="HTML")


# 7. SUDOKU
async def cmd_sudoku(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"sdk_{user.id}"

    if not args or len(args) < 3:
        state = sudoku_engine.start_sudoku_session()
        _SESSIONS[sess_key] = state
        grid_str = sudoku_engine.render_grid(state["current"])
        await update.message.reply_text(
            f"🔢 <b>SUDOKU MINI (4x4)</b>\n\n<pre>{grid_str}</pre>\n\n"
            "Fill rows, cols, and 2x2 boxes with numbers 1 to 4!\n"
            "👉 Place a number: <code>/sudoku &lt;row&gt; &lt;col&gt; &lt;val&gt;</code>\n"
            "Example: <code>/sudoku 1 2 4</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        await update.message.reply_text("⚠️ Start a game with <code>/sudoku</code> first.")
        return

    try:
        r, c, v = int(args[0]), int(args[1]), int(args[2])
    except ValueError:
        await update.message.reply_text("⚠️ Row, col, and value must be numbers 1-4.")
        return

    ok, note, is_solved = sudoku_engine.place_number(state, r, c, v)
    grid_str = sudoku_engine.render_grid(state["current"])

    if is_solved:
        del _SESSIONS[sess_key]
        atomic_add_balance(user.id, 2500, currency="coins", reason="Solved Sudoku")
        add_xp(user.id, 200)
        await update.message.reply_text(f"<pre>{grid_str}</pre>\n\n🎉 <b>BRILLIANT!</b> Sudoku solved perfectly!\n🎁 Reward: +$2,500 coins, +200 XP!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"{note}\n\n<pre>{grid_str}</pre>\nNext: <code>/sudoku &lt;r&gt; &lt;c&gt; &lt;v&gt;</code>", parse_mode="HTML")


# 8. MINESWEEPER
async def cmd_minesweeper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"ms_{user.id}"

    if not args or len(args) < 2:
        state = mines_engine.start_minesweeper_session()
        _SESSIONS[sess_key] = state
        board_str = mines_engine.render_board(state)
        await update.message.reply_text(
            f"💣 <b>MINESWEEPER</b> (5x5, 4 Mines)\n\n<pre>{board_str}</pre>\n\n"
            "👉 Uncover a coordinate: <code>/minesweeper &lt;row&gt; &lt;col&gt;</code>\n"
            "Example: <code>/minesweeper 2 3</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        await update.message.reply_text("⚠️ Start a new game with <code>/minesweeper</code>.")
        return

    try:
        r, c = int(args[0]) - 1, int(args[1]) - 1
    except ValueError:
        await update.message.reply_text("⚠️ Row and column must be numbers 1 to 5.")
        return

    ok, note, game_over = mines_engine.reveal(state, r, c)
    board_str = mines_engine.render_board(state, show_mines=game_over and not ok)

    if game_over:
        del _SESSIONS[sess_key]
        if ok:
            atomic_add_balance(user.id, 3500, currency="coins", reason="Cleared Minesweeper")
            add_xp(user.id, 300)
            await update.message.reply_text(f"<pre>{board_str}</pre>\n\n🎉 <b>MINEFIELD CLEARED!</b>\n🎁 Reward: +$3,500 coins, +300 XP!", parse_mode="HTML")
        else:
            await update.message.reply_text(f"{note}\n\n<pre>{board_str}</pre>\nTry again: <code>/minesweeper</code>", parse_mode="HTML")
    else:
        await update.message.reply_text(f"{note}\n\n<pre>{board_str}</pre>\nNext move: <code>/minesweeper &lt;row&gt; &lt;col&gt;</code>", parse_mode="HTML")


# 9. BLACKJACK
async def cmd_blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"bj_{user.id}"

    if not args or args[0].lower() in ("start", "new"):
        state = bj_engine.start_blackjack()
        _SESSIONS[sess_key] = state

        p_cards = " ".join([c["name"] for c in state["player_hand"]])
        d_card = state["dealer_hand"][0]["name"]
        await update.message.reply_text(
            f"♠️♦️ <b>BLACKJACK (21)</b>\n\n"
            f"👤 <b>Your Hand:</b> {p_cards} (Value: <b>{state['player_val']}</b>)\n"
            f"🤖 <b>Dealer Shows:</b> {d_card} 🂠\n\n"
            "👉 Next move: <code>/blackjack hit</code> or <code>/blackjack stand</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        await update.message.reply_text("⚠️ Deal a new hand with <code>/blackjack</code> first.")
        return

    action = args[0].lower().strip()
    if action == "hit":
        val, busted = bj_engine.hit(state)
        p_cards = " ".join([c["name"] for c in state["player_hand"]])
        if busted:
            del _SESSIONS[sess_key]
            await update.message.reply_text(f"💥 <b>BUST!</b> Hand value: <b>{val}</b> (Exceeded 21!)\nCards: {p_cards}\n\nPlay again: <code>/blackjack</code>", parse_mode="HTML")
        else:
            await update.message.reply_text(f"🃏 Drew card! Hand: {p_cards} (Value: <b>{val}</b>)\nChoose: <code>/blackjack hit</code> or <code>/blackjack stand</code>", parse_mode="HTML")
    elif action == "stand":
        res_state = bj_engine.stand(state)
        del _SESSIONS[sess_key]

        p_cards = " ".join([c["name"] for c in res_state["player_hand"]])
        d_cards = " ".join([c["name"] for c in res_state["dealer_hand"]])
        result = res_state["state"]

        if result == "WIN":
            atomic_add_balance(user.id, 2000, currency="coins", reason="Won Blackjack")
            add_xp(user.id, 150)
            msg = f"🎉 <b>YOU WIN!</b>\n\n👤 You: {p_cards} ({res_state['player_val']})\n🤖 Dealer: {d_cards} ({res_state['dealer_val']})\n🎁 Reward: +$2,000 coins, +150 XP!"
        elif result == "PUSH":
            msg = f"🤝 <b>PUSH!</b> Both have {res_state['player_val']}.\nYour stake is returned."
        else:
            msg = f"💀 <b>DEALER WINS!</b>\n\n👤 You: {p_cards} ({res_state['player_val']})\n🤖 Dealer: {d_cards} ({res_state['dealer_val']})"

        await update.message.reply_text(msg, parse_mode="HTML")


# 10. HIGHER OR LOWER
async def cmd_higherlower(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"hl_{user.id}"

    if not args:
        state = hl_engine.start_session()
        _SESSIONS[sess_key] = state
        await update.message.reply_text(
            f"⬆️⬇️ <b>HIGHER OR LOWER</b>\n\n"
            f"Current Card: <b>{state['current_card']}</b>\n\n"
            "Will the next card be HIGHER or LOWER?\n"
            "👉 Predict: <code>/higherlower higher</code> or <code>/higherlower lower</code>\n"
            "👉 Or cash out: <code>/higherlower cashout</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        await update.message.reply_text("⚠️ Start a game with <code>/higherlower</code> first.")
        return

    choice = args[0].lower().strip()
    if choice in ("cashout", "claim", "stop"):
        del _SESSIONS[sess_key]
        payout = int(1000 * state["multiplier"])
        atomic_add_balance(user.id, payout, currency="coins", reason="Cashed out HigherLower")
        add_xp(user.id, state["streak"] * 50)
        await update.message.reply_text(f"💰 <b>CASHED OUT!</b> You walked away with a <b>{state['multiplier']}x</b> multiplier!\n🎁 Payout: +${payout:,} coins!", parse_mode="HTML")
        return

    ok, note, game_over = hl_engine.guess(state, choice)
    if game_over:
        del _SESSIONS[sess_key]
        await update.message.reply_text(f"{note}\nPlay again with <code>/higherlower</code>!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"{note}\nNext card: <b>{state['current_card']}</b>\n\nPredict: <code>/higherlower higher</code>, <code>/higherlower lower</code>, or <code>/higherlower cashout</code>", parse_mode="HTML")


# 11. NUMBER GUESS
async def cmd_numberguess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"ng_{user.id}"

    if not args:
        _SESSIONS[sess_key] = num_engine.start_session(100)
        await update.message.reply_text(
            "🔢🎯 <b>NUMBER GUESSING GAME</b>\n\n"
            "I am thinking of a secret number between 1 and 100.\n"
            "You have 7 attempts to guess it!\n"
            "👉 Guess with: <code>/numberguess &lt;number&gt;</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        _SESSIONS[sess_key] = num_engine.start_session(100)
        state = _SESSIONS[sess_key]

    try:
        val = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a number between 1 and 100.")
        return

    won, msg, done = num_engine.guess(state, val)
    if done:
        del _SESSIONS[sess_key]
        if won:
            atomic_add_balance(user.id, 1500, currency="coins", reason="Won Number Guess")
            add_xp(user.id, 100)
            msg += "\n🎁 Reward: +$1,500 coins, +100 XP!"
    await update.message.reply_text(msg, parse_mode="HTML")


# 12. TRIVIA BATTLE
async def cmd_trivia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"trv_{user.id}"

    if not args:
        q = trivia_engine.get_question()
        _SESSIONS[sess_key] = q
        opts = "\n".join([f"<b>{i+1}.</b> {opt}" for i, opt in enumerate(q["options"])])
        await update.message.reply_text(
            f"🧠🏆 <b>TRIVIA CHALLENGE</b>\n\n"
            f"❓ <b>{q['q']}</b>\n\n"
            f"{opts}\n\n"
            "👉 Answer with: <code>/trivia &lt;1-4&gt;</code>",
            parse_mode="HTML"
        )
        return

    q = _SESSIONS.get(sess_key)
    if not q:
        await update.message.reply_text("⚠️ Get a question with <code>/trivia</code> first.")
        return

    del _SESSIONS[sess_key]
    try:
        choice = int(args[0]) - 1
    except ValueError:
        await update.message.reply_text("⚠️ Choose 1, 2, 3, or 4.")
        return

    if choice == q["ans"]:
        atomic_add_balance(user.id, 1200, currency="coins", reason="Won Trivia")
        add_xp(user.id, 120)
        await update.message.reply_text(f"🎉 <b>CORRECT!</b> The answer was <b>{q['options'][q['ans']]}</b>!\n🎁 Reward: +$1,200 coins, +120 XP!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"❌ <b>Incorrect!</b> The correct answer was <b>{q['options'][q['ans']]}</b>.", parse_mode="HTML")


# 13. EMOJI QUIZ
async def cmd_emojiquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"eq_{user.id}"

    if not args:
        p = emoji_engine.get_puzzle()
        _SESSIONS[sess_key] = p
        await update.message.reply_text(
            f"🎬🧩 <b>EMOJI POP QUIZ</b>\n\n"
            f"Guess the movie/phrase:\n"
            f"<h1>{p['emojis']}</h1>\n"
            f"💡 Hint: <i>{p['hint']}</i>\n\n"
            "👉 Answer with: <code>/emojiquiz &lt;title&gt;</code>",
            parse_mode="HTML"
        )
        return

    p = _SESSIONS.get(sess_key)
    if not p:
        await update.message.reply_text("⚠️ Start with <code>/emojiquiz</code> first.")
        return

    guess = " ".join(args)
    if emoji_engine.check_answer(p, guess):
        del _SESSIONS[sess_key]
        atomic_add_balance(user.id, 1500, currency="coins", reason="Solved Emoji Quiz")
        add_xp(user.id, 150)
        await update.message.reply_text(f"🎉 <b>GENIUS!</b> The answer was <b>{p['answer']}</b>!\n🎁 Reward: +$1,500 coins, +150 XP!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"❌ '{html.escape(guess)}' is incorrect! Try again: <code>/emojiquiz &lt;title&gt;</code>", parse_mode="HTML")


# 14. CHESS PUZZLE
async def cmd_chess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"chs_{user.id}"

    if not args:
        p = chess_engine.get_puzzle()
        _SESSIONS[sess_key] = p
        await update.message.reply_text(
            f"♟️👑 <b>TACTICAL CHESS TACTIC</b>\n\n"
            f"<b>Position:</b> {p['fen_desc']}\n"
            f"🎯 <b>Objective:</b> {p['prompt']}\n\n"
            "👉 Enter your move (e.g. <code>Qxf7</code>, <code>Ra8</code>, <code>Nf7</code>):\n"
            "<code>/chess &lt;move&gt;</code>",
            parse_mode="HTML"
        )
        return

    p = _SESSIONS.get(sess_key)
    if not p:
        await update.message.reply_text("⚠️ Start a puzzle with <code>/chess</code> first.")
        return

    move_guess = " ".join(args)
    if chess_engine.verify_move(p, move_guess):
        del _SESSIONS[sess_key]
        atomic_add_balance(user.id, 2500, currency="coins", reason="Solved Chess Tactic")
        add_xp(user.id, 200)
        await update.message.reply_text(f"🎉 <b>CHECKMATE!</b> Solution <b>{p['solution']}</b> is correct!\n🎁 Reward: +$2,500 coins, +200 XP!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"❌ Move '{html.escape(move_guess)}' does not deliver mate-in-1. Try again!", parse_mode="HTML")


# 15. CHECKERS
async def cmd_checkers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    b = checkers_engine.new_board()
    reds, whites = checkers_engine.count_pieces(b)
    lines = ["🔴⚪ <b>CHECKERS MATCH ARENA</b>\n"]
    for row in b:
        lines.append("".join(row))
    lines.append(f"\n🔴 Red: {reds} pieces | ⚪ White: {whites} pieces")
    lines.append("<i>Interactive checker movements coming in tournament mode!</i>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# 16. BATTLESHIP
async def cmd_battleship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"bs_{user.id}"

    if not args or len(args) < 2:
        state = bs_engine.start_battleship_session()
        _SESSIONS[sess_key] = state
        radar = bs_engine.render_radar(state)
        await update.message.reply_text(
            f"🚢🌊 <b>NAVAL BATTLESHIP RADAR</b>\n\n<pre>{radar}</pre>\n\n"
            f"3 enemy ships hidden in a 5x5 grid! 10 shells available.\n"
            "👉 Fire shell: <code>/battleship &lt;row&gt; &lt;col&gt;</code>\n"
            "Example: <code>/battleship 3 4</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        await update.message.reply_text("⚠️ Start a naval mission with <code>/battleship</code> first.")
        return

    try:
        r, c = int(args[0]), int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Row and column must be numbers 1-5.")
        return

    hit, note, game_over = bs_engine.fire_shell(state, r, c)
    radar = bs_engine.render_radar(state)

    if game_over:
        del _SESSIONS[sess_key]
        if hit and len(state["hits"]) == len(state["ships"]):
            atomic_add_balance(user.id, 4000, currency="coins", reason="Won Battleship")
            add_xp(user.id, 350)
            await update.message.reply_text(f"<pre>{radar}</pre>\n\n🎉 <b>FLEET ANNIHILATED!</b> All enemy ships sunk!\n🎁 Reward: +$4,000 coins, +350 XP!", parse_mode="HTML")
        else:
            await update.message.reply_text(f"{note}\n\n<pre>{radar}</pre>\n💀 <b>Out of ammunition!</b> Naval defeat.", parse_mode="HTML")
    else:
        await update.message.reply_text(f"{note}\n\n<pre>{radar}</pre>\nNext shot: <code>/battleship &lt;r&gt; &lt;c&gt;</code>", parse_mode="HTML")


# 17. QUIZ TOURNAMENT
async def cmd_quiztourney(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    q = trivia_engine.get_question()
    payout = tourney_engine.calculate_tournament_payout(streak=3, base_stake=1500)
    opts = "\n".join([f"<b>{i+1}.</b> {opt}" for i, opt in enumerate(q["options"])])
    await update.message.reply_text(
        f"🏆👑 <b>GRAND QUIZ TOURNAMENT</b>\n\n"
        f"❓ <b>{q['q']}</b>\n\n{opts}\n\n"
        f"💰 Current Prize Pool: <b>${payout:,} coins</b>\n"
        "👉 Submit answer: <code>/trivia &lt;1-4&gt;</code>",
        parse_mode="HTML"
    )


# 18. MULTIPLAYER WORD BATTLE
async def cmd_wordbattle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    args = context.args or []
    sess_key = f"wb_{chat.id if chat else user.id}"

    if not args:
        state = wb_engine.start_battle()
        _SESSIONS[sess_key] = state
        await update.message.reply_text(
            f"⚔️🔤 <b>MULTIPLAYER WORD BATTLE</b>\n\n"
            f"Form valid subwords (3+ letters) from:\n"
            f"<h1>{state['root_word']}</h1>\n\n"
            "👉 Claim a word: <code>/wordbattle &lt;word&gt;</code>\n"
            "Example: If root is TELEGRAM, submit: <code>/wordbattle game</code>",
            parse_mode="HTML"
        )
        return

    state = _SESSIONS.get(sess_key)
    if not state:
        await update.message.reply_text("⚠️ Start a battle with <code>/wordbattle</code> first!")
        return

    subword = args[0]
    ok, note, pts = wb_engine.submit_subword(state, user.id, subword)
    if ok:
        atomic_add_balance(user.id, pts * 10, currency="coins", reason=f"WordBattle {subword}")
        add_xp(user.id, pts)
        await update.message.reply_text(f"{note}\nRoot: <b>{state['root_word']}</b> | Total claimed: {len(state['accepted_words'])} words", parse_mode="HTML")
    else:
        await update.message.reply_text(note, parse_mode="HTML")


# 19. REACTION CHALLENGE
async def cmd_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    sess_key = f"rct_{user.id}"

    if not args:
        _SESSIONS[sess_key] = time.time()
        await update.message.reply_text(
            "⚡⏱️ <b>REFLEX SPEED CHALLENGE</b>\n\n"
            "🔴 Ready...\n"
            "🟡 Steady...\n"
            "🟢 <b>CLICK NOW!</b>\n\n"
            "👉 Respond with <code>/reaction tap</code> immediately!",
            parse_mode="HTML"
        )
        return

    start_t = _SESSIONS.get(sess_key)
    if not start_t:
        await update.message.reply_text("⚠️ Trigger with <code>/reaction</code> first.")
        return

    del _SESSIONS[sess_key]
    delta_ms = (time.time() - start_t) * 1000
    rank_str, prize = react_engine.evaluate_reaction_speed(delta_ms)
    atomic_add_balance(user.id, prize, currency="coins", reason="Reaction Speed")
    add_xp(user.id, 50)
    await update.message.reply_text(
        f"⚡ <b>Reaction Time: {delta_ms:.1f} ms</b>\n"
        f"🏆 {rank_str}\n"
        f"🎁 Reward: +${prize} coins, +50 XP!",
        parse_mode="HTML"
    )


# 20. DAILY PUZZLE CHALLENGE
async def cmd_dailypuzzle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    todays = daily_engine.get_todays_puzzle()

    if not args:
        await update.message.reply_text(
            f"🧩📅 <b>DAILY CONUNDRUM RIDDLE</b>\n\n"
            f"📜 <i>\"{todays['riddle']}\"</i>\n\n"
            "👉 Solve with: <code>/dailypuzzle &lt;answer&gt;</code>\n"
            "🎁 Solvers earn: <b>$5,000 coins + 2 💎 Gems + 300 XP</b>!",
            parse_mode="HTML"
        )
        return

    guess = " ".join(args)
    if daily_engine.check_solution(guess):
        atomic_add_balance(user.id, 5000, currency="coins", reason="Solved Daily Puzzle")
        atomic_add_balance(user.id, 2.0, currency="gems", reason="Solved Daily Puzzle")
        add_xp(user.id, 300)
        await update.message.reply_text(
            f"🎉 <b>CONGRATULATIONS!</b>\n\n"
            f"Answer: <b>{todays['ans']}</b> is correct!\n"
            f"🎁 Daily Rewards: +$5,000 coins, +2 💎 Gems, +300 XP!",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"❌ '{html.escape(guess)}' is incorrect! Ponder carefully and try again.", parse_mode="HTML")


# 21. COMPLETE INTERACTIVE LUDO DICE RACE
async def cmd_ludo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    sess_key = f"ludo_{user.id}"

    state = _SESSIONS.get(sess_key)
    if not state:
        state = ludo_engine.start_ludo_session([user.id])
        _SESSIONS[sess_key] = state

    roll, msg, is_win = ludo_engine.advance_player(state, user.id)
    pdata = state["players"][user.id]

    status_str = (
        f"🎲🏁 <b>LUDO DICE RACE CIRCUIT</b>\n\n"
        f"👤 <b>Player:</b> {pdata['color']} ({html.escape(user.first_name)})\n"
        f"🎲 <b>Dice Roll:</b> <b>{roll}</b>\n"
        f"📢 {msg}\n\n"
        f"📍 <b>Token Positions:</b> Token 1: Track #{pdata['tokens'][0]}/52 | Token 2: Track #{pdata['tokens'][1]}/52\n"
        f"🏆 <b>Tokens Home:</b> {pdata['home_tokens']} / 2\n\n"
    )

    if is_win:
        del _SESSIONS[sess_key]
        atomic_add_balance(user.id, 5000, currency="coins", reason="Won Ludo Race")
        add_xp(user.id, 400)
        status_str += "🎉 <b>VICTORY! Both tokens reached home base!</b>\n🎁 Prize: +$5,000 coins, +400 XP!"
    else:
        status_str += "👉 Roll again with: <code>/ludo</code>"

    await update.message.reply_text(status_str, parse_mode="HTML")


HANDLERS = {
    # Group A
    "tictactoe": cmd_tictactoe,
    "ttt": cmd_tictactoe,
    "rps": cmd_rps,
    "rockpaperscissors": cmd_rps,
    "connect4": cmd_connect4,
    "c4": cmd_connect4,
    "hangman": cmd_hangman,
    "wordle": cmd_wordle,

    # Group B
    "memory": cmd_memory,
    "mem": cmd_memory,
    "sudoku": cmd_sudoku,
    "minesweeper": cmd_minesweeper,
    "ms": cmd_minesweeper,
    "blackjack": cmd_blackjack,
    "bj": cmd_blackjack,
    "higherlower": cmd_higherlower,
    "hl": cmd_higherlower,

    # Group C
    "numberguess": cmd_numberguess,
    "ng": cmd_numberguess,
    "trivia": cmd_trivia,
    "emojiquiz": cmd_emojiquiz,
    "eq": cmd_emojiquiz,
    "chess": cmd_chess,
    "checkers": cmd_checkers,

    # Group D + Ludo
    "battleship": cmd_battleship,
    "bs": cmd_battleship,
    "quiztourney": cmd_quiztourney,
    "wordbattle": cmd_wordbattle,
    "wb": cmd_wordbattle,
    "reaction": cmd_reaction,
    "dailypuzzle": cmd_dailypuzzle,
    "dp": cmd_dailypuzzle,
    "ludo": cmd_ludo,
    "rollludo": cmd_ludo,
}
