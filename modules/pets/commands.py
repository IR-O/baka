from __future__ import annotations

import html
from telegram import Update
from telegram.ext import ContextTypes

from modules.pets.pet_catalog import PET_SPECIES_CATALOG
from modules.pets.pet_manager import PetManager


async def cmd_pets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pm = PetManager.get_instance()
    pets = pm.get_user_pets(user.id)

    if not pets:
        species_lines = []
        for k, s in PET_SPECIES_CATALOG.items():
            species_lines.append(
                f"• {s.rarity_badge} <b>{s.name}</b> (<code>{k}</code>) — ${s.cost_coins:,} coins"
                + (f" + {s.cost_gems} 💎" if s.cost_gems > 0 else "")
            )

        text = (
            f"🐾 <b>{html.escape(user.first_name)}, you don't have any pets yet!</b>\n\n"
            "Adopt a faithful companion to accompany you on quests and compete in pet arenas!\n\n"
            "✨ <b>Available Species to Adopt:</b>\n" + "\n".join(species_lines) + "\n\n"
            "🐾 <b>How to Adopt:</b> <code>/adoptpet &lt;species&gt; [custom_name]</code>\n"
            "Example: <code>/adoptpet fox Kurama</code>"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    lines = [f"🐾 <b>{html.escape(user.first_name)}'s Companion Kennel ({len(pets)})</b>\n"]
    for p in pets:
        evolve_tag = " [✨ EVOLVED]" if p["evolved"] else ""
        lines.append(
            f"{p['rarity_badge']} <b>{p['name']}</b> (Lv.<b>{p['level']}</b>){evolve_tag}\n"
            f"   ID: <code>{p['pet_id']}</code> | XP: {p['xp']}/{p['level']*100}\n"
            f"   🍖 Hunger: {p['hunger']}/100 | ❤️ Happiness: {p['happiness']}/100 | ⚡ Stamina: {p['stamina']}/100"
        )

    lines.append(
        "\n<b>🎮 Pet Commands:</b>\n"
        "• <code>/feedpet [id]</code> — Feed your pet ($100 coins)\n"
        "• <code>/playpet [id]</code> — Play games (+happiness, +XP)\n"
        "• <code>/trainpet [id]</code> — Train for levels and rewards\n"
        "• <code>/petevolve [id]</code> — Evolve at Lv.10 into divine form\n"
        "• <code>/petbattle [id]</code> — Enter pet championship"
    )
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_adoptpet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        species_list = ", ".join([f"<code>{k}</code>" for k in PET_SPECIES_CATALOG.keys()])
        await update.message.reply_text(
            f"🐾 <b>Usage:</b> <code>/adoptpet &lt;species&gt; [custom_name]</code>\n\n"
            f"Available species: {species_list}",
            parse_mode="HTML"
        )
        return

    species_id = args[0]
    custom_name = " ".join(args[1:]) if len(args) > 1 else None

    pm = PetManager.get_instance()
    ok, msg, _ = pm.adopt_pet(user.id, species_id, custom_name)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_feedpet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    pet_id = args[0] if args else None

    pm = PetManager.get_instance()
    ok, msg = pm.feed_pet(user.id, pet_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_playpet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    pet_id = args[0] if args else None

    pm = PetManager.get_instance()
    ok, msg = pm.play_with_pet(user.id, pet_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_trainpet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    pet_id = args[0] if args else None

    pm = PetManager.get_instance()
    ok, msg = pm.train_pet(user.id, pet_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_petevolve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    pet_id = args[0] if args else None

    pm = PetManager.get_instance()
    ok, msg = pm.evolve_pet(user.id, pet_id)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_petbattle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    pet_id = args[0] if args else None

    pm = PetManager.get_instance()
    ok, msg = pm.pet_competition(user.id, pet_id)
    await update.message.reply_text(msg, parse_mode="HTML")


HANDLERS = {
    "pets": cmd_pets,
    "mypets": cmd_pets,
    "pet": cmd_pets,
    "adoptpet": cmd_adoptpet,
    "adopt": cmd_adoptpet,
    "feedpet": cmd_feedpet,
    "feed": cmd_feedpet,
    "playpet": cmd_playpet,
    "play": cmd_playpet,
    "trainpet": cmd_trainpet,
    "train": cmd_trainpet,
    "petevolve": cmd_petevolve,
    "evolvepet": cmd_petevolve,
    "petbattle": cmd_petbattle,
    "petcontest": cmd_petbattle,
}
