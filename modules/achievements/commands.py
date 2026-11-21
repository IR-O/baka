from __future__ import annotations

import html
from telegram import Update
from telegram.ext import ContextTypes

from modules.achievements.achievement_manager import AchievementManager


async def cmd_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    am = AchievementManager.get_instance()
    data = am.get_user_achievements(user.id)

    lines = [
        f"🏆 <b>{html.escape(user.first_name)}'s Hall of Trophies</b>",
        f"Unlocked: <b>{data['total_unlocked']} / {data['total_available']}</b> achievements\n",
    ]

    if data["unlocked"]:
        lines.append("✨ <b>Completed Achievements:</b>")
        for u in data["unlocked"]:
            lines.append(f"• <b>{u['title']}</b> ({u['category']}) — <i>{u['description']}</i>")
        lines.append("")

    if data["in_progress"]:
        lines.append("⏳ <b>In Progress:</b>")
        for p in data["in_progress"][:6]:
            pct = int((p["progress"] / p["max_progress"]) * 100) if p["max_progress"] > 0 else 0
            lines.append(f"• <b>{p['title']}</b> ({p['category']}): {p['progress']}/{p['max_progress']} ({pct}%)")
        if len(data["in_progress"]) > 6:
            lines.append(f"<i>...and {len(data['in_progress']) - 6} more in progress</i>")

    if data["hidden_locked_count"] > 0:
        lines.append(f"\n🔒 <i>{data['hidden_locked_count']} Secret Achievement(s) remaining to discover!</i>")

    lines.append("\n👉 View global leaders with <code>/topachievers</code>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_topachievers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    am = AchievementManager.get_instance()
    leaders = am.get_leaderboard(limit=10)

    if not leaders:
        await update.message.reply_text("🏆 No achievements unlocked yet! Be the first with <code>/achievements</code>.", parse_mode="HTML")
        return

    lines = ["🏆 <b>GLOBAL TROPHY LEADERBOARD</b>\n"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for l in leaders:
        m = medals[l["rank"] - 1] if l["rank"] <= len(medals) else f"{l['rank']}."
        lines.append(f"{m} <b>{html.escape(l['name'])}</b> — <b>{l['count']}</b> trophies 🎖️")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


HANDLERS = {
    "achievements": cmd_achievements,
    "achievement": cmd_achievements,
    "achieve": cmd_achievements,
    "badges": cmd_achievements,
    "trophies": cmd_achievements,
    "topachievers": cmd_topachievers,
    "achieverank": cmd_topachievers,
}
