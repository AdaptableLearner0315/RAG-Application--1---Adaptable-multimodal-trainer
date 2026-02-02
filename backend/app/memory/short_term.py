"""
Short-term memory storage using SQLite.
Stores rolling 7-day activity window that auto-expires.
"""

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.memory.schemas import MealLog, ShortTermMemory, SleepLog, WorkoutLog


class ShortTermMemoryStore:
    """
    Rolling 7-day activity memory using SQLite.
    Automatically cleans up records older than retention period.
    """

    def __init__(self, db_path: Optional[Path] = None, retention_days: int = 7):
        """
        Initialize short-term memory store.

        Args:
            db_path: Path to SQLite database. Defaults to config storage dir.
            retention_days: Number of days to retain records. Defaults to 7.
        """
        settings = get_settings()
        self.db_path = db_path or settings.storage_dir / "short_term_memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_logs (
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, date)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_date
                ON daily_logs(user_id, date)
            """)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_or_create_daily(self, user_id: str, log_date: date) -> ShortTermMemory:
        """
        Get or create daily log for user.

        Args:
            user_id: User identifier.
            log_date: Date of the log.

        Returns:
            ShortTermMemory for the day.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT data FROM daily_logs WHERE user_id = ? AND date = ?",
                (user_id, log_date.isoformat())
            )
            row = cursor.fetchone()

        if row:
            data = json.loads(row["data"])
            return ShortTermMemory(**data)

        return ShortTermMemory(user_id=user_id, date=log_date)

    def _save_daily(self, memory: ShortTermMemory) -> None:
        """Save daily log to database."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO daily_logs (user_id, date, data, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, date) DO UPDATE SET
                    data = excluded.data,
                    updated_at = excluded.updated_at
            """, (
                memory.user_id,
                memory.date.isoformat(),
                memory.model_dump_json(),
                now
            ))
            conn.commit()

    def log_meal(
        self,
        user_id: str,
        meal: Dict,
        log_date: Optional[date] = None
    ) -> None:
        """
        Log a meal to short-term memory.

        Args:
            user_id: Unique user identifier.
            meal: Meal data with time, foods, calories, protein, carbs, fat.
            log_date: Date to log to. Defaults to today.

        Raises:
            ValueError: If meal data is missing required fields or has invalid values.
        """
        # Validate meal data
        required_fields = {"time", "foods", "calories", "protein", "carbs", "fat"}
        missing = required_fields - set(meal.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Validate non-negative values
        for field in ["calories", "protein", "carbs", "fat"]:
            if meal.get(field, 0) < 0:
                raise ValueError(f"{field} cannot be negative")

        meal_log = MealLog(**meal)
        log_date = log_date or date.today()
        daily = self._get_or_create_daily(user_id, log_date)

        daily.meals.append(meal_log)
        daily.calories_consumed += meal_log.calories
        daily.protein_total += meal_log.protein

        self._save_daily(daily)

    def log_workout(
        self,
        user_id: str,
        workout: Dict,
        log_date: Optional[date] = None
    ) -> None:
        """
        Log a workout to short-term memory.

        Args:
            user_id: Unique user identifier.
            workout: Workout data with time, type, duration_min, intensity.
            log_date: Date to log to. Defaults to today.

        Raises:
            ValueError: If workout data is invalid.
        """
        required_fields = {"time", "type", "duration_min", "intensity"}
        missing = required_fields - set(workout.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        if workout.get("duration_min", 0) <= 0:
            raise ValueError("duration_min must be positive")

        workout_log = WorkoutLog(**workout)
        log_date = log_date or date.today()
        daily = self._get_or_create_daily(user_id, log_date)

        daily.workouts.append(workout_log)
        # Estimate calories burned (rough calculation)
        intensity_multiplier = {"low": 4, "moderate": 6, "high": 8}
        multiplier = intensity_multiplier.get(workout_log.intensity.lower(), 5)
        daily.calories_burned += workout_log.duration_min * multiplier

        self._save_daily(daily)

    def log_sleep(
        self,
        user_id: str,
        sleep: Dict,
        log_date: Optional[date] = None
    ) -> None:
        """
        Log sleep to short-term memory.

        Args:
            user_id: Unique user identifier.
            sleep: Sleep data with bed_time, wake_time, quality.
            log_date: Date to log to. Defaults to today.
        """
        sleep_log = SleepLog(**sleep)
        log_date = log_date or date.today()
        daily = self._get_or_create_daily(user_id, log_date)

        daily.sleep = sleep_log
        self._save_daily(daily)

    def get_recent(
        self,
        user_id: str,
        days: int = 7
    ) -> List[ShortTermMemory]:
        """
        Get recent activity within rolling window.

        Args:
            user_id: Unique user identifier.
            days: Number of days to look back. Defaults to 7.

        Returns:
            List of daily activity records, most recent first.
        """
        cutoff_date = date.today() - timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT data FROM daily_logs
                WHERE user_id = ? AND date >= ?
                ORDER BY date DESC
            """, (user_id, cutoff_date.isoformat()))
            rows = cursor.fetchall()

        return [ShortTermMemory(**json.loads(row["data"])) for row in rows]

    def get_day(self, user_id: str, log_date: date) -> Optional[ShortTermMemory]:
        """
        Get activity for a specific day.

        Args:
            user_id: Unique user identifier.
            log_date: Date to retrieve.

        Returns:
            ShortTermMemory for the day or None.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT data FROM daily_logs WHERE user_id = ? AND date = ?",
                (user_id, log_date.isoformat())
            )
            row = cursor.fetchone()

        if not row:
            return None
        return ShortTermMemory(**json.loads(row["data"]))

    def cleanup_expired(self) -> int:
        """
        Remove records older than retention period.

        Returns:
            Number of records deleted.
        """
        cutoff_date = date.today() - timedelta(days=self.retention_days)

        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM daily_logs WHERE date < ?",
                (cutoff_date.isoformat(),)
            )
            conn.commit()
            return cursor.rowcount

    def get_summary(self, user_id: str, days: int = 7) -> Dict:
        """
        Get summary statistics for recent activity.

        Args:
            user_id: User identifier.
            days: Number of days to summarize.

        Returns:
            Dict with avg_calories, avg_protein, workout_count, avg_sleep_quality.
        """
        records = self.get_recent(user_id, days)
        if not records:
            return {
                "avg_calories": 0,
                "avg_protein": 0,
                "workout_count": 0,
                "avg_sleep_quality": 0
            }

        total_calories = sum(r.calories_consumed for r in records)
        total_protein = sum(r.protein_total for r in records)
        workout_count = sum(len(r.workouts) for r in records)
        sleep_qualities = [r.sleep.quality for r in records if r.sleep]

        return {
            "avg_calories": total_calories // len(records) if records else 0,
            "avg_protein": total_protein // len(records) if records else 0,
            "workout_count": workout_count,
            "avg_sleep_quality": sum(sleep_qualities) / len(sleep_qualities) if sleep_qualities else 0
        }
