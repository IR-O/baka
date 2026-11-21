from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple

from modules.utils.storage import (
    get_user,
    atomic_transfer_balance,
    _STORAGE_LOCK,
)
from modules.utils.db import (
    _get_conn,
    record_player_report,
)


class SocialManager:
    _instance: Optional[SocialManager] = None

    @classmethod
    def get_instance(cls) -> SocialManager:
        if cls._instance is None:
            cls._instance = SocialManager()
        return cls._instance

    def send_friend_request(self, sender_id: int, receiver_id: int) -> Tuple[bool, str]:
        if sender_id == receiver_id:
            return False, "You cannot send a friend request to yourself."

        try:
            conn = _get_conn()
            cur = conn.cursor()

            # Check if already friends
            cur.execute("SELECT id FROM friendships WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)", (str(sender_id), str(receiver_id), str(receiver_id), str(sender_id)))
            if cur.fetchone():
                return False, "You are already friends with this player!"

            # Check existing pending request
            cur.execute("SELECT id, sender_id FROM friend_requests WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)", (str(sender_id), str(receiver_id), str(receiver_id), str(sender_id)))
            row = cur.fetchone()
            if row:
                if str(row[1]) == str(receiver_id):
                    # Auto-accept reciprocal request!
                    return self.accept_friend_request(sender_id, receiver_id)
                return False, "A friend request is already pending between you two!"

            with conn:
                conn.execute("INSERT INTO friend_requests (sender_id, receiver_id, status) VALUES (?, ?, 'pending')", (str(sender_id), str(receiver_id)))
            return True, f"🤝 Friend request sent to User <code>{receiver_id}</code>!"
        except Exception as e:
            return False, f"Failed to send friend request: {e}"

    def accept_friend_request(self, receiver_id: int, sender_id: int) -> Tuple[bool, str]:
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id FROM friend_requests WHERE sender_id = ? AND receiver_id = ?", (str(sender_id), str(receiver_id)))
            row = cur.fetchone()
            if not row:
                return False, "No pending friend request found from that user."

            with conn:
                conn.execute("DELETE FROM friend_requests WHERE id = ?", (row[0],))
                conn.execute("INSERT OR IGNORE INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'accepted')", (str(receiver_id), str(sender_id)))
                conn.execute("INSERT OR IGNORE INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'accepted')", (str(sender_id), str(receiver_id)))
            return True, f"🎉 You are now friends with User <code>{sender_id}</code>!"
        except Exception as e:
            return False, f"Failed to accept friend request: {e}"

    def remove_friend(self, user_id: int, target_id: int) -> Tuple[bool, str]:
        try:
            conn = _get_conn()
            with conn:
                conn.execute("DELETE FROM friendships WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)", (str(user_id), str(target_id), str(target_id), str(user_id)))
            return True, f"User <code>{target_id}</code> was removed from your friends list."
        except Exception as e:
            return False, f"Failed to remove friend: {e}"

    def get_friends(self, user_id: int) -> List[Dict[str, Any]]:
        friends = []
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute("SELECT friend_id, created_at FROM friendships WHERE user_id = ?", (str(user_id),))
            rows = cur.fetchall()
            for r in rows:
                fid = int(r[0])
                ud = get_user(fid)
                friends.append({
                    "user_id": fid,
                    "name": ud.get("display_name") or ud.get("username", "User"),
                    "level": ud.get("level", 1),
                    "since": r[1],
                })
        except Exception as e:
            print(f"Error fetching friends: {e}")
        return friends

    def submit_report(self, reporter_id: int, reported_id: int, chat_id: Optional[int], reason: str) -> Tuple[bool, str]:
        if reporter_id == reported_id:
            return False, "You cannot report yourself."
        if not reason.strip():
            return False, "Please provide a reason for the report."

        record_player_report(reporter_id, reported_id, chat_id, reason.strip())
        return True, "🚨 Player report submitted to administrators for investigation."
