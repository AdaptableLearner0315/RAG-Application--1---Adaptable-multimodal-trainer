"""
Unit tests for chat API endpoint.
Tests 5 edge cases for the chat route.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.memory.schemas import LongTermMemory


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_profile():
    """Sample user profile."""
    return LongTermMemory(
        user_id="test_user_123",
        age=17,
        height_cm=175.0,
        weight_kg=70.0,
        injuries=[],
        intolerances=[],
        allergies=[],
        dietary_pref="omnivore",
        fitness_level="beginner",
        primary_goal="build_muscle"
    )


class TestChatEndpoint:
    """Unit tests for POST /api/chat endpoint."""

    # Edge Case 1: New user without profile
    @patch("app.api.routes.chat.get_long_term_store")
    def test_chat_new_user_returns_onboarding(self, mock_store, client):
        """
        GIVEN a new user with no profile
        WHEN chat endpoint is called
        THEN onboarding message is returned.
        """
        mock_store.return_value.get.return_value = None

        response = client.post(
            "/api/chat",
            json={
                "message": "Hello!",
                "user_id": "new_user_123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "Welcome" in data["response"]
        assert data["agent"] == "system"

    # Edge Case 2: Empty message
    def test_chat_empty_message_rejected(self, client):
        """
        GIVEN an empty message
        WHEN chat endpoint is called
        THEN 422 validation error is returned.
        """
        response = client.post(
            "/api/chat",
            json={
                "message": "",
                "user_id": "test_user"
            }
        )

        assert response.status_code == 422

    # Edge Case 3: Invalid user ID
    def test_chat_invalid_user_id_rejected(self, client):
        """
        GIVEN an empty user_id
        WHEN chat endpoint is called
        THEN 400 error is returned.
        """
        response = client.post(
            "/api/chat",
            json={
                "message": "Hello",
                "user_id": "   "
            }
        )

        assert response.status_code == 400
        assert "user_id" in response.json()["detail"].lower()

    # Edge Case 4: Harmful content blocked
    @patch("app.api.routes.chat.TextProcessor")
    @patch("app.api.routes.chat.get_long_term_store")
    def test_chat_harmful_content_blocked(
        self, mock_store, mock_processor, client, mock_profile
    ):
        """
        GIVEN a message with harmful content
        WHEN chat endpoint is called
        THEN request is blocked with 400 error.
        """
        mock_store.return_value.get.return_value = mock_profile

        # Mock safety check to fail
        mock_instance = Mock()
        mock_instance.check_safety.return_value = Mock(
            is_safe=False,
            reason="Potentially harmful weight loss request"
        )
        mock_processor.return_value = mock_instance

        response = client.post(
            "/api/chat",
            json={
                "message": "How to lose 30 pounds in one week?",
                "user_id": "test_user_123"
            }
        )

        assert response.status_code == 400
        assert "blocked" in response.json()["detail"].lower()

    # Edge Case 5: Message too long
    def test_chat_message_too_long_rejected(self, client):
        """
        GIVEN a message exceeding max length
        WHEN chat endpoint is called
        THEN 422 validation error is returned.
        """
        long_message = "a" * 5000  # Max is 4096

        response = client.post(
            "/api/chat",
            json={
                "message": long_message,
                "user_id": "test_user"
            }
        )

        assert response.status_code == 422


class TestChatHealth:
    """Tests for chat health endpoint."""

    def test_chat_health_returns_healthy(self, client):
        """
        GIVEN the chat service is running
        WHEN health endpoint is called
        THEN healthy status is returned.
        """
        response = client.get("/api/chat/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
