from __future__ import annotations

import html
from telegram import Update
from telegram.ext import ContextTypes

from modules.management.admin_dashboard import AdminDashboard


async def cmd_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    ad = AdminDashboard.get_instance()
    if not ad.is_authorized(caller.id):
        await update.message.reply_text("🚫 Unauthorized. Verified Admin ID required.")
        return

    data = ad.get_system_overview()
    status_str = "🔴 Active (Restricted)" if data["maintenance_mode"] else "🟢 Normal"

    text = (
        "📊 <b>MIKO PLATFORM MASTER DASHBOARD</b>\n\n"
        f"👥 <b>Registered Users:</b> <b>{data['total_users']:,}</b>\n"
        f"👑 <b>VIP Premium Subscriptions:</b> <b>{data['premium_users']:,}</b>\n"
        f"💰 <b>Total Circulating Coins:</b> <b>${data['total_coins']:,}</b>\n"
        f"💎 <b>Total Circulating Gems:</b> <b>{data['total_gems']} 💎</b>\n"
        f"💳 <b>Total Wallet Transactions:</b> <b>{data['total_transactions']:,}</b>\n"
        f"🎮 <b>Active/Logged Game Sessions:</b> <b>{data['total_game_sessions']:,}</b>\n"
        f"🏰 <b>Active Clans & Guilds:</b> <b>{data['total_guilds']}</b>\n"
        f"🐾 <b>Adopted Virtual Pets:</b> <b>{data['total_pets']}</b>\n"
        f"🛠️ <b>Maintenance Mode:</b> {status_str}\n\n"
        "⚡ <b>Admin Quick Actions:</b>\n"
        "• <code>/eco_give &lt;uid&gt; &lt;amt&gt; [gems]</code>\n"
        "• <code>/eco_take &lt;uid&gt; &lt;amt&gt; [gems]</code>\n"
        "• <code>/eco_set &lt;uid&gt; &lt;amt&gt; [gems]</code>\n"
        "• <code>/admin_warn &lt;uid&gt; &lt;reason&gt;</code>\n"
        "• <code>/admin_ban &lt;uid&gt; &lt;reason&gt;</code>\n"
        "• <code>/admin_unban &lt;uid&gt;</code>\n"
        "• <code>/admin_reports</code>\n"
        "• <code>/maintenance &lt;on|off&gt;</code>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_admin_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("⚠️ Usage: <code>/admin_warn &lt;user_id&gt; [reason]</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a numeric Telegram User ID.")
        return

    reason = " ".join(args[1:]) if len(args) > 1 else "Violation of game rules"
    ad = AdminDashboard.get_instance()
    ok, msg = ad.warn_user(caller.id, target_id, reason)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("⚠️ Usage: <code>/admin_ban &lt;user_id&gt; [reason]</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a numeric Telegram User ID.")
        return

    reason = " ".join(args[1:]) if len(args) > 1 else "Permanent administrative ban"
    ad = AdminDashboard.get_instance()
    ok, msg = ad.ban_user(caller.id, target_id, reason)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("⚠️ Usage: <code>/admin_unban &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a numeric Telegram User ID.")
        return

    ad = AdminDashboard.get_instance()
    ok, msg = ad.unban_user(caller.id, target_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_admin_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    ad = AdminDashboard.get_instance()
    if not ad.is_authorized(caller.id):
        await update.message.reply_text("🚫 Unauthorized.")
        return

    reports = ad.get_recent_reports(limit=5)
    if not reports:
        await update.message.reply_text("🛡️ No player reports on file.")
        return

    lines = ["🚨 <b>RECENT PLAYER REPORTS</b>\n"]
    for r in reports:
        lines.append(
            f"• <b>Report #{r['id']}</b> ({r['created_at']})\n"
            f"   Reporter: <code>{r['reporter_id']}</code> | Target: <code>{r['reported_id']}</code>\n"
            f"   Reason: <i>{html.escape(r['reason'])}</i>"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_eco_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: <code>/eco_give &lt;user_id&gt; &lt;amount&gt; [gems]</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
        amt = float(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid ID or amount.")
        return

    curr = "gems" if len(args) > 2 and "gem" in args[2].lower() else "coins"
    ad = AdminDashboard.get_instance()
    ok, msg = ad.eco_modify(caller.id, target_id, "give", amt, curr)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_eco_take(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: <code>/eco_take &lt;user_id&gt; &lt;amount&gt; [gems]</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
        amt = float(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid ID or amount.")
        return

    curr = "gems" if len(args) > 2 and "gem" in args[2].lower() else "coins"
    ad = AdminDashboard.get_instance()
    ok, msg = ad.eco_modify(caller.id, target_id, "take", amt, curr)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_eco_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: <code>/eco_set &lt;user_id&gt; &lt;amount&gt; [gems]</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
        amt = float(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid ID or amount.")
        return

    curr = "gems" if len(args) > 2 and "gem" in args[2].lower() else "coins"
    ad = AdminDashboard.get_instance()
    ok, msg = ad.eco_modify(caller.id, target_id, "set", amt, curr)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user
    args = context.args or []
    if not args:
        ad = AdminDashboard.get_instance()
        st = "ON" if ad.is_maintenance() else "OFF"
        await update.message.reply_text(f"🛠️ Maintenance mode is currently <b>{st}</b>. Toggle with: <code>/maintenance on</code> or <code>/maintenance off</code>", parse_mode="HTML")
        return

    state = args[0].lower() in ("on", "enable", "true", "1")
    ad = AdminDashboard.get_instance()
    ok, msg = ad.set_maintenance(caller.id, state)
    await update.message.reply_text(msg, parse_mode="HTML")


HANDLERS = {
    "dashboard": cmd_dashboard,
    "adminstats": cmd_dashboard,
    "admin_warn": cmd_admin_warn,
    "admin_ban": cmd_admin_ban,
    "admin_unban": cmd_admin_unban,
    "admin_reports": cmd_admin_reports,
    "eco_give": cmd_eco_give,
    "eco_take": cmd_eco_take,
    "eco_set": cmd_eco_set,
    "maintenance": cmd_maintenance,
}
