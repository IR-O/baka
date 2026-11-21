from __future__ import annotations

import html
from telegram import Update
from telegram.ext import ContextTypes

from modules.guilds.guild_manager import GuildManager
from modules.utils.storage import get_user


async def cmd_guild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ud = get_user(user.id)
    guild_id = ud.get("guild_id")
    gm = GuildManager.get_instance()

    if not guild_id:
        text = (
            f"🏰 <b>{html.escape(user.first_name)}, you are not in a Guild!</b>\n\n"
            "Unite with fellow adventurers to unlock clan wars and shared treasury perks!\n\n"
            "✨ <b>Guild Commands:</b>\n"
            "• <code>/createguild &lt;tag&gt; &lt;name&gt;</code> — Found a new Guild ($25,000 coins, Lv.5+)\n"
            "• <code>/joinguild &lt;tag&gt;</code> — Join an existing Guild\n"
            "• <code>/topguilds</code> — View the highest ranking Guilds"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    guild = gm.get_guild(guild_id)
    if not guild:
        await update.message.reply_text("⚠️ Guild record not found.")
        return

    text = (
        f"🏰 <b>{guild['name']} [{guild['tag']}]</b>\n\n"
        f"👑 Leader ID: <code>{guild['leader_id']}</code>\n"
        f"🟤 Guild Level: <b>{guild['level']}</b> ({guild['xp']:,} XP)\n"
        f"👥 Members: <b>{guild['member_count']} / {guild['max_members']}</b>\n"
        f"🏦 Treasury: <b>${guild['treasury_coins']:,} coins</b> | <b>{guild['treasury_gems']} 💎</b>\n\n"
        "📜 <b>Guild Actions:</b>\n"
        "• <code>/depositguild &lt;amount&gt;</code> — Donate to treasury\n"
        "• <code>/leaveguild</code> — Leave this guild\n"
        "• <code>/topguilds</code> — Guild rankings"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_createguild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("🏰 Usage: <code>/createguild &lt;TAG&gt; &lt;Guild Name&gt;</code>\nExample: <code>/createguild TITAN Titan Vanguard</code>", parse_mode="HTML")
        return

    tag = args[0]
    name = " ".join(args[1:])
    gm = GuildManager.get_instance()
    ok, msg, _ = gm.create_guild(user.id, tag, name)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_joinguild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("🏰 Usage: <code>/joinguild &lt;TAG&gt;</code>", parse_mode="HTML")
        return

    tag = args[0]
    gm = GuildManager.get_instance()
    ok, msg = gm.join_guild(user.id, tag)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_leaveguild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    gm = GuildManager.get_instance()
    ok, msg = gm.leave_guild(user.id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_depositguild(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("🏦 Usage: <code>/depositguild &lt;amount&gt; [gems]</code>", parse_mode="HTML")
        return

    try:
        amount = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number.")
        return

    currency = "gems" if len(args) > 1 and "gem" in args[1].lower() else "coins"
    gm = GuildManager.get_instance()
    ok, msg = gm.deposit_treasury(user.id, amount, currency=currency)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_topguilds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gm = GuildManager.get_instance()
    guilds = gm.get_top_guilds(limit=10)

    if not guilds:
        await update.message.reply_text("🏰 No guilds have been founded yet! Be the first with <code>/createguild</code>.", parse_mode="HTML")
        return

    lines = ["🏆 <b>TOP 10 GUILD RANKINGS</b>\n"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for g in guilds:
        m = medals[g["rank"] - 1] if g["rank"] <= len(medals) else f"{g['rank']}."
        lines.append(
            f"{m} <b>{g['name']} [{g['tag']}]</b>\n"
            f"   Level <b>{g['level']}</b> | 👥 {g['member_count']} members | Treasury: ${g['treasury_coins']:,}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


HANDLERS = {
    "guild": cmd_guild,
    "clan": cmd_guild,
    "createguild": cmd_createguild,
    "createclan": cmd_createguild,
    "joinguild": cmd_joinguild,
    "joinclan": cmd_joinguild,
    "leaveguild": cmd_leaveguild,
    "leaveclan": cmd_leaveguild,
    "depositguild": cmd_depositguild,
    "topguilds": cmd_topguilds,
    "guildrank": cmd_topguilds,
}
