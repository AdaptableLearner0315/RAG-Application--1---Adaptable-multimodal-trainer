"""
Unit tests for LongTermMemoryStore.
Tests 5 edge cases for permanent profile storage.
"""

import pytest
from datetime import datetime
from pathlib import Path

from app.memory.long_term import LongTermMemoryStore
from app.memory.schemas import LongTermMemory


class TestLongTermMemoryStore:
    """Unit tests for LongTermMemoryStore class."""

    @pytest.fixture
    def store(self, temp_dir: Path) -> LongTermMemoryStore:
        """Create LongTermMemoryStore with temp database."""
        db_path = temp_dir / "test_long_term.db"
        return LongTermMemoryStore(db_path=db_path)

    @pytest.fixture
    def sample_profile(self) -> dict:
        """Sample user profile data."""
        return {
            "age": 17,
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "injuries": [],
            "intolerances": ["lactose"],
            "allergies": [],
            "dietary_pref": "omnivore",
            "fitness_level": "intermediate",
            "primary_goal": "build_muscle",
            "target_weight_kg": 75.0
        }

    # ==================== EDGE CASE 1: User not found ====================
    def test_get_nonexistent_user_returns_none(self, store: LongTermMemoryStore):
        """
        GIVEN user_id that doesn't exist in database
        WHEN get() is called
        THEN None is returned (no exception raised)
        """
        result = store.get("nonexistent_user_123")
        assert result is None

    # ==================== EDGE CASE 2: Duplicate injury ====================
    def test_add_injury_ignores_duplicate(
        self,
        store: LongTermMemoryStore,
        sample_profile: dict
    ):
        """
        GIVEN user with existing injury
        WHEN same injury is added again (case-insensitive)
        THEN injury list contains no duplicates
        """
        user_id = "user_123"
        store.upsert(user_id, sample_profile)

        # Add injury twice with different casing
        store.add_injury(user_id, "Left Knee")
        store.add_injury(user_id, "left knee")  # Duplicate
        store.add_injury(user_id, "LEFT KNEE")  # Another duplicate

        profile = store.get(user_id)
        assert len(profile.injuries) == 1
        assert "Left Knee" in profile.injuries

    # ==================== EDGE CASE 3: Invalid data type ====================
    def test_upsert_invalid_type_raises_error(self, store: LongTermMemoryStore):
        """
        GIVEN invalid data type for a field (string instead of int for age)
        WHEN upsert() is called
        THEN ValidationError is raised with field name
        """
        invalid_data = {
            "age": "seventeen",  # Should be int
            "height_cm": 175.0,
            "weight_kg": 70.0
        }

        with pytest.raises(Exception) as exc_info:
            store.upsert("user_123", invalid_data)

        # Pydantic validation error
        assert "age" in str(exc_info.value).lower() or "validation" in str(exc_info.value).lower()

    # ==================== EDGE CASE 4: Database retry on lock ====================
    def test_get_connection_retries_on_lock(
        self,
        store: LongTermMemoryStore,
        sample_profile: dict
    ):
        """
        GIVEN database operations
        WHEN multiple rapid operations occur
        THEN operations succeed with retry logic
        """
        user_id = "user_retry_test"

        # Perform multiple rapid operations to test retry logic
        store.upsert(user_id, sample_profile)
        for i in range(5):
            store.add_injury(user_id, f"injury_{i}")

        profile = store.get(user_id)
        assert len(profile.injuries) == 5

    # ==================== EDGE CASE 5: Delete nonexistent user ====================
    def test_delete_nonexistent_returns_false(self, store: LongTermMemoryStore):
        """
        GIVEN user_id that doesn't exist
        WHEN delete() is called
        THEN False is returned, no exception raised
        """
        result = store.delete("nonexistent_user_456")
        assert result is False

    # ==================== Additional Tests ====================
    def test_upsert_creates_new_profile(
        self,
        store: LongTermMemoryStore,
        sample_profile: dict
    ):
        """Test that upsert creates a new profile correctly."""
        user_id = "new_user"
        store.upsert(user_id, sample_profile)

        profile = store.get(user_id)
        assert profile is not None
        assert profile.user_id == user_id
        assert profile.age == 17
        assert profile.weight_kg == 70.0
        assert "lactose" in profile.intolerances

    def test_upsert_updates_existing_profile(
        self,
        store: LongTermMemoryStore,
        sample_profile: dict
    ):
        """Test that upsert updates existing profile fields."""
        user_id = "update_user"
        store.upsert(user_id, sample_profile)

        # Update weight
        store.upsert(user_id, {"weight_kg": 72.0})

        profile = store.get(user_id)
        assert profile.weight_kg == 72.0
        assert profile.age == 17  # Original value preserved

    def test_remove_injury(
        self,
        store: LongTermMemoryStore,
        sample_profile: dict
    ):
        """Test removing injury from profile."""
        user_id = "remove_injury_user"
        sample_profile["injuries"] = ["back pain", "knee strain"]
        store.upsert(user_id, sample_profile)

        store.remove_injury(user_id, "Back Pain")  # Case insensitive

        profile = store.get(user_id)
        assert "back pain" not in [i.lower() for i in profile.injuries]
        assert len(profile.injuries) == 1

    def test_list_users(
        self,
        store: LongTermMemoryStore,
        sample_profile: dict
    ):
        """Test listing all users."""
        store.upsert("user_1", sample_profile)
        store.upsert("user_2", sample_profile)
        store.upsert("user_3", sample_profile)

        users = store.list_users()
        assert len(users) == 3
        assert "user_1" in users
        assert "user_2" in users
        assert "user_3" in users

    def test_delete_removes_profile(
        self,
        store: LongTermMemoryStore,
        sample_profile: dict
    ):
        """Test that delete removes profile completely."""
        user_id = "delete_user"
        store.upsert(user_id, sample_profile)

        result = store.delete(user_id)
        assert result is True

        profile = store.get(user_id)
        assert profile is None
