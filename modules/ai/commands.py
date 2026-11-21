from __future__ import annotations

import html
from telegram import Update
from telegram.ext import ContextTypes

from modules.ai.game_assistant import AIGamingCopilot, GAME_EXPLANATIONS
from modules.ai.chatbot import _call_openrouter, _clean_ai_reply


async def cmd_gamehelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    copilot = AIGamingCopilot.get_instance()

    if not args:
        keys = ", ".join([f"<code>{k}</code>" for k in GAME_EXPLANATIONS.keys()])
        await update.message.reply_text(
            f"🎮 <b>AI Game Guide Usage:</b> <code>/gamehelp &lt;game_name&gt;</code>\n\n"
            f"Available game guides: {keys}",
            parse_mode="HTML"
        )
        return

    game_name = " ".join(args)
    text = copilot.explain_game(game_name)
    if text:
        await update.message.reply_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(f"⚠️ No game guide found for '{html.escape(game_name)}'. Try: <code>poker</code>, <code>roulette</code>, <code>bluff</code>, <code>cards</code>, <code>dungeon</code>, <code>pets</code>", parse_mode="HTML")


async def cmd_recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    copilot = AIGamingCopilot.get_instance()
    text = copilot.recommend_games(user.id)
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_askai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("🤖 <b>Usage:</b> <code>/askai &lt;question about games, rules, or bot features&gt;</code>", parse_mode="HTML")
        return

    prompt = " ".join(args).strip()
    copilot = AIGamingCopilot.get_instance()
    is_safe, error_msg = copilot.guardrail_check(prompt)

    if not is_safe:
        await update.message.reply_text(error_msg, parse_mode="HTML")
        return

    system_prompt = (
        "You are Miko AI Gaming Copilot, an expert gaming assistant for the Telegram gaming bot platform.\n"
        "Explain games, strategies, and features in a friendly, encouraging manner.\n"
        "Never promise balance changes, coin transfers, or admin privileges."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    reply = await _call_openrouter(messages)
    clean_reply = _clean_ai_reply(reply) if reply else "🤖 I am currently strategizing my next move! Please ask again in a moment."
    await update.message.reply_text(f"🤖 <b>AI Copilot:</b>\n\n{clean_reply}", parse_mode="HTML")


HANDLERS = {
    "gamehelp": cmd_gamehelp,
    "ghelp": cmd_gamehelp,
    "recommend": cmd_recommend,
    "recs": cmd_recommend,
    "askai": cmd_askai,
    "copilot": cmd_askai,
}
