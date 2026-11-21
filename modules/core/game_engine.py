from __future__ import annotations

import time
import uuid
import json
import random
from typing import Dict, Any, List, Optional, Tuple, Callable
from abc import ABC, abstractmethod

from modules.utils.storage import (
    get_user,
    update_user,
    atomic_add_balance,
    atomic_deduct_balance,
    add_xp_with_limits,
    _STORAGE_LOCK,
)
from modules.utils.db import (
    _get_conn,
    check_cooldown,
    set_cooldown,
    log_transaction,
)


class GameDifficulty:
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"

    MULTIPLIERS = {
        EASY: 1.0,
        NORMAL: 1.25,
        HARD: 1.75,
        EXPERT: 2.5,
    }


class SessionStatus:
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class GameSession:
    def __init__(
        self,
        session_id: str,
        game_id: str,
        chat_id: int,
        host_id: int,
        stake: float = 0.0,
        currency: str = "coins",
        difficulty: str = GameDifficulty.NORMAL,
        min_players: int = 1,
        max_players: int = 2,
        timeout_seconds: float = 300.0,
    ):
        self.session_id = session_id
        self.game_id = game_id
        self.chat_id = chat_id
        self.host_id = host_id
        self.stake = float(stake)
        self.currency = currency
        self.difficulty = difficulty
        self.min_players = min_players
        self.max_players = max_players
        self.timeout_seconds = timeout_seconds
        self.status = SessionStatus.WAITING
        self.created_at = time.time()
        self.expires_at = self.created_at + timeout_seconds
        self.players: List[Dict[str, Any]] = []
        self.state: Dict[str, Any] = {}
        self.winner_id: Optional[int] = None
        self.event_log: List[Dict[str, Any]] = []

    def is_expired(self) -> bool:
        return time.time() > self.expires_at and self.status in (SessionStatus.WAITING, SessionStatus.ACTIVE)

    def add_player(self, user_id: int, name: str) -> bool:
        if len(self.players) >= self.max_players:
            return False
        if any(p["user_id"] == user_id for p in self.players):
            return False
        self.players.append({"user_id": user_id, "name": name, "joined_at": time.time()})
        self.expires_at = time.time() + self.timeout_seconds
        return True

    def remove_player(self, user_id: int) -> bool:
        initial_len = len(self.players)
        self.players = [p for p in self.players if p["user_id"] != user_id]
        return len(self.players) < initial_len

    def log_event(self, action: str, user_id: Optional[int] = None, details: str = ""):
        self.event_log.append({
            "timestamp": time.time(),
            "action": action,
            "user_id": user_id,
            "details": details,
        })


