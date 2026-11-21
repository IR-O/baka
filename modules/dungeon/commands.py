from __future__ import annotations

import html
from telegram import Update
from telegram.ext import ContextTypes

from modules.dungeon.dungeon_engine import DungeonEngine
from modules.dungeon.dungeon_catalog import DUNGEON_LOCATIONS, WEAPONS_CATALOG, ARMOR_CATALOG


async def cmd_dungeon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    engine = DungeonEngine.get_instance()

    if not args:
        lines = [
            "⚔️ <b>MIKO RPG DUNGEON EXPEDITIONS</b>\n",
            "<i>Descend into treacherous ruins to slay beasts and harvest rare relics!</i>\n",
        ]
        for loc_id, loc in DUNGEON_LOCATIONS.items():
            lines.append(
                f"{loc['emoji']} <b>{loc['name']}</b> [Lv.{loc['min_level']}+ • {loc['difficulty']}]\n"
                f"   🏰 Floors: <b>{loc['max_floors']}</b> | Boss: <b>{loc['boss']['name']}</b>\n"
                f"   🎁 Clear Loot: <b>${loc['boss']['coin_reward']:,}</b> + {loc['boss']['gem_reward']} 💎\n"
                f"   👉 Enter: <code>/dungeon {loc_id}</code>\n"
            )
        lines.append("🛡️ <b>Controls:</b>\n• <code>/explore</code> — Advance room\n• <code>/attack</code> — Strike enemy\n• <code>/potion</code> — Heal\n• <code>/dstats</code> — Character sheet")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return

    dungeon_id = args[0].lower().strip()
    ok, msg, run = engine.start_run(user.id, dungeon_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_dstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    engine = DungeonEngine.get_instance()
    prof = engine.get_or_create_rpg_profile(user.id)
    eff = engine.get_effective_stats(prof)

    active_run = engine.get_active_run(user.id)
    status_str = f"🏰 Exploring <b>{active_run['name']}</b> (Floor {active_run['floor']}/{active_run['max_floors']})" if active_run else "🏘️ Resting in Town"

    text = (
        f"🛡️ <b>{html.escape(user.first_name)}'s RPG Adventurer Stats:</b>\n\n"
        f"📍 Status: {status_str}\n"
        f"🟤 Level: <b>{prof['level']}</b>\n"
        f"❤️ HP: <b>{prof['hp']} / {eff['max_hp']}</b>\n"
        f"⚔️ Attack Power: <b>{eff['atk']}</b>\n"
        f"🛡️ Defense Rating: <b>{eff['def']}</b>\n"
        f"⚡ Speed: <b>{eff['spd']}</b>\n\n"
        f"🗡️ Equipped Weapon: <b>{prof['weapon']}</b>\n"
        f"🛡️ Equipped Armor: <b>{prof['armor']}</b>\n"
        f"🧪 Potions in Pouch: <b>{prof['potions']}</b>\n"
        f"🏆 Bosses Slain: <b>{prof['completed_floors']}</b>\n\n"
        "💡 <i>Discover new weapons in dungeons or equip with <code>/equip &lt;item_name&gt;</code>!</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_explore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    engine = DungeonEngine.get_instance()
    ok, msg, _ = engine.explore_floor(user.id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    engine = DungeonEngine.get_instance()
    ok, msg, _ = engine.attack_enemy(user.id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_potion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    engine = DungeonEngine.get_instance()
    ok, msg = engine.use_potion(user.id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_flee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    engine = DungeonEngine.get_instance()
    ok, msg = engine.flee_dungeon(user.id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_equip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        avail_w = ", ".join(WEAPONS_CATALOG.keys())
        avail_a = ", ".join(ARMOR_CATALOG.keys())
        await update.message.reply_text(
            f"🗡️ Usage: <code>/equip &lt;item name&gt;</code>\n\n"
            f"<b>Weapons:</b> {avail_w}\n"
            f"<b>Armor:</b> {avail_a}",
            parse_mode="HTML"
        )
        return

    item_name = " ".join(args).strip()
    engine = DungeonEngine.get_instance()
    ok, msg = engine.equip_gear(user.id, item_name)
    await update.message.reply_text(msg, parse_mode="HTML")


HANDLERS = {
    "dungeon": cmd_dungeon,
    "dstats": cmd_dstats,
    "dungeonstatus": cmd_dstats,
    "explore": cmd_explore,
    "crawl": cmd_explore,
    "attack": cmd_attack,
    "potion": cmd_potion,
    "drink": cmd_potion,
    "flee": cmd_flee,
    "equip": cmd_equip,
}
