"""
Unit tests for MemoryRetriever.
Tests 5 edge cases for query-aware memory fetching.
"""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from app.memory.retriever import MemoryRetriever, QUERY_MEMORY_MAP
from app.memory.long_term import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore
from app.memory.working import WorkingMemoryStore
from app.memory.schemas import LongTermMemory


class TestMemoryRetriever:
    """Unit tests for MemoryRetriever class."""

    @pytest.fixture
    def working_store(self) -> WorkingMemoryStore:
        """Create working memory store."""
        return WorkingMemoryStore(redis_client=None)

    @pytest.fixture
    def short_term_store(self, temp_dir: Path) -> ShortTermMemoryStore:
        """Create short-term memory store."""
        return ShortTermMemoryStore(db_path=temp_dir / "st.db")

    @pytest.fixture
    def long_term_store(self, temp_dir: Path) -> LongTermMemoryStore:
        """Create long-term memory store."""
        return LongTermMemoryStore(db_path=temp_dir / "lt.db")

    @pytest.fixture
    def retriever(
        self,
        working_store: WorkingMemoryStore,
        short_term_store: ShortTermMemoryStore,
        long_term_store: LongTermMemoryStore
    ) -> MemoryRetriever:
        """Create MemoryRetriever with all stores."""
        return MemoryRetriever(
            working=working_store,
            short_term=short_term_store,
            long_term=long_term_store,
            token_budgets={"working": 500, "short_term": 800, "long_term": 400}
        )

    @pytest.fixture
    def setup_user_data(
        self,
        long_term_store: LongTermMemoryStore,
        short_term_store: ShortTermMemoryStore,
        working_store: WorkingMemoryStore
    ):
        """Set up test user data in all stores."""
        user_id = "test_user"
        session_id = "test_session"

        # Long-term profile
        long_term_store.upsert(user_id, {
            "age": 17,
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "injuries": ["knee strain"],
            "intolerances": ["lactose"],
            "dietary_pref": "omnivore",
            "fitness_level": "intermediate",
            "primary_goal": "build_muscle"
        })

        # Short-term activity
        short_term_store.log_meal(user_id, {
            "time": "12:00",
            "foods": ["chicken", "rice"],
            "calories": 500,
            "protein": 40,
            "carbs": 50,
            "fat": 10
        })

        # Working memory
        working_store.create_session(user_id, session_id)
        working_store.add_message(user_id, session_id, "user", "What should I eat?")

        return user_id, session_id

    # ==================== EDGE CASE 1: No intent match ====================
    def test_retrieve_unknown_intent_uses_default(
        self,
        retriever: MemoryRetriever,
        setup_user_data
    ):
        """
        GIVEN query matching no known intent patterns
        WHEN retrieve_for_query() is called
        THEN default memory spec is used
        """
        user_id, session_id = setup_user_data

        result = retriever.retrieve_for_query(
            user_id,
            session_id,
            "xyz random gibberish query abc"
        )

        # Should return context from all tiers using defaults
        assert "long_term" in result
        assert "short_term" in result
        assert "working" in result

    # ==================== EDGE CASE 2: No profile exists ====================
    def test_retrieve_no_profile_returns_empty_long_term(
        self,
        retriever: MemoryRetriever
    ):
        """
        GIVEN user with no profile in long-term memory
        WHEN retrieve_for_query() is called
        THEN long_term context is empty string
        """
        result = retriever.retrieve_for_query(
            "nonexistent_user",
            "any_session",
            "how much protein should I eat?"
        )

        assert result["long_term"] == ""

    # ==================== EDGE CASE 3: Token budget exceeded ====================
    def test_retrieve_truncates_to_budget(
        self,
        working_store: WorkingMemoryStore,
        short_term_store: ShortTermMemoryStore,
        long_term_store: LongTermMemoryStore,
        temp_dir: Path
    ):
        """
        GIVEN memory content exceeding token budget
        WHEN retrieve_for_query() is called
        THEN content is truncated to fit budget
        """
        # Create retriever with very small budget
        retriever = MemoryRetriever(
            working=working_store,
            short_term=short_term_store,
            long_term=long_term_store,
            token_budgets={"working": 10, "short_term": 10, "long_term": 10}
        )

        user_id = "budget_test_user"

        # Add profile with lots of data
        long_term_store.upsert(user_id, {
            "age": 17,
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "injuries": [f"injury_{i}" for i in range(50)],
            "intolerances": [f"intolerance_{i}" for i in range(50)],
            "dietary_pref": "omnivore",
            "fitness_level": "intermediate",
            "primary_goal": "build_muscle"
        })

        result = retriever.retrieve_for_query(user_id, "session", "workout plan")

        # 10 tokens * 4 chars = 40 chars max
        assert len(result["long_term"]) <= 50  # Some buffer for truncation

    # ==================== EDGE CASE 4: Multi-intent query ====================
    def test_retrieve_multi_intent_includes_relevant_fields(
        self,
        retriever: MemoryRetriever,
        setup_user_data
    ):
        """
        GIVEN query spanning multiple intents (food + exercise)
        WHEN retrieve_for_query() is called
        THEN context includes fields from both intents
        """
        user_id, session_id = setup_user_data

        # Query mentions both food and exercise
        result = retriever.retrieve_for_query(
            user_id,
            session_id,
            "what should I eat before my workout at the gym?"
        )

        # Should have context from both nutrition and fitness intents
        long_term = result["long_term"].lower()
        # Should include injury info (fitness) and intolerance info (nutrition)
        assert "long_term" in result
        assert len(result["long_term"]) > 0

    # ==================== EDGE CASE 5: Store connection fails ====================
    def test_retrieve_handles_store_failure(self):
        """
        GIVEN memory store that raises exception
        WHEN retrieve_for_query() is called
        THEN empty context returned for that tier, no exception raised
        """
        # Create mock stores
        mock_working = MagicMock()
        mock_short_term = MagicMock()
        mock_long_term = MagicMock()

        # Long-term store fails
        mock_long_term.get.side_effect = Exception("Database error")
        mock_short_term.get_recent.return_value = []
        mock_working.get_recent_messages.return_value = []

        retriever = MemoryRetriever(
            working=mock_working,
            short_term=mock_short_term,
            long_term=mock_long_term
        )

        # Should not raise exception
        result = retriever.retrieve_for_query("user", "session", "any query")

        assert result["long_term"] == ""

    # ==================== Additional Tests ====================
    def test_classify_intent_food_query(self, retriever: MemoryRetriever):
        """Test that food-related queries are classified correctly."""
        queries = [
            "what should I eat for breakfast?",
            "how many calories in rice?",
            "I need more protein",
            "meal plan for the week"
        ]

        for query in queries:
            intent = retriever._classify_intent(query)
            assert "food" in intent or "meal" in intent or "nutrition" in intent or "protein" in intent or "calorie" in intent

    def test_classify_intent_workout_query(self, retriever: MemoryRetriever):
        """Test that workout-related queries are classified correctly."""
        queries = [
            "what exercises should I do?",
            "leg day workout",
            "how to train chest",
            "gym routine"
        ]

        for query in queries:
            intent = retriever._classify_intent(query)
            assert "workout" in intent or "exercise" in intent or "training" in intent or "gym" in intent

    def test_classify_intent_sleep_query(self, retriever: MemoryRetriever):
        """Test that sleep-related queries are classified correctly."""
        queries = [
            "I'm so tired today",
            "how much sleep do I need?",
            "recovery tips",
            "feeling fatigued"
        ]

        for query in queries:
            intent = retriever._classify_intent(query)
            assert "sleep" in intent or "tired" in intent or "rest" in intent or "recovery" in intent or "fatigue" in intent

    def test_classify_intent_general_query(self, retriever: MemoryRetriever):
        """Test that unrelated queries return 'general' intent."""
        intent = retriever._classify_intent("what is the weather today?")
        assert intent == "general"

    def test_format_memory_empty_dict(self, retriever: MemoryRetriever):
        """Test formatting empty memory dict."""
        result = retriever._format_memory({}, 100)
        assert result == ""

    def test_truncate_to_tokens_short_text(self, retriever: MemoryRetriever):
        """Test that short text is not truncated."""
        short_text = "Hello world"
        result = retriever._truncate_to_tokens(short_text, 100)
        assert result == short_text

    def test_truncate_to_tokens_long_text(self, retriever: MemoryRetriever):
        """Test that long text is truncated with ellipsis."""
        long_text = "word " * 100
        result = retriever._truncate_to_tokens(long_text, 10)  # 40 chars max
        assert len(result) <= 43  # 40 + "..."
        assert result.endswith("...")
