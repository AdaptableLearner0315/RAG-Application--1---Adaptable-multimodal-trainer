"""
Unit tests for WorkingMemoryStore.
Tests 5 edge cases for session-based memory.
"""

import pytest
from unittest.mock import MagicMock

from app.memory.working import WorkingMemoryStore


class TestWorkingMemoryStore:
    """Unit tests for WorkingMemoryStore class."""

    @pytest.fixture
    def store(self) -> WorkingMemoryStore:
        """Create WorkingMemoryStore with in-memory fallback."""
        return WorkingMemoryStore(redis_client=None)

    @pytest.fixture
    def store_with_mock_redis(self) -> tuple:
        """Create store with mock Redis client."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.expire.return_value = True

        store = WorkingMemoryStore(redis_client=mock_redis)
        return store, mock_redis

    # ==================== EDGE CASE 1: Session not found ====================
    def test_get_nonexistent_session_returns_none(self, store: WorkingMemoryStore):
        """
        GIVEN session that doesn't exist
        WHEN get() is called
        THEN None is returned
        """
        result = store.get("user_123", "nonexistent_session")
        assert result is None

    # ==================== EDGE CASE 2: Redis connection fails ====================
    def test_fallback_when_redis_unavailable(self):
        """
        GIVEN Redis client that fails to connect
        WHEN WorkingMemoryStore is initialized
        THEN fallback to in-memory store is used
        """
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = ConnectionError("Redis unavailable")

        store = WorkingMemoryStore(redis_client=mock_redis)

        # Should use fallback
        assert store._use_fallback is True

        # Operations should still work
        session = store.create_session("user_1", "session_1")
        assert session is not None

    # ==================== EDGE CASE 3: Clear nonexistent session ====================
    def test_clear_nonexistent_returns_false(self, store: WorkingMemoryStore):
        """
        GIVEN session that doesn't exist
        WHEN clear() is called
        THEN False is returned
        """
        result = store.clear("user_123", "nonexistent_session")
        assert result is False

    # ==================== EDGE CASE 4: Empty conversation history ====================
    def test_get_recent_messages_empty_session(self, store: WorkingMemoryStore):
        """
        GIVEN session with no messages
        WHEN get_recent_messages() is called
        THEN empty list is returned
        """
        result = store.get_recent_messages("user_123", "no_messages_session", count=5)
        assert result == []

    # ==================== EDGE CASE 5: Extend TTL on nonexistent session ====================
    def test_extend_ttl_nonexistent_returns_false(self, store: WorkingMemoryStore):
        """
        GIVEN session that doesn't exist
        WHEN extend_ttl() is called
        THEN False is returned
        """
        result = store.extend_ttl("user_123", "nonexistent_session")
        assert result is False

    # ==================== Additional Tests ====================
    def test_create_session(self, store: WorkingMemoryStore):
        """Test creating new session."""
        session = store.create_session("user_1", "session_1")

        assert session is not None
        assert session.user_id == "user_1"
        assert session.session_id == "session_1"
        assert session.conversation == []

    def test_get_existing_session(self, store: WorkingMemoryStore):
        """Test retrieving existing session."""
        store.create_session("user_1", "session_1")

        result = store.get("user_1", "session_1")

        assert result is not None
        assert result.user_id == "user_1"

    def test_add_message(self, store: WorkingMemoryStore):
        """Test adding message to conversation."""
        store.create_session("user_1", "session_1")

        store.add_message("user_1", "session_1", "user", "Hello!")

        session = store.get("user_1", "session_1")
        assert len(session.conversation) == 1
        assert session.conversation[0]["role"] == "user"
        assert session.conversation[0]["content"] == "Hello!"

    def test_add_message_creates_session_if_not_exists(self, store: WorkingMemoryStore):
        """Test that add_message creates session if it doesn't exist."""
        store.add_message("new_user", "new_session", "user", "First message")

        session = store.get("new_user", "new_session")
        assert session is not None
        assert len(session.conversation) == 1

    def test_get_recent_messages_limits_count(self, store: WorkingMemoryStore):
        """Test that get_recent_messages respects count limit."""
        store.create_session("user_1", "session_1")

        # Add 10 messages
        for i in range(10):
            store.add_message("user_1", "session_1", "user", f"Message {i}")

        # Get only last 3
        messages = store.get_recent_messages("user_1", "session_1", count=3)

        assert len(messages) == 3
        assert messages[-1]["content"] == "Message 9"  # Most recent

    def test_set_active_agent(self, store: WorkingMemoryStore):
        """Test setting active agent."""
        store.create_session("user_1", "session_1")

        store.set_active_agent("user_1", "session_1", "nutritionist")

        session = store.get("user_1", "session_1")
        assert session.current_agent == "nutritionist"

    def test_set_context(self, store: WorkingMemoryStore):
        """Test setting pending context."""
        store.create_session("user_1", "session_1")
        context = {"documents": ["doc1", "doc2"], "tool_results": {"search": []}}

        store.set_context("user_1", "session_1", context)

        session = store.get("user_1", "session_1")
        assert session.pending_context == context

    def test_clear_session(self, store: WorkingMemoryStore):
        """Test clearing session."""
        store.create_session("user_1", "session_1")
        store.add_message("user_1", "session_1", "user", "Hello!")

        result = store.clear("user_1", "session_1")

        assert result is True
        assert store.get("user_1", "session_1") is None

    def test_extend_ttl_existing_session(self, store: WorkingMemoryStore):
        """Test extending TTL on existing session."""
        store.create_session("user_1", "session_1")

        result = store.extend_ttl("user_1", "session_1")

        assert result is True

    def test_multiple_sessions_per_user(self, store: WorkingMemoryStore):
        """Test multiple concurrent sessions for same user."""
        store.create_session("user_1", "session_a")
        store.create_session("user_1", "session_b")

        store.add_message("user_1", "session_a", "user", "Message A")
        store.add_message("user_1", "session_b", "user", "Message B")

        session_a = store.get("user_1", "session_a")
        session_b = store.get("user_1", "session_b")

        assert session_a.conversation[0]["content"] == "Message A"
        assert session_b.conversation[0]["content"] == "Message B"
