"""
Unit tests for ShortTermMemoryStore.
Tests 5 edge cases for 7-day rolling activity memory.
"""

import pytest
from datetime import date, timedelta
from pathlib import Path

from app.memory.short_term import ShortTermMemoryStore


class TestShortTermMemoryStore:
    """Unit tests for ShortTermMemoryStore class."""

    @pytest.fixture
    def store(self, temp_dir: Path) -> ShortTermMemoryStore:
        """Create ShortTermMemoryStore with temp database."""
        db_path = temp_dir / "test_short_term.db"
        return ShortTermMemoryStore(db_path=db_path, retention_days=7)

    @pytest.fixture
    def valid_meal(self) -> dict:
        """Valid meal data."""
        return {
            "time": "12:30",
            "foods": ["chicken breast", "rice", "broccoli"],
            "calories": 550,
            "protein": 45,
            "carbs": 60,
            "fat": 12
        }

    @pytest.fixture
    def valid_workout(self) -> dict:
        """Valid workout data."""
        return {
            "time": "16:00",
            "type": "strength",
            "duration_min": 60,
            "intensity": "moderate",
            "exercises": ["squats", "lunges"]
        }

    # ==================== EDGE CASE 1: Missing required fields ====================
    def test_log_meal_missing_fields_raises_error(self, store: ShortTermMemoryStore):
        """
        GIVEN meal data missing required fields
        WHEN log_meal() is called
        THEN ValueError is raised listing missing fields
        """
        incomplete_meal = {"foods": ["apple"]}  # Missing calories, protein, carbs, fat, time

        with pytest.raises(ValueError) as exc_info:
            store.log_meal("user_123", incomplete_meal)

        error_msg = str(exc_info.value).lower()
        assert "missing" in error_msg or "required" in error_msg

    # ==================== EDGE CASE 2: New user returns empty ====================
    def test_get_recent_new_user_returns_empty(self, store: ShortTermMemoryStore):
        """
        GIVEN user with no logged data
        WHEN get_recent() is called
        THEN empty list is returned
        """
        result = store.get_recent("brand_new_user")
        assert result == []

    # ==================== EDGE CASE 3: Boundary date inclusion ====================
    def test_get_recent_includes_boundary_date(
        self,
        store: ShortTermMemoryStore,
        valid_meal: dict
    ):
        """
        GIVEN meal logged exactly 7 days ago
        WHEN get_recent(days=7) is called
        THEN that meal is included (inclusive boundary)
        """
        user_id = "boundary_user"
        boundary_date = date.today() - timedelta(days=7)

        store.log_meal(user_id, valid_meal, log_date=boundary_date)

        result = store.get_recent(user_id, days=7)
        assert len(result) == 1
        assert result[0].date == boundary_date

    # ==================== EDGE CASE 4: Negative values rejected ====================
    def test_log_meal_negative_calories_raises_error(self, store: ShortTermMemoryStore):
        """
        GIVEN meal with negative calories
        WHEN log_meal() is called
        THEN ValueError is raised
        """
        bad_meal = {
            "time": "12:00",
            "foods": ["salad"],
            "calories": -100,  # Invalid
            "protein": 10,
            "carbs": 15,
            "fat": 5
        }

        with pytest.raises(ValueError) as exc_info:
            store.log_meal("user_123", bad_meal)

        assert "negative" in str(exc_info.value).lower()

    # ==================== EDGE CASE 5: Cleanup with nothing to clean ====================
    def test_cleanup_no_expired_returns_zero(self, store: ShortTermMemoryStore):
        """
        GIVEN no expired records exist
        WHEN cleanup_expired() is called
        THEN 0 is returned
        """
        result = store.cleanup_expired()
        assert result == 0

    # ==================== Additional Tests ====================
    def test_log_meal_creates_daily_record(
        self,
        store: ShortTermMemoryStore,
        valid_meal: dict
    ):
        """Test that logging meal creates daily record."""
        user_id = "meal_user"
        store.log_meal(user_id, valid_meal)

        records = store.get_recent(user_id, days=1)
        assert len(records) == 1
        assert len(records[0].meals) == 1
        assert records[0].calories_consumed == 550

    def test_log_workout_updates_calories_burned(
        self,
        store: ShortTermMemoryStore,
        valid_workout: dict
    ):
        """Test that logging workout updates calories burned estimate."""
        user_id = "workout_user"
        store.log_workout(user_id, valid_workout)

        records = store.get_recent(user_id, days=1)
        assert len(records) == 1
        assert records[0].calories_burned > 0

    def test_log_workout_negative_duration_raises_error(
        self,
        store: ShortTermMemoryStore
    ):
        """Test that negative duration is rejected."""
        bad_workout = {
            "time": "16:00",
            "type": "strength",
            "duration_min": -30,  # Invalid
            "intensity": "moderate"
        }

        with pytest.raises(ValueError) as exc_info:
            store.log_workout("user_123", bad_workout)

        assert "duration" in str(exc_info.value).lower() or "positive" in str(exc_info.value).lower()

    def test_log_sleep(self, store: ShortTermMemoryStore):
        """Test logging sleep data."""
        user_id = "sleep_user"
        sleep_data = {
            "bed_time": "23:00",
            "wake_time": "07:00",
            "quality": 4
        }

        store.log_sleep(user_id, sleep_data)

        records = store.get_recent(user_id, days=1)
        assert len(records) == 1
        assert records[0].sleep is not None
        assert records[0].sleep.quality == 4

    def test_get_day_specific_date(
        self,
        store: ShortTermMemoryStore,
        valid_meal: dict
    ):
        """Test getting data for specific date."""
        user_id = "day_user"
        target_date = date.today() - timedelta(days=3)

        store.log_meal(user_id, valid_meal, log_date=target_date)

        result = store.get_day(user_id, target_date)
        assert result is not None
        assert result.date == target_date

    def test_get_day_nonexistent_returns_none(self, store: ShortTermMemoryStore):
        """Test getting nonexistent day returns None."""
        result = store.get_day("user_123", date.today())
        assert result is None

    def test_cleanup_removes_old_records(
        self,
        store: ShortTermMemoryStore,
        valid_meal: dict
    ):
        """Test that cleanup removes old records."""
        user_id = "cleanup_user"

        # Log old meal (8 days ago, outside retention)
        old_date = date.today() - timedelta(days=8)
        store.log_meal(user_id, valid_meal, log_date=old_date)

        # Log recent meal
        store.log_meal(user_id, valid_meal)

        # Cleanup should remove old record
        deleted = store.cleanup_expired()
        assert deleted == 1

        # Only recent record should remain
        records = store.get_recent(user_id, days=10)
        assert len(records) == 1

    def test_get_summary(
        self,
        store: ShortTermMemoryStore,
        valid_meal: dict,
        valid_workout: dict
    ):
        """Test getting activity summary."""
        user_id = "summary_user"

        # Log data for multiple days
        for i in range(3):
            log_date = date.today() - timedelta(days=i)
            store.log_meal(user_id, valid_meal, log_date=log_date)
            store.log_workout(user_id, valid_workout, log_date=log_date)

        summary = store.get_summary(user_id, days=7)

        assert summary["avg_calories"] > 0
        assert summary["avg_protein"] > 0
        assert summary["workout_count"] == 3

    def test_multiple_meals_same_day(
        self,
        store: ShortTermMemoryStore
    ):
        """Test logging multiple meals on same day."""
        user_id = "multi_meal_user"

        meals = [
            {"time": "08:00", "foods": ["oatmeal"], "calories": 300, "protein": 10, "carbs": 50, "fat": 5},
            {"time": "12:00", "foods": ["sandwich"], "calories": 500, "protein": 25, "carbs": 40, "fat": 20},
            {"time": "19:00", "foods": ["salmon"], "calories": 600, "protein": 40, "carbs": 30, "fat": 25}
        ]

        for meal in meals:
            store.log_meal(user_id, meal)

        records = store.get_recent(user_id, days=1)
        assert len(records) == 1
        assert len(records[0].meals) == 3
        assert records[0].calories_consumed == 1400  # Sum of all meals