class BaseGame(ABC):
    def __init__(
        self,
        game_id: str,
        game_name: str,
        description: str = "",
        min_players: int = 1,
        max_players: int = 2,
        default_stake: float = 50.0,
        cooldown_seconds: float = 5.0,
        timeout_seconds: float = 300.0,
    ):
        self.game_id = game_id
        self.game_name = game_name
        self.description = description
        self.min_players = min_players
        self.max_players = max_players
        self.default_stake = default_stake
        self.cooldown_seconds = cooldown_seconds
        self.timeout_seconds = timeout_seconds

    def initialize_session(self, session: GameSession) -> None:
        session.state = {}

    def process_action(self, session: GameSession, user_id: int, action: str, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Processes player input. Returns (is_valid, message, state_update)."""
        return True, "Action processed", {}

    def calculate_rewards(self, session: GameSession, winner_id: int) -> Dict[str, Any]:
        """Calculates fair reward payout with difficulty and tier multipliers."""
        diff_mult = GameDifficulty.MULTIPLIERS.get(session.difficulty, 1.0)
        total_pot = session.stake * max(1, len(session.players))
        reward_coins = int(total_pot * diff_mult)
        reward_xp = int(30 * diff_mult)
        reward_gems = 0.0

        if session.difficulty == GameDifficulty.EXPERT and random.random() < 0.25:
            reward_gems = 0.1

        return {
            "coins": reward_coins,
            "xp": reward_xp,
            "gems": reward_gems,
        }


class CentralGamingEngine:
    _instance: Optional[CentralGamingEngine] = None

    def __init__(self):
        self._games: Dict[str, BaseGame] = {}
        self._sessions: Dict[str, GameSession] = {}
        self._matchmaking_queue: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def get_instance(cls) -> CentralGamingEngine:
        if cls._instance is None:
            cls._instance = CentralGamingEngine()
        return cls._instance

    def register_game(self, game: BaseGame) -> None:
        self._games[game.game_id] = game
        if game.game_id not in self._matchmaking_queue:
            self._matchmaking_queue[game.game_id] = []

    def get_game(self, game_id: str) -> Optional[BaseGame]:
        return self._games.get(game_id)

    def list_games(self) -> List[Dict[str, Any]]:
        return [
            {
                "game_id": g.game_id,
                "name": g.game_name,
                "description": g.description,
                "min_players": g.min_players,
                "max_players": g.max_players,
                "default_stake": g.default_stake,
            }
            for g in self._games.values()
        ]

    def create_session(
        self,
        game_id: str,
        chat_id: int,
        host_id: int,
        host_name: str,
        stake: float = 0.0,
        currency: str = "coins",
        difficulty: str = GameDifficulty.NORMAL,
        max_players: Optional[int] = None,
    ) -> Tuple[Optional[GameSession], str]:
        game = self.get_game(game_id)
        if not game:
            return None, f"Game '{game_id}' is not registered in Gaming Engine."

        # Cooldown Anti-Cheat Check
        is_cd, rem = check_cooldown(host_id, f"game_{game_id}")
        if is_cd:
            return None, f"⏳ Cooldown active! Please wait {rem}s before starting another {game.game_name}."

        # Existing active session in chat check
        existing = self.get_active_session_for_chat(chat_id, game_id)
        if existing:
            return None, f"A session of {game.game_name} is already waiting or in progress in this chat!"

        # Stake deduction validation
        if stake > 0:
            ud = get_user(host_id)
            if ud.get("balance", 0) < stake:
                return None, f"Insufficient balance for stake ${stake:,}. You have ${ud.get('balance', 0):,}."
            if not atomic_deduct_balance(host_id, stake, currency=currency, reason=f"Stake for {game.game_name}"):
                return None, "Stake transaction failed."

        session_id = f"{game_id}_{uuid.uuid4().hex[:8]}"
        session = GameSession(
            session_id=session_id,
            game_id=game_id,
            chat_id=chat_id,
            host_id=host_id,
            stake=stake,
            currency=currency,
            difficulty=difficulty,
            min_players=game.min_players,
            max_players=max_players or game.max_players,
            timeout_seconds=game.timeout_seconds,
        )
        session.add_player(host_id, host_name)
        game.initialize_session(session)

        self._sessions[session_id] = session
        self._sync_session_db(session)
        set_cooldown(host_id, f"game_{game_id}", game.cooldown_seconds)
        return session, ""

    def join_session(self, session_id: str, user_id: int, user_name: str) -> Tuple[bool, str]:
        session = self._sessions.get(session_id)
        if not session:
            return False, "Session not found or has already concluded."
        if session.status != SessionStatus.WAITING:
            return False, "This game has already started or concluded."
        if any(p["user_id"] == user_id for p in session.players):
            return False, "You have already joined this session."
        if len(session.players) >= session.max_players:
            return False, "Game lobby is already full!"

        if session.stake > 0:
            ud = get_user(user_id)
            if ud.get("balance", 0) < session.stake:
                return False, f"Insufficient balance for stake ${session.stake:,}. Current balance: ${ud.get('balance', 0):,}."
            if not atomic_deduct_balance(user_id, session.stake, currency=session.currency, reason=f"Join stake {session.game_id}"):
                return False, "Stake payment failed."

        added = session.add_player(user_id, user_name)
        if not added:
            if session.stake > 0:
                atomic_add_balance(user_id, session.stake, currency=session.currency, reason="Refund join failed")
            return False, "Could not join session."

        session.log_event("join", user_id, f"{user_name} joined lobby.")
        self._sync_session_db(session)
        return True, f"Successfully joined! ({len(session.players)}/{session.max_players} players)"

    def get_session(self, session_id: str) -> Optional[GameSession]:
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            self._handle_session_timeout(session)
        return session

    def get_active_session_for_chat(self, chat_id: int, game_id: Optional[str] = None) -> Optional[GameSession]:
        now = time.time()
        for session in list(self._sessions.values()):
            if session.chat_id == chat_id and session.status in (SessionStatus.WAITING, SessionStatus.ACTIVE):
                if session.is_expired():
                    self._handle_session_timeout(session)
                    continue
                if game_id is None or session.game_id == game_id:
                    return session
        return None

    def finalize_game(self, session_id: str, winner_id: Optional[int]) -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session:
            return {}

        session.status = SessionStatus.COMPLETED
        session.winner_id = winner_id
        game = self.get_game(session.game_id)
        payouts: Dict[str, Any] = {}

        if game and winner_id:
            rewards = game.calculate_rewards(session, winner_id)
            coins = rewards.get("coins", 0)
            xp = rewards.get("xp", 0)
            gems = rewards.get("gems", 0.0)

            if coins > 0:
                atomic_add_balance(winner_id, coins, currency=session.currency, reason=f"Won {game.game_name}")
            if gems > 0:
                atomic_add_balance(winner_id, gems, currency="gems", reason=f"Bonus {game.game_name}")
            if xp > 0:
                add_xp_with_limits(winner_id, xp, reason=f"Won {game.game_name}")

            payouts = rewards
            session.log_event("win", winner_id, f"Winner awarded {rewards}")

            # Update stats
            self._record_player_game_stats(winner_id, session.game_id, is_win=True, won_amount=coins)
            for p in session.players:
                if p["user_id"] != winner_id:
                    self._record_player_game_stats(p["user_id"], session.game_id, is_win=False, lost_amount=int(session.stake))

        self._sync_session_db(session)
        return payouts

    def cancel_session(self, session_id: str, reason: str = "Game cancelled") -> None:
        session = self._sessions.get(session_id)
        if not session or session.status in (SessionStatus.COMPLETED, SessionStatus.CANCELLED):
            return

        session.status = SessionStatus.CANCELLED
        # Refund stakes
        if session.stake > 0:
            for p in session.players:
                atomic_add_balance(p["user_id"], session.stake, currency=session.currency, reason=f"Refund: {reason}")

        session.log_event("cancelled", details=reason)
        self._sync_session_db(session)

    def _handle_session_timeout(self, session: GameSession) -> None:
        session.status = SessionStatus.EXPIRED
        if session.stake > 0:
            for p in session.players:
                atomic_add_balance(p["user_id"], session.stake, currency=session.currency, reason="Refund: Session timeout")
        session.log_event("timeout", details="Game session expired automatically")
        self._sync_session_db(session)

    def _sync_session_db(self, session: GameSession) -> None:
        try:
            conn = _get_conn()
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO game_sessions
                    (session_id, game_type, chat_id, host_user_id, status, stake, max_players, players_data, state_data, winner_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        session.session_id,
                        session.game_id,
                        str(session.chat_id),
                        str(session.host_id),
                        session.status,
                        session.stake,
                        session.max_players,
                        json.dumps(session.players),
                        json.dumps(session.state),
                        str(session.winner_id) if session.winner_id else None,
                    )
                )
        except Exception as e:
            print(f"Error syncing game session to DB: {e}")

    def _record_player_game_stats(self, user_id: int, game_key: str, is_win: bool, won_amount: int = 0, lost_amount: int = 0) -> None:
        try:
            conn = _get_conn()
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT games_played, wins, losses, streak, max_streak, total_won, total_lost FROM game_statistics WHERE user_id = ? AND game_key = ?", (str(user_id), game_key))
                row = cur.fetchone()
                if row:
                    played, wins, losses, streak, max_s, t_won, t_lost = row
                    played += 1
                    if is_win:
                        wins += 1
                        streak += 1
                    else:
                        losses += 1
                        streak = 0
                    max_s = max(max_s, streak)
                    t_won += won_amount
                    t_lost += lost_amount
                    conn.execute(
                        """
                        UPDATE game_statistics
                        SET games_played = ?, wins = ?, losses = ?, streak = ?, max_streak = ?, total_won = ?, total_lost = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND game_key = ?
                        """,
                        (played, wins, losses, streak, max_s, t_won, t_lost, str(user_id), game_key)
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO game_statistics (user_id, game_key, games_played, wins, losses, streak, max_streak, total_won, total_lost)
                        VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
                        """,
                        (str(user_id), game_key, 1 if is_win else 0, 0 if is_win else 1, 1 if is_win else 0, 1 if is_win else 0, won_amount, lost_amount)
                    )

            # Also update overall total_games in user profile
            ud = get_user(user_id)
            t_games = ud.get("total_games", 0) + 1
            w_games = ud.get("games_won", 0) + (1 if is_win else 0)
            l_games = ud.get("games_lost", 0) + (0 if is_win else 1)
            update_user(user_id, total_games=t_games, games_won=w_games, games_lost=l_games)
        except Exception as e:
            print(f"Error recording player game stats: {e}")

    def cleanup_expired_sessions(self) -> int:
        count = 0
        now = time.time()
        for sid, session in list(self._sessions.items()):
            if session.is_expired():
                self._handle_session_timeout(session)
                count += 1
        return count
