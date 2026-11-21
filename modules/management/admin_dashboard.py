"""
Miko Telegram Gaming Platform - Advanced Admin Dashboard & Control Center
Provides system analytics, economy oversight, role-based authorization (verified User IDs),
moderation (warn/ban/unban), audit logging, and maintenance mode controls.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import (
    get_user,
    update_user,
    atomic_add_balance,
    atomic_deduct_balance,
    get_all_users,
    _STORAGE_LOCK,
)
from modules.utils.db import (
    _get_conn,
    is_sudo_user,
    get_owner_id,
    log_admin_action,
)


class AdminDashboard:
    _instance: Optional[AdminDashboard] = None
    _maintenance_mode: bool = False

    @classmethod
    def get_instance(cls) -> AdminDashboard:
        if cls._instance is None:
            cls._instance = AdminDashboard()
        return cls._instance

    def is_authorized(self, user_id: int) -> bool:
        """Verifies admin privileges strictly against numeric Telegram user IDs."""
        return user_id == get_owner_id() or is_sudo_user(user_id)

    def is_maintenance(self) -> bool:
        return self._maintenance_mode

    def set_maintenance(self, admin_id: int, state: bool) -> Tuple[bool, str]:
        if not self.is_authorized(admin_id):
            return False, "Unauthorized."
        self._maintenance_mode = state
        status_str = "ENABLED (Users cannot start games)" if state else "DISABLED (Normal operations)"
        self.log_action(admin_id, "TOGGLE_MAINTENANCE", None, f"Maintenance set to {state}")
        return True, f"🛠️ Maintenance mode is now <b>{status_str}</b>."

    def log_action(self, admin_id: int, action: str, target_id: Optional[int], details: str):
        try:
            log_admin_action(admin_id, action, target_id, details)
        except Exception as e:
            print(f"Error logging admin action: {e}")

    def get_system_overview(self) -> Dict[str, Any]:
        all_u = get_all_users()
        total_users = len(all_u)

        total_coins = sum(u.get("balance", 0) for u in all_u.values())
        total_gems = sum(u.get("gems", 0.0) for u in all_u.values())
        total_kills = sum(u.get("kills", 0) for u in all_u.values())
        total_robs = sum(u.get("robs", 0) for u in all_u.values())
        prem_users = sum(1 for u in all_u.values() if u.get("premium"))

        # Database queries for game sessions & transactions
        total_tx = 0
        total_sessions = 0
        total_guilds = 0
        total_pets = 0
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(id) FROM transactions")
            total_tx = cur.fetchone()[0]

            cur.execute("SELECT COUNT(session_id) FROM game_sessions")
            total_sessions = cur.fetchone()[0]

            cur.execute("SELECT COUNT(guild_id) FROM guilds")
            total_guilds = cur.fetchone()[0]

            cur.execute("SELECT COUNT(pet_id) FROM pets")
            total_pets = cur.fetchone()[0]
        except Exception as e:
            print(f"Overview db error: {e}")

        return {
            "total_users": total_users,
            "total_coins": total_coins,
            "total_gems": round(total_gems, 2),
            "total_kills": total_kills,
            "total_robs": total_robs,
            "premium_users": prem_users,
            "total_transactions": total_tx,
            "total_game_sessions": total_sessions,
            "total_guilds": total_guilds,
            "total_pets": total_pets,
            "maintenance_mode": self._maintenance_mode,
        }

    def warn_user(self, admin_id: int, target_id: int, reason: str) -> Tuple[bool, str]:
        if not self.is_authorized(admin_id):
            return False, "Unauthorized."
        ud = get_user(target_id)
        current_warns = ud.get("warns", 0) + 1
        update_user(target_id, warns=current_warns)
        self.log_action(admin_id, "WARN_USER", target_id, f"Warned ({current_warns}/3): {reason}")

        banned_msg = ""
        if current_warns >= 3:
            update_user(target_id, banned=True)
            self.log_action(admin_id, "AUTO_BAN_WARNS", target_id, "Exceeded 3 warnings")
            banned_msg = "\n⛔ <b>User has reached 3 warnings and was automatically BANNED!</b>"

        return True, f"⚠️ User <code>{target_id}</code> warned ({current_warns}/3).\nReason: <i>{reason}</i>{banned_msg}"

    def ban_user(self, admin_id: int, target_id: int, reason: str) -> Tuple[bool, str]:
        if not self.is_authorized(admin_id):
            return False, "Unauthorized."
        if target_id == get_owner_id():
            return False, "Cannot ban the Bot Owner."

        update_user(target_id, banned=True)
        self.log_action(admin_id, "BAN_USER", target_id, reason)
        return True, f"⛔ User <code>{target_id}</code> was permanently BANNED.\nReason: <i>{reason}</i>"

    def unban_user(self, admin_id: int, target_id: int) -> Tuple[bool, str]:
        if not self.is_authorized(admin_id):
            return False, "Unauthorized."
        update_user(target_id, banned=False, warns=0)
        self.log_action(admin_id, "UNBAN_USER", target_id, "Unbanned by admin")
        return True, f"✅ User <code>{target_id}</code> unbanned and warnings reset to 0."

    def eco_modify(self, admin_id: int, target_id: int, action: str, amount: float, currency: str = "coins") -> Tuple[bool, str]:
        if not self.is_authorized(admin_id):
            return False, "Unauthorized."

        if amount <= 0:
            return False, "Amount must be greater than 0."

        currency = "gems" if "gem" in currency.lower() else "coins"

        with _STORAGE_LOCK:
            if action == "give":
                atomic_add_balance(target_id, amount, currency=currency, reason=f"Admin grant by {admin_id}")
                self.log_action(admin_id, f"ECO_GIVE_{currency.upper()}", target_id, f"+{amount}")
                return True, f"✅ Added +{amount} {currency} to User <code>{target_id}</code>."
            elif action == "take":
                atomic_deduct_balance(target_id, amount, currency=currency, reason=f"Admin deduction by {admin_id}")
                self.log_action(admin_id, f"ECO_TAKE_{currency.upper()}", target_id, f"-{amount}")
                return True, f"✅ Deducted -{amount} {currency} from User <code>{target_id}</code>."
            elif action == "set":
                update_kwargs = {"gems": amount} if currency == "gems" else {"balance": int(amount)}
                update_user(target_id, **update_kwargs)
                self.log_action(admin_id, f"ECO_SET_{currency.upper()}", target_id, f"Set to {amount}")
                return True, f"✅ Set User <code>{target_id}</code> {currency} balance to {amount}."

        return False, "Unknown action."

    def get_recent_reports(self, limit: int = 5) -> List[Dict[str, Any]]:
        reports = []
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, reporter_id, reported_id, chat_id, reason, status, created_at
                FROM player_reports ORDER BY id DESC LIMIT ?
            """, (limit,))
            for r in cur.fetchall():
                reports.append({
                    "id": r[0],
                    "reporter_id": int(r[1]),
                    "reported_id": int(r[2]),
                    "chat_id": int(r[3]) if r[3] else None,
                    "reason": r[4],
                    "status": r[5],
                    "created_at": r[6],
                })
        except Exception as e:
            print(f"Error fetching reports: {e}")
        return reports
