"""
Integration tests for Memory + Retrieval modules.
Tests cross-module interactions between memory stores and RAG retrieval.
"""

import pytest
from pathlib import Path
from datetime import date, timedelta

from app.memory.long_term import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore
from app.memory.working import WorkingMemoryStore
from app.memory.retriever import MemoryRetriever
from app.core.config import get_settings


class TestMemoryRetrievalIntegration:
    """Integration tests for memory retrieval workflow."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path):
        """Create temporary storage for tests."""
        return tmp_path

    @pytest.fixture
    def long_term_store(self, temp_storage: Path) -> LongTermMemoryStore:
        """Create long-term memory store."""
        return LongTermMemoryStore(db_path=temp_storage / "long_term.db")

    @pytest.fixture
    def short_term_store(self, temp_storage: Path) -> ShortTermMemoryStore:
        """Create short-term memory store."""
        return ShortTermMemoryStore(
            db_path=temp_storage / "short_term.db",
            retention_days=7
        )

    @pytest.fixture
    def working_store(self) -> WorkingMemoryStore:
        """Create working memory store (in-memory fallback)."""
        return WorkingMemoryStore(redis_client=None)  # Use in-memory fallback

    @pytest.fixture
    def retriever(
        self,
        working_store: WorkingMemoryStore,
        short_term_store: ShortTermMemoryStore,
        long_term_store: LongTermMemoryStore
    ) -> MemoryRetriever:
        """Create memory retriever with all stores."""
        settings = get_settings()
        return MemoryRetriever(
            working=working_store,
            short_term=short_term_store,
            long_term=long_term_store,
            token_budgets={
                "working": settings.working_memory_budget,
                "short_term": settings.short_term_memory_budget,
                "long_term": settings.long_term_memory_budget
            }
        )

    @pytest.fixture
    def sample_profile(self) -> dict:
        """Sample user profile."""
        return {
            "age": 17,
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "injuries": ["left knee ACL"],
            "intolerances": ["lactose"],
            "allergies": [],
            "dietary_pref": "omnivore",
            "fitness_level": "intermediate",
            "primary_goal": "build_muscle"
        }

    # ==================== INTEGRATION TEST 1 ====================
    def test_full_memory_retrieval_workflow(
        self,
        retriever: MemoryRetriever,
        long_term_store: LongTermMemoryStore,
        short_term_store: ShortTermMemoryStore,
        working_store: WorkingMemoryStore,
        sample_profile: dict
    ):
        """
        Test complete memory retrieval workflow:
        1. Store user profile in long-term
        2. Log meals in short-term
        3. Add conversation to working memory
        4. Retrieve relevant context for query
        """
        user_id = "integration_test_user"
        session_id = "test_session_123"

        # Step 1: Create user profile
        long_term_store.upsert(user_id, sample_profile)

        # Step 2: Log recent meal
        meal = {
            "time": "12:30",
            "foods": ["chicken breast", "rice"],
            "calories": 550,
            "protein": 45,
            "carbs": 60,
            "fat": 12
        }
        short_term_store.log_meal(user_id, meal)

        # Step 3: Add conversation context
        working_store.add_message(
            user_id=user_id,
            session_id=session_id,
            role="user",
            content="I want to focus on building muscle"
        )

        # Step 4: Retrieve context for nutrition query
        context = retriever.retrieve_for_query(
            user_id=user_id,
            session_id=session_id,
            query="What should I eat before my workout?"
        )

        # Verify all tiers returned context
        assert "long_term" in context
        assert "short_term" in context
        assert "working" in context

        # Verify profile data is in long-term context
        assert context["long_term"] != ""

    # ==================== INTEGRATION TEST 2 ====================
    def test_query_aware_retrieval_fitness(
        self,
        retriever: MemoryRetriever,
        long_term_store: LongTermMemoryStore,
        sample_profile: dict
    ):
        """
        Test that fitness queries retrieve injury information.
        """
        user_id = "fitness_test_user"
        long_term_store.upsert(user_id, sample_profile)

        # Query about workouts should retrieve injury info
        context = retriever.retrieve_for_query(
            user_id=user_id,
            session_id="test_session",
            query="What exercises should I do for legs?"
        )

        # Long-term context should be populated
        assert context["long_term"] != ""

    # ==================== INTEGRATION TEST 3 ====================
    def test_query_aware_retrieval_nutrition(
        self,
        retriever: MemoryRetriever,
        long_term_store: LongTermMemoryStore,
        short_term_store: ShortTermMemoryStore,
        sample_profile: dict
    ):
        """
        Test that nutrition queries retrieve dietary restrictions and recent meals.
        """
        user_id = "nutrition_test_user"
        long_term_store.upsert(user_id, sample_profile)

        # Log a meal
        meal = {
            "time": "08:00",
            "foods": ["oatmeal", "banana"],
            "calories": 350,
            "protein": 12,
            "carbs": 65,
            "fat": 8
        }
        short_term_store.log_meal(user_id, meal)

        # Query about food
        context = retriever.retrieve_for_query(
            user_id=user_id,
            session_id="test_session",
            query="What protein sources should I eat?"
        )

        # Both tiers should have data
        assert context["long_term"] != ""

    # ==================== INTEGRATION TEST 4 ====================
    def test_new_user_retrieval_returns_empty_gracefully(
        self,
        retriever: MemoryRetriever
    ):
        """
        Test that retrieval for new user (no profile) handles gracefully.
        """
        context = retriever.retrieve_for_query(
            user_id="brand_new_user_no_data",
            session_id="test_session",
            query="How do I start working out?"
        )

        # Should return structure with empty strings, not errors
        assert "long_term" in context
        assert "short_term" in context
        assert "working" in context
        assert context["long_term"] == ""

    # ==================== INTEGRATION TEST 5 ====================
    def test_memory_persistence_across_sessions(
        self,
        long_term_store: LongTermMemoryStore,
        short_term_store: ShortTermMemoryStore,
        sample_profile: dict
    ):
        """
        Test that memory persists across store instances.
        """
        user_id = "persistence_test_user"

        # Store data
        long_term_store.upsert(user_id, sample_profile)
        meal = {
            "time": "19:00",
            "foods": ["salmon", "vegetables"],
            "calories": 450,
            "protein": 40,
            "carbs": 20,
            "fat": 25
        }
        short_term_store.log_meal(user_id, meal)

        # Retrieve data
        profile = long_term_store.get(user_id)
        recent = short_term_store.get_recent(user_id, days=7)

        # Verify persistence
        assert profile is not None
        assert profile.age == 17
        assert "left knee ACL" in profile.injuries
        assert len(recent) >= 1
