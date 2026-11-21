from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import (
    get_user,
    update_user,
    get_all_users,
    atomic_add_balance,
    atomic_deduct_balance,
    atomic_transfer_balance,
    add_xp_with_limits,
    _STORAGE_LOCK,
)
from modules.utils.db import (
    log_transaction,
    get_transaction_history,
    log_admin_action,
    _get_conn,
)

# === VIRTUAL MARKETPLACE ITEMS CATALOG ===
MARKETPLACE_CATALOG: Dict[str, Dict[str, Any]] = {
    "health_potion": {
        "id": "health_potion",
        "name": "Health Potion",
        "emoji": "🧪",
        "category": "consumable",
        "buy_price": 500,
        "sell_price": 350,
        "description": "Restores 50 HP in dungeon RPG battles.",
    },
    "elixir_vitality": {
        "id": "elixir_vitality",
        "name": "Elixir of Vitality",
        "emoji": "🍷",
        "category": "consumable",
        "buy_price": 1200,
        "sell_price": 840,
        "description": "Restores 150 HP and cures negative battle effects.",
    },
    "xp_booster": {
        "id": "xp_booster",
        "name": "XP Booster Charm",
        "emoji": "⚡",
        "category": "booster",
        "buy_price": 2500,
        "sell_price": 1750,
        "description": "Grants +50% bonus XP for the next 24 hours.",
    },
    "coin_magnet": {
        "id": "coin_magnet",
        "name": "Coin Magnet",
        "emoji": "🧲",
        "category": "booster",
        "buy_price": 3000,
        "sell_price": 2100,
        "description": "Grants +25% bonus coins from all mini games for 24 hours.",
    },
    "thief_ward": {
        "id": "thief_ward",
        "name": "Thief's Ward",
        "emoji": "🧿",
        "category": "protection",
        "buy_price": 4000,
        "sell_price": 2800,
        "description": "Reduces coins lost from robberies by 50% for 3 days.",
    },
    "lucky_clover": {
        "id": "lucky_clover",
        "name": "Four-Leaf Clover",
        "emoji": "🍀",
        "category": "luck",
        "buy_price": 5000,
        "sell_price": 3500,
        "description": "Increases card pack rare drop rates by 15%.",
    },
}


