from __future__ import annotations

import html
from telegram import Update
from telegram.ext import ContextTypes

from modules.houses.house_manager import HouseManager, HOUSE_TIERS, FURNITURE_CATALOG
from modules.utils.storage import get_user


async def cmd_house(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    hm = HouseManager.get_instance()
    house = hm.get_or_create_house(user.id)
    items = hm.get_house_items(user.id)

    furniture_summary = ""
    if items:
        furniture_lines = [f"• {html.escape(it['item_name'])} ({it['room']}) [+{it['comfort_bonus']} ✨]" for it in items[:6]]
        furniture_summary = "\n🛋️ <b>Featured Decor:</b>\n" + "\n".join(furniture_lines) + ("\n<i>...and more</i>" if len(items) > 6 else "")

    next_tier = HOUSE_TIERS.get(house["level"] + 1)
    upgrade_note = (
        f"\n\n⬆️ <b>Next Upgrade:</b> {next_tier.name}\n"
        f"Cost: ${next_tier.upgrade_coins:,} coins" + (f" + {next_tier.upgrade_gems} 💎" if next_tier.upgrade_gems > 0 else "") + "\n"
        "Use <code>/upgradehouse</code> to expand!"
        if next_tier else "\n\n🏛️ <b>Maximum Estate Tier Achieved!</b>"
    )

    text = (
        f"🏡 <b>{html.escape(user.first_name)}'s Virtual Estate</b>\n\n"
        f"🏠 <b>Dwelling:</b> {house['house_type']} (Tier {house['level']})\n"
        f"🚪 <b>Rooms:</b> {house['rooms_count']} chambers\n"
        f"✨ <b>Comfort Rating:</b> {house['comfort']}\n"
        f"🎨 <b>Decor Score:</b> {house['decor_score']}"
        f"{furniture_summary}"
        f"{upgrade_note}\n\n"
        "📜 <b>House Commands:</b>\n"
        "• <code>/furniture</code> — Browse furniture marketplace\n"
        "• <code>/buyfurniture &lt;item&gt;</code> — Purchase decor\n"
        "• <code>/upgradehouse</code> — Upgrade estate size\n"
        "• <code>/tophouses</code> — Estate leaderboards\n"
        "• <code>/visithouse &lt;user_id&gt;</code> — Tour another player's house"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_upgradehouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    hm = HouseManager.get_instance()
    ok, msg = hm.upgrade_house(user.id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_furniture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🛋️ <b>VIRTUAL HOME FURNITURE MARKETPLACE</b>\n"]
    for k, item in FURNITURE_CATALOG.items():
        cost_str = f"${item.cost_coins:,} coins" + (f" + {item.cost_gems} 💎" if item.cost_gems > 0 else "")
        lines.append(
            f"• <b>{item.name}</b>\n"
            f"   Key: <code>{k}</code> | Fits: <b>{item.room}</b>\n"
            f"   Bonus: +{item.comfort_bonus} Comfort | Price: {cost_str}"
        )

    lines.append("\n👉 <b>Purchase with:</b> <code>/buyfurniture &lt;key&gt;</code>\nExample: <code>/buyfurniture sofa</code>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_buyfurniture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("🛋️ Usage: <code>/buyfurniture &lt;item_key&gt;</code>\nBrowse catalog with <code>/furniture</code>", parse_mode="HTML")
        return

    item_key = args[0]
    hm = HouseManager.get_instance()
    ok, msg = hm.buy_furniture(user.id, item_key)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_visithouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    target_id = None
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target_id = update.message.reply_to_message.from_user.id
    elif args:
        try:
            target_id = int(args[0].replace("@", ""))
        except ValueError:
            await update.message.reply_text("⚠️ Please provide a valid User ID or reply to a user.")
            return

    if not target_id:
        await update.message.reply_text("🚪 Usage: <code>/visithouse &lt;user_id&gt;</code> or reply to a message with <code>/visithouse</code>", parse_mode="HTML")
        return

    target_ud = get_user(target_id)
    t_name = target_ud.get("display_name") or target_ud.get("username", f"User {target_id}")

    hm = HouseManager.get_instance()
    house = hm.get_or_create_house(target_id)
    items = hm.get_house_items(target_id)

    furniture_summary = ""
    if items:
        decor_lines = [f"• {html.escape(it['item_name'])} ({it['room']})" for it in items[:5]]
        furniture_summary = "\n🛋️ <b>Interior Showcase:</b>\n" + "\n".join(decor_lines)

    text = (
        f"🚪 <b>Visiting {html.escape(t_name)}'s Residence</b>\n\n"
        f"🏠 <b>Estate:</b> {house['house_type']} (Tier {house['level']})\n"
        f"🚪 <b>Rooms:</b> {house['rooms_count']}\n"
        f"✨ <b>Comfort Rating:</b> {house['comfort']}\n"
        f"🎨 <b>Decor Score:</b> {house['decor_score']}"
        f"{furniture_summary}\n\n"
        f"<i>{html.escape(user.first_name)} left a guest sign in the visitor logbook! ✍️</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_tophouses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hm = HouseManager.get_instance()
    houses = hm.get_top_houses(limit=10)

    if not houses:
        await update.message.reply_text("🏡 No virtual estates registered yet. Visit yours with <code>/house</code>!", parse_mode="HTML")
        return

    lines = ["🏆 <b>LUXURY ESTATE LEADERBOARD</b>\n"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for h in houses:
        m = medals[h["rank"] - 1] if h["rank"] <= len(medals) else f"{h['rank']}."
        lines.append(
            f"{m} <b>{html.escape(h['owner_name'])}</b>\n"
            f"   {h['house_type']} | ✨ Comfort: <b>{h['comfort']}</b> | Decor: {h['decor_score']}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


HANDLERS = {
    "house": cmd_house,
    "myhouse": cmd_house,
    "estate": cmd_house,
    "upgradehouse": cmd_upgradehouse,
    "expandhouse": cmd_upgradehouse,
    "furniture": cmd_furniture,
    "furniturecatalog": cmd_furniture,
    "buyfurniture": cmd_buyfurniture,
    "visithouse": cmd_visithouse,
    "tophouses": cmd_tophouses,
    "houserank": cmd_tophouses,
}
