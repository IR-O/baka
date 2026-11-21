from __future__ import annotations

import html
from telegram import Update
from telegram.ext import ContextTypes

from modules.missions.mission_manager import MissionManager


async def cmd_missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mm = MissionManager.get_instance()
    missions = mm.get_user_missions(user.id)

    lines = [f"📜 <b>{html.escape(user.first_name)}'s Quest Logbook</b>\n"]

    lines.append("☀️ <b>Daily Missions (Resets Daily at Midnight UTC):</b>")
    for m in missions["daily"]:
        state = "✅ [CLAIMED]" if m["claimed"] else ("🎁 [CLAIMABLE!]" if m["completed"] else f"({m['progress']}/{m['target']})")
        lines.append(f"• <b>{m['description']}</b> {state}\n   ID: <code>{m['id']}</code> | Reward: ${m['reward_coins']:,} + {m['reward_xp']} XP")

    lines.append("\n🗓️ <b>Weekly Missions (Resets Every Monday UTC):</b>")
    for m in missions["weekly"]:
        state = "✅ [CLAIMED]" if m["claimed"] else ("🎁 [CLAIMABLE!]" if m["completed"] else f"({m['progress']}/{m['target']})")
        lines.append(f"• <b>{m['description']}</b> {state}\n   ID: <code>{m['id']}</code> | Reward: ${m['reward_coins']:,} + {m['reward_gems']} 💎 + {m['reward_tokens']} 🎟️")

    lines.append(
        "\n👉 <b>Claim your rewards:</b> <code>/claimmission &lt;id&gt;</code>\n"
        "Example: <code>/claimmission daily_play</code>"
    )
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_claimmission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("📜 Usage: <code>/claimmission &lt;mission_id&gt;</code>\nCheck quests with <code>/missions</code>", parse_mode="HTML")
        return

    mission_id = args[0]
    mm = MissionManager.get_instance()
    ok, msg = mm.claim_mission(user.id, mission_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mm = MissionManager.get_instance()
    events = mm.get_active_events()

    lines = ["🎉 <b>SEASONAL EVENTS & CAMPAIGNS</b>\n"]
    for e in events:
        lines.append(
            f"<b>{e['title']}</b> ({e['status']})\n"
            f"📜 {e['description']}\n"
            f"⚡ Multiplier: <b>{e['multiplier']}x</b> Boost\n"
        )

    lines.append("🎟️ <i>Earn Event Tokens from daily missions and games to spend in the upcoming festival shop!</i>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


HANDLERS = {
    "missions": cmd_missions,
    "mission": cmd_missions,
    "quests": cmd_missions,
    "quest": cmd_missions,
    "dailyquest": cmd_missions,
    "claimmission": cmd_claimmission,
    "claimquest": cmd_claimmission,
    "events": cmd_events,
    "event": cmd_events,
    "campaigns": cmd_events,
}