class EconomyEngine:
    _instance: Optional[EconomyEngine] = None

    @classmethod
    def get_instance(cls) -> EconomyEngine:
        if cls._instance is None:
            cls._instance = EconomyEngine()
        return cls._instance

    # --- REWARD SYSTEMS ---

    def claim_daily_reward(self, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        with _STORAGE_LOCK:
            ud = get_user(user_id)
            now = datetime.now()
            last_daily_str = ud.get("last_daily")

            streak = ud.get("daily_streak", 1)
            if last_daily_str:
                last_daily = datetime.fromisoformat(last_daily_str)
                elapsed = now - last_daily
                if elapsed < timedelta(hours=24):
                    remaining = timedelta(hours=24) - elapsed
                    hrs, rem = divmod(int(remaining.total_seconds()), 3600)
                    mins, _ = divmod(rem, 60)
                    return False, f"⏳ You have already claimed your daily reward! Next claim in {hrs}h {mins}m.", {}
                elif elapsed < timedelta(hours=48):
                    streak += 1
                else:
                    streak = 1
            else:
                streak = 1

            # Base rewards + streak bonus (up to 7 days multiplier)
            multiplier = min(2.0, 1.0 + (streak - 1) * 0.15)
            base_coins = 5000 if ud.get("premium") else 2000
            coins_reward = int(base_coins * multiplier)
            xp_reward = int((200 if ud.get("premium") else 50) * multiplier)
            event_tokens = 5 if streak >= 3 else 0

            atomic_add_balance(user_id, coins_reward, currency="coins", reason=f"Daily Reward (Streak {streak})")
            if event_tokens > 0:
                atomic_add_balance(user_id, event_tokens, currency="event_tokens", reason=f"Daily Streak Bonus")
            add_xp_with_limits(user_id, xp_reward, reason="daily_claim")

            update_user(user_id, last_daily=now.isoformat(), daily_streak=streak, status="alive")

            rewards = {
                "coins": coins_reward,
                "xp": xp_reward,
                "event_tokens": event_tokens,
                "streak": streak,
            }
            return True, f"🎁 Claimed Day {streak} reward! +${coins_reward:,} coins, +{xp_reward} XP, +{event_tokens} tokens.", rewards

    def claim_weekly_reward(self, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        with _STORAGE_LOCK:
            ud = get_user(user_id)
            now = datetime.now()
            last_weekly = ud.get("weekly_rewards_claimed")

            if last_weekly:
                last_dt = datetime.fromisoformat(last_weekly)
                if now - last_dt < timedelta(days=7):
                    remaining = timedelta(days=7) - (now - last_dt)
                    days = remaining.days
                    hrs = remaining.seconds // 3600
                    return False, f"⏳ Weekly reward already claimed! Next available in {days}d {hrs}h.", {}

            coins = 15000 if ud.get("premium") else 8000
            gems = 1.0 if ud.get("premium") else 0.5
            event_tokens = 25
            xp = 500

            atomic_add_balance(user_id, coins, currency="coins", reason="Weekly Bonus")
            atomic_add_balance(user_id, gems, currency="gems", reason="Weekly Bonus")
            atomic_add_balance(user_id, event_tokens, currency="event_tokens", reason="Weekly Bonus")
            add_xp_with_limits(user_id, xp, reason="weekly_claim")

            update_user(user_id, weekly_rewards_claimed=now.isoformat())
            rewards = {"coins": coins, "gems": gems, "event_tokens": event_tokens, "xp": xp}
            return True, f"🌟 Weekly reward claimed! +${coins:,} coins, +{gems} gems, +{event_tokens} tokens, +{xp} XP!", rewards

    def claim_monthly_reward(self, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        with _STORAGE_LOCK:
            ud = get_user(user_id)
            now = datetime.now()
            last_monthly = ud.get("monthly_rewards_claimed")

            if last_monthly:
                last_dt = datetime.fromisoformat(last_monthly)
                if now - last_dt < timedelta(days=30):
                    remaining = timedelta(days=30) - (now - last_dt)
                    days = remaining.days
                    return False, f"⏳ Monthly reward already claimed! Next available in {days} days.", {}

            coins = 50000 if ud.get("premium") else 25000
            gems = 5.0 if ud.get("premium") else 2.0
            event_tokens = 100
            prem_tokens = 1 if ud.get("premium") else 0
            xp = 2000

            atomic_add_balance(user_id, coins, currency="coins", reason="Monthly Mega Bonus")
            atomic_add_balance(user_id, gems, currency="gems", reason="Monthly Mega Bonus")
            atomic_add_balance(user_id, event_tokens, currency="event_tokens", reason="Monthly Mega Bonus")
            if prem_tokens > 0:
                atomic_add_balance(user_id, prem_tokens, currency="premium_tokens", reason="Monthly VIP Token")
            add_xp_with_limits(user_id, xp, reason="monthly_claim")

            update_user(user_id, monthly_rewards_claimed=now.isoformat())
            rewards = {"coins": coins, "gems": gems, "event_tokens": event_tokens, "premium_tokens": prem_tokens, "xp": xp}
            return True, f"👑 Monthly Mega reward claimed! +${coins:,} coins, +{gems} gems, +{event_tokens} tokens, +{xp} XP!", rewards

    # --- REFERRAL SYSTEM ---

    def process_referral(self, invitee_id: int, referral_code: str) -> Tuple[bool, str]:
        with _STORAGE_LOCK:
            invitee = get_user(invitee_id)
            if invitee.get("referred_by"):
                return False, "You have already used a referral code!"

            code = referral_code.strip().upper()
            if not code.startswith("REF") or not code[3:].isdigit():
                return False, "Invalid referral code format. Example: REF12345678"

            inviter_id = int(code[3:])
            if inviter_id == invitee_id:
                return False, "You cannot refer yourself!"

            inviter = get_user(inviter_id)
            if not inviter:
                return False, "Referral code owner does not exist."

            # Reward both players
            REWARD_COINS = 5000
            REWARD_XP = 150
            REWARD_TOKENS = 10

            atomic_add_balance(invitee_id, REWARD_COINS, currency="coins", reason=f"Referral bonus from {inviter_id}")
            atomic_add_balance(inviter_id, REWARD_COINS, currency="coins", reason=f"Referral reward for inviting {invitee_id}")

            atomic_add_balance(invitee_id, REWARD_TOKENS, currency="event_tokens", reason="Referral tokens")
            atomic_add_balance(inviter_id, REWARD_TOKENS, currency="event_tokens", reason="Referral tokens")

            add_xp_with_limits(invitee_id, REWARD_XP, reason="referral_bonus")
            add_xp_with_limits(inviter_id, REWARD_XP, reason="referral_reward")

            update_user(invitee_id, referred_by=inviter_id)
            inviter_referrals = inviter.get("referrals_count", 0) + 1
            update_user(inviter_id, referrals_count=inviter_referrals)

            return True, f"🎉 Referral code applied! Both you and your friend received ${REWARD_COINS:,} coins and {REWARD_TOKENS} tokens!"

    # --- MARKETPLACE & INVENTORY ---

    def buy_item(self, user_id: int, item_id: str, count: int = 1) -> Tuple[bool, str]:
        if item_id not in MARKETPLACE_CATALOG:
            return False, f"Unknown item '{item_id}'. Check /marketplace to see available items."
        if count <= 0:
            return False, "Purchase quantity must be at least 1."

        item = MARKETPLACE_CATALOG[item_id]
        total_cost = item["buy_price"] * count

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            if ud.get("balance", 0) < total_cost:
                return False, f"Insufficient coins! Need ${total_cost:,}, you have ${ud.get('balance', 0):,}."

            if not atomic_deduct_balance(user_id, total_cost, currency="coins", reason=f"Bought {count}x {item['name']}"):
                return False, "Transaction failed."

            inventory = dict(ud.get("inventory") or {})
            inventory[item_id] = inventory.get(item_id, 0) + count
            update_user(user_id, inventory=inventory)
            return True, f"🛒 Purchased {count}x {item['emoji']} <b>{item['name']}</b> for ${total_cost:,} coins!"

    def sell_item(self, user_id: int, item_id: str, count: int = 1) -> Tuple[bool, str]:
        if item_id not in MARKETPLACE_CATALOG:
            return False, f"Unknown item '{item_id}'."
        if count <= 0:
            return False, "Quantity must be at least 1."

        item = MARKETPLACE_CATALOG[item_id]

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            inventory = dict(ud.get("inventory") or {})
            owned = inventory.get(item_id, 0)
            if owned < count:
                return False, f"You only have {owned}x of {item['name']}."

            inventory[item_id] = owned - count
            if inventory[item_id] <= 0:
                del inventory[item_id]

            total_gain = item["sell_price"] * count
            atomic_add_balance(user_id, total_gain, currency="coins", reason=f"Sold {count}x {item['name']}")
            update_user(user_id, inventory=inventory)
            return True, f"💰 Sold {count}x {item['emoji']} <b>{item['name']}</b> for ${total_gain:,} coins!"

    def get_inventory(self, user_id: int) -> Dict[str, Any]:
        ud = get_user(user_id)
        raw_inv = ud.get("inventory") or {}
        detailed: List[Dict[str, Any]] = []
        for item_id, count in raw_inv.items():
            info = MARKETPLACE_CATALOG.get(item_id, {
                "id": item_id,
                "name": item_id.replace("_", " ").title(),
                "emoji": "📦",
                "category": "misc",
                "description": "Inventory item",
            })
            detailed.append({**info, "count": count})
        return {"items": detailed, "raw": raw_inv}

    # --- ECONOMY METRICS & ADMIN CONTROLS ---

    def calculate_economy_metrics(self) -> Dict[str, Any]:
        users = get_all_users()
        total_users = len(users)
        total_coins = sum(int(u.get("balance", 0)) for u in users.values())
        total_gems = sum(float(u.get("gems", 0.0) or 0.0) for u in users.values())
        total_event_tokens = sum(int(u.get("event_tokens", 0)) for u in users.values())
        total_prem_tokens = sum(int(u.get("premium_tokens", 0)) for u in users.values())
        total_kills = sum(int(u.get("kills", 0)) for u in users.values())
        total_robs = sum(int(u.get("robs", 0)) for u in users.values())
        avg_coins = int(total_coins / max(1, total_users))

        return {
            "total_users": total_users,
            "total_coins": total_coins,
            "total_gems": round(total_gems, 2),
            "total_event_tokens": total_event_tokens,
            "total_prem_tokens": total_prem_tokens,
            "total_kills": total_kills,
            "total_robs": total_robs,
            "avg_coins": avg_coins,
        }

    def admin_adjust_balance(self, admin_id: int, target_user_id: int, amount: float, currency: str, operation: str = "add") -> Tuple[bool, str]:
        with _STORAGE_LOCK:
            target = get_user(target_user_id)
            if not target:
                return False, f"User {target_user_id} not found."

            if operation == "add":
                new_bal = atomic_add_balance(target_user_id, amount, currency=currency, reason=f"Admin {admin_id} grant")
                log_admin_action(admin_id, f"eco_add_{currency}", target_user_id, f"Added {amount} {currency}")
                return True, f"Successfully granted {amount:g} {currency} to User {target_user_id}. New balance: {new_bal:g}"

            elif operation == "deduct":
                deducted = atomic_deduct_balance(target_user_id, amount, currency=currency, reason=f"Admin {admin_id} confiscate")
                if not deducted:
                    return False, f"Could not deduct {amount:g} {currency}: User has insufficient balance."
                log_admin_action(admin_id, f"eco_deduct_{currency}", target_user_id, f"Deducted {amount} {currency}")
                return True, f"Successfully deducted {amount:g} {currency} from User {target_user_id}."

            elif operation == "set":
                curr_key = "gems" if currency == "gems" else ("event_tokens" if currency == "event_tokens" else ("premium_tokens" if currency == "premium_tokens" else "balance"))
                update_user(target_user_id, **{curr_key: amount})
                log_transaction(target_user_id, "admin_set", amount, currency, amount, f"Admin {admin_id} override")
                log_admin_action(admin_id, f"eco_set_{currency}", target_user_id, f"Set to {amount}")
                return True, f"Successfully set {currency} balance of User {target_user_id} to {amount:g}."

            return False, f"Unknown operation '{operation}'."
