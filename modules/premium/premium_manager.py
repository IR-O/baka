"""
Miko Telegram Gaming Platform - Premium Membership Manager
Handles VIP tiers (Silver, Gold, Diamond Sovereign), perks, badges, daily gem distributions, and subscription history.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import (
    get_user,
    update_user,
    atomic_add_balance,
    _STORAGE_LOCK,
)
from modules.utils.db import _get_conn


@dataclass
class PremiumTier:
    tier_id: str
    name: str
    badge: str
    daily_gems: float
    cooldown_reduction_pct: int
    marketplace_tax_rate: float
    description: str


PREMIUM_TIERS: Dict[str, PremiumTier] = {
    "silver": PremiumTier(
        tier_id="silver",
        name="Silver VIP",
        badge="⭐ Silver VIP",
        daily_gems=1.0,
        cooldown_reduction_pct=20,
        marketplace_tax_rate=0.04,
        description="20% faster game cooldowns, 1 daily Gem bonus, Silver VIP badge."
    ),
    "gold": PremiumTier(
        tier_id="gold",
        name="Gold VIP",
        badge="💎 Gold VIP",
        daily_gems=3.0,
        cooldown_reduction_pct=40,
        marketplace_tax_rate=0.02,
        description="40% faster game cooldowns, 3 daily Gems bonus, Gold VIP badge, exclusive packs."
    ),
    "diamond": PremiumTier(
        tier_id="diamond",
        name="Diamond Sovereign",
        badge="👑 Diamond Sovereign",
        daily_gems=5.0,
        cooldown_reduction_pct=60,
        marketplace_tax_rate=0.00,
        description="60% faster game cooldowns, 5 daily Gems bonus, zero marketplace tax, Sovereign badge."
    ),
}


class PremiumManager:
    _instance: Optional[PremiumManager] = None

    @classmethod
    def get_instance(cls) -> PremiumManager:
        if cls._instance is None:
            cls._instance = PremiumManager()
            cls._instance._ensure_table()
        return cls._instance

    def _ensure_table(self):
        try:
            conn = _get_conn()
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS premium_subscriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        tier TEXT NOT NULL,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at REAL NOT NULL,
                        source TEXT DEFAULT 'Payment',
                        last_perk_claim TEXT DEFAULT ''
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_prem_user ON premium_subscriptions(user_id)")
        except Exception as e:
            print(f"Error creating premium_subscriptions table: {e}")

    def grant_premium(self, user_id: int, tier_key: str = "silver", days: int = 30, source: str = "Payment") -> Tuple[bool, str]:
        clean_tier = tier_key.strip().lower()
        tier = PREMIUM_TIERS.get(clean_tier, PREMIUM_TIERS["silver"])

        now = time.time()
        duration_sec = days * 86400

        with _STORAGE_LOCK:
            ud = get_user(user_id)
            current_expiry = ud.get("premium_expiry", 0)
            if current_expiry and current_expiry > now:
                new_expiry = current_expiry + duration_sec
            else:
                new_expiry = now + duration_sec

            try:
                conn = _get_conn()
                with conn:
                    conn.execute("""
                        INSERT INTO premium_subscriptions (user_id, tier, expires_at, source)
                        VALUES (?, ?, ?, ?)
                    """, (str(user_id), tier.tier_id, new_expiry, source))

                update_user(user_id, premium=True, premium_tier=tier.tier_id, premium_expiry=new_expiry)
                return True, f"🎉 <b>{tier.badge}</b> granted for {days} days! Active until {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(new_expiry))}."
            except Exception as e:
                return False, f"Failed to grant premium: {e}"

    def check_subscription(self, user_id: int) -> Dict[str, Any]:
        ud = get_user(user_id)
        is_prem = bool(ud.get("premium", False))
        expiry = ud.get("premium_expiry", 0)
        now = time.time()

        if is_prem and expiry and expiry < now:
            # Expired
            update_user(user_id, premium=False, premium_tier=None)
            is_prem = False

        tier_id = ud.get("premium_tier") or "silver"
        tier = PREMIUM_TIERS.get(tier_id, PREMIUM_TIERS["silver"])

        days_left = max(0, int((expiry - now) / 86400)) if (is_prem and expiry > now) else 0

        return {
            "is_premium": is_prem,
            "tier_id": tier.tier_id if is_prem else None,
            "tier_name": tier.name if is_prem else "Standard Free Player",
            "badge": tier.badge if is_prem else "👤 Free Tier",
            "days_left": days_left,
            "expiry_timestamp": expiry,
            "tier_info": tier if is_prem else None,
        }

    def claim_daily_perks(self, user_id: int) -> Tuple[bool, str]:
        sub = self.check_subscription(user_id)
        if not sub["is_premium"]:
            return False, "⚠️ You need an active VIP Premium Membership to claim daily perks! See /premium."

        tier: PremiumTier = sub["tier_info"]
        import datetime
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, last_perk_claim FROM premium_subscriptions
                WHERE user_id = ? ORDER BY id DESC LIMIT 1
            """, (str(user_id),))
            row = cur.fetchone()

            if row and row[1] == today_str:
                return False, "⏳ You have already claimed today's VIP perk bonus! Return tomorrow after UTC midnight."

            with conn:
                if row:
                    conn.execute("UPDATE premium_subscriptions SET last_perk_claim = ? WHERE id = ?", (today_str, row[0]))

            atomic_add_balance(user_id, tier.daily_gems, currency="gems", reason="VIP Daily Perk Claim")
            return True, f"💎 <b>VIP DAILY PERK CLAIMED!</b>\n\nReward: <b>+{tier.daily_gems} Gems</b> received!"
        except Exception as e:
            return False, f"Database error claiming perk: {e}"
