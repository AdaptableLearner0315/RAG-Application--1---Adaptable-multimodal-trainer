"""
Long-term memory storage using SQLite.
Stores permanent user profiles that persist across sessions.
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.memory.schemas import LongTermMemory


class LongTermMemoryStore:
    """
    Permanent user profile storage using SQLite.
    Handles CRUD operations for user profiles with retry logic.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize long-term memory store.

        Args:
            db_path: Path to SQLite database. Defaults to config storage dir.
        """
        settings = get_settings()
        self.db_path = db_path or settings.storage_dir / "long_term_memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection with retry logic.

        Returns:
            sqlite3.Connection: Database connection.

        Raises:
            sqlite3.OperationalError: If connection fails after retries.
        """
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(str(self.db_path), timeout=10)
                conn.row_factory = sqlite3.Row
                return conn
            except sqlite3.OperationalError as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise

    def get(self, user_id: str) -> Optional[LongTermMemory]:
        """
        Retrieve user's long-term profile.

        Args:
            user_id: Unique user identifier.

        Returns:
            LongTermMemory object or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT data FROM profiles WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

        if not row:
            return None

        data = json.loads(row["data"])
        return LongTermMemory(**data)

    def upsert(self, user_id: str, data: Dict) -> None:
        """
        Create or update user profile.

        Args:
            user_id: Unique user identifier.
            data: Profile data to store/update.

        Raises:
            TypeError: If data contains invalid types.
            ValueError: If data fails validation.
        """
        # Validate data by creating model
        existing = self.get(user_id)
        if existing:
            merged = existing.model_dump()
            merged.update(data)
            merged["updated_at"] = datetime.utcnow().isoformat()
            profile = LongTermMemory(**merged)
        else:
            data["user_id"] = user_id
            data["created_at"] = datetime.utcnow().isoformat()
            data["updated_at"] = data["created_at"]
            profile = LongTermMemory(**data)

        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO profiles (user_id, data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    data = excluded.data,
                    updated_at = excluded.updated_at
            """, (user_id, profile.model_dump_json(), now, now))
            conn.commit()

    def add_injury(self, user_id: str, injury: str) -> None:
        """
        Add injury to user's profile.

        Args:
            user_id: Unique user identifier.
            injury: Injury description.
        """
        profile = self.get(user_id)
        if not profile:
            raise ValueError(f"User {user_id} not found")

        # Dedupe - don't add if already exists
        if injury.lower() not in [i.lower() for i in profile.injuries]:
            profile.injuries.append(injury)
            self.upsert(user_id, {"injuries": profile.injuries})

    def remove_injury(self, user_id: str, injury: str) -> None:
        """
        Remove injury from user's profile.

        Args:
            user_id: Unique user identifier.
            injury: Injury description to remove.
        """
        profile = self.get(user_id)
        if not profile:
            raise ValueError(f"User {user_id} not found")

        profile.injuries = [i for i in profile.injuries if i.lower() != injury.lower()]
        self.upsert(user_id, {"injuries": profile.injuries})

    def add_intolerance(self, user_id: str, intolerance: str) -> None:
        """
        Add food intolerance to user's profile.

        Args:
            user_id: Unique user identifier.
            intolerance: Intolerance to add.
        """
        profile = self.get(user_id)
        if not profile:
            raise ValueError(f"User {user_id} not found")

        if intolerance.lower() not in [i.lower() for i in profile.intolerances]:
            profile.intolerances.append(intolerance)
            self.upsert(user_id, {"intolerances": profile.intolerances})

    def delete(self, user_id: str) -> bool:
        """
        Delete user profile (GDPR compliance).

        Args:
            user_id: Unique user identifier.

        Returns:
            True if deleted, False if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM profiles WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_users(self) -> List[str]:
        """
        List all user IDs in the store.

        Returns:
            List of user IDs.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT user_id FROM profiles")
            return [row["user_id"] for row in cursor.fetchall()]
