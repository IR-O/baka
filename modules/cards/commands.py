from __future__ import annotations

import html
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from modules.cards.card_manager import CardManager
from modules.cards.card_catalog import PACK_DEFINITIONS, CARDS_CATALOG, CardRarity


async def cmd_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cm = CardManager.get_instance()
    cards = cm.get_user_cards(user.id)

    if not cards:
        text = (
            f"🃏 <b>{html.escape(user.first_name)}'s Card Collection:</b>\n\n"
            "You have not unlocked any trading cards yet!\n"
            "🛒 Browse card packs using: <code>/packs</code>\n"
            "✨ Open a Bronze Pack for $1,500 coins: <code>/openpack bronze</code>"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    total_cards = sum(c["count"] for c in cards)
    unique_cards = len(cards)
    catalog_total = len(CARDS_CATALOG)
    comp_pct = round((unique_cards / catalog_total) * 100, 1)

    lines = [
        f"🃏 <b>{html.escape(user.first_name)}'s Card Deck ({unique_cards}/{catalog_total} Unique • {comp_pct}%):</b>\n",
        f"📊 Total Cards Owned: <b>{total_cards}</b>\n",
    ]

    for c in cards[:15]:
        qty = f" (x{c['count']})" if c['count'] > 1 else ""
        lines.append(
            f"{c['rarity_color']} <b>{c['name']}</b> [Lv.{c['level']}]{qty} — <code>{c['card_id']}</code>\n"
            f"   ⚔️ ATK: {c['attack']} | 🛡️ DEF: {c['defense']} | ❤️ HP: {c['hp']} | {c['element']}"
        )

    if len(cards) > 15:
        lines.append(f"\n<i>...and {len(cards) - 15} more cards.</i>")

    lines.append("\n💡 <b>Commands:</b>\n• <code>/upgradecard &lt;card_id&gt;</code> — Boost card stats\n• <code>/cardduel &lt;card_id&gt;</code> — Battle in the arena\n• <code>/giftcard &lt;card_id&gt;</code> — Gift to replied user")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_cardpacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [
        "📦 <b>COLLECTIBLE CARD PACKS</b>\n",
        "<i>Unlock mythical beings, elemental dragons, and legendary heroes!</i>\n",
    ]
    for pack_id, pack in PACK_DEFINITIONS.items():
        gems_txt = f" / {pack['cost_gems']} 💎" if pack['cost_gems'] > 0 else ""
        lines.append(
            f"{pack['emoji']} <b>{pack['name']}</b> (<code>{pack_id}</code>)\n"
            f"   💵 Price: <b>${pack['cost_coins']:,} coins</b>{gems_txt}\n"
            f"   🎴 Contains: <b>{pack['card_count']} cards</b>\n"
            f"   👉 To open: <code>/openpack {pack_id}</code>\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_opencardpack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("📦 Usage: <code>/openpack &lt;bronze|silver|gold|mythic&gt;</code>\nSee available packs at /packs", parse_mode="HTML")
        return

    pack_type = args[0].lower().strip()
    cm = CardManager.get_instance()
    ok, msg, drawn_cards = cm.open_pack(user.id, pack_type)

    if not ok:
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    lines = [f"{msg}\n\n<b>🃏 Cards Obtained:</b>\n"]
    for c in drawn_cards:
        color = CardRarity.COLORS.get(c["rarity"], "⚪")
        lines.append(
            f"{color} <b>{c['name']}</b> [{c['rarity']}]\n"
            f"   ⚔️ ATK: {c['attack']} | 🛡️ DEF: {c['defense']} | ❤️ HP: {c['hp']} | {c['element']}\n"
            f"   <i>\"{c['description']}\"</i>\n"
        )

    lines.append("✨ <i>All cards have been added to your deck! Check /cards</i>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_upgradecard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("⚡ Usage: <code>/upgradecard &lt;card_id&gt;</code>\nCheck your card IDs at /cards", parse_mode="HTML")
        return

    card_id = args[0].strip()
    cm = CardManager.get_instance()
    ok, msg = cm.upgrade_card(user.id, card_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_giftcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user:
        await update.message.reply_text("🎁 Reply to the friend you want to gift a card to:\n<code>/giftcard &lt;card_id&gt;</code>", parse_mode="HTML")
        return

    args = context.args or []
    if not args:
        await update.message.reply_text("🎁 Usage: Reply + <code>/giftcard &lt;card_id&gt;</code>", parse_mode="HTML")
        return

    receiver = update.message.reply_to_message.from_user
    card_id = args[0].strip()
    cm = CardManager.get_instance()
    ok, msg = cm.gift_card(user.id, receiver.id, card_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_cardduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("⚔️ Usage: <code>/cardduel &lt;card_id&gt;</code>\nSend your card into battle against an arena challenger!", parse_mode="HTML")
        return

    card_id = args[0].strip()
    cm = CardManager.get_instance()
    duel = cm.simulate_card_duel(user.id, card_id, user_b_id=0)

    if "error" in duel:
        await update.message.reply_text(f"❌ {duel['error']}")
        return

    card_a = duel["card_a"]
    card_b = duel["card_b"]
    is_win = duel["winner_a"]

    header = (
        f"⚔️ <b>CARD BATTLE ARENA</b>\n\n"
        f"🔵 <b>Your Champion:</b> {card_a['rarity_color']} {card_a['name']} (Lv.{card_a['level']})\n"
        f"🔴 <b>Challenger:</b> {card_b['rarity_color']} {card_b['name']} (Lv.{card_b['level']})\n\n"
        f"<b>📜 Battle Transcript:</b>\n"
    )

    battle_body = "\n".join(duel["battle_log"][:6])
    result_str = (
        f"\n\n🎉 <b>VICTORY!</b> Your {card_a['name']} overpowered the enemy!\n"
        f"🎁 Reward: +${duel['rewards']['coins']} coins, +{duel['rewards']['xp']} XP!"
        if is_win else
        f"\n\n💀 <b>DEFEAT!</b> Your card was vanquished. Better luck next time!\n"
        f"🎁 Consolation: +${duel['rewards']['coins']} coins, +{duel['rewards']['xp']} XP."
    )

    await update.message.reply_text(header + battle_body + result_str, parse_mode="HTML")


HANDLERS = {
    "cards": cmd_cards,
    "cardcollection": cmd_cards,
    "packs": cmd_cardpacks,
    "cardpacks": cmd_cardpacks,
    "openpack": cmd_opencardpack,
    "opencardpack": cmd_opencardpack,
    "upgradecard": cmd_upgradecard,
    "giftcard": cmd_giftcard,
    "cardduel": cmd_cardduel,
}
