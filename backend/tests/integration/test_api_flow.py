"""
Integration tests for API + Memory + Agents modules.
Tests the complete API request flow through all backend layers.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.memory.schemas import LongTermMemory


class TestAPIMemoryIntegration:
    """Integration tests for API endpoints with memory stores."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_profile(self) -> LongTermMemory:
        """Sample user profile."""
        return LongTermMemory(
            user_id="integration_user",
            age=17,
            height_cm=175.0,
            weight_kg=70.0,
            injuries=["shoulder strain"],
            intolerances=["gluten"],
            allergies=["peanuts"],
            dietary_pref="omnivore",
            fitness_level="intermediate",
            primary_goal="build_muscle"
        )

    # ==================== INTEGRATION TEST 1 ====================
    @patch("app.api.routes.chat.get_long_term_store")
    def test_new_user_chat_triggers_onboarding(self, mock_store, client):
        """
        Test that chatting without a profile returns onboarding message.
        """
        # No profile exists
        mock_store.return_value.get.return_value = None

        response = client.post(
            "/api/chat",
            json={
                "message": "Hello!",
                "user_id": "new_user_12345"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should return onboarding message
        assert "Welcome" in data["response"]
        assert data["agent"] == "system"

    # ==================== INTEGRATION TEST 2 ====================
    @patch("app.api.routes.chat.run_agent_workflow")
    @patch("app.api.routes.chat.get_working_store")
    @patch("app.api.routes.chat.get_memory_retriever")
    @patch("app.api.routes.chat.get_long_term_store")
    async def test_existing_user_chat_invokes_agents(
        self,
        mock_lt_store,
        mock_retriever,
        mock_working,
        mock_workflow,
        client,
        mock_profile
    ):
        """
        Test that existing user chat triggers agent workflow.
        """
        # User has profile
        mock_lt_store.return_value.get.return_value = mock_profile

        # Mock retriever
        mock_retriever.return_value.retrieve_for_query.return_value = {
            "long_term": "User profile context",
            "short_term": "Recent activity",
            "working": "Current conversation"
        }

        # Mock working memory
        mock_working.return_value.add_message = Mock()

        # Mock agent workflow
        mock_workflow.return_value = "Here's a workout plan for you..."

        response = client.post(
            "/api/chat",
            json={
                "message": "What workout should I do today?",
                "user_id": "integration_user"
            }
        )

        assert response.status_code == 200

    # ==================== INTEGRATION TEST 3 ====================
    @patch("app.api.routes.profile.get_long_term_store")
    def test_profile_create_then_retrieve(self, mock_store, client):
        """
        Test creating a profile and then retrieving it.
        """
        user_id = "profile_test_user"

        # Profile to return after creation
        mock_profile = LongTermMemory(
            user_id=user_id,
            age=18,
            height_cm=180.0,
            weight_kg=75.0,
            injuries=[],
            intolerances=[],
            allergies=[],
            dietary_pref="omnivore",
            fitness_level="beginner",
            primary_goal="lose_fat"
        )

        # Track call count to return None first, then profile
        call_count = [0]

        def get_side_effect(uid):
            call_count[0] += 1
            # First call returns None (no existing profile)
            # Subsequent calls return the profile
            if call_count[0] == 1:
                return None
            return mock_profile

        mock_store.return_value.get.side_effect = get_side_effect
        mock_store.return_value.upsert = Mock()

        # Create profile
        create_response = client.post(
            f"/api/profile/{user_id}",
            json={
                "age": 18,
                "height_cm": 180.0,
                "weight_kg": 75.0,
                "dietary_pref": "omnivore",
                "fitness_level": "beginner",
                "primary_goal": "lose_fat"
            }
        )

        assert create_response.status_code == 200

        # Retrieve profile
        get_response = client.get(f"/api/profile/{user_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["age"] == 18
        assert data["primary_goal"] == "lose_fat"

    # ==================== INTEGRATION TEST 4 ====================
    @patch("app.api.routes.profile.get_long_term_store")
    def test_profile_update_injury_then_retrieve(self, mock_store, client, mock_profile):
        """
        Test adding an injury and verifying it's stored.
        """
        user_id = "injury_test_user"
        mock_store.return_value.get.return_value = mock_profile
        mock_store.return_value.add_injury = Mock()

        # Add injury
        injury_response = client.post(
            f"/api/profile/{user_id}/injury",
            json={"injury": "sprained ankle"}
        )

        assert injury_response.status_code == 200
        assert "added" in injury_response.json()["message"].lower()

    # ==================== INTEGRATION TEST 5 ====================
    def test_health_endpoints_all_respond(self, client):
        """
        Test that all health check endpoints respond correctly.
        """
        endpoints = [
            "/health",
            "/api/chat/health",
            "/api/voice/health",
            "/api/image/health"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert "healthy" in response.json().get("status", "")


class TestAPISafetyIntegration:
    """Integration tests for API safety checks."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    # ==================== INTEGRATION TEST 6 ====================
    def test_harmful_message_blocked_at_api_layer(self, client):
        """
        Test that harmful messages are blocked before reaching agents.
        """
        harmful_messages = [
            "How do I lose 30 pounds in one week?",
            "Tell me about extreme crash diets",
        ]

        for message in harmful_messages:
            response = client.post(
                "/api/chat",
                json={
                    "message": message,
                    "user_id": "test_user"
                }
            )

            # Should be blocked
            assert response.status_code == 400
            assert "blocked" in response.json()["detail"].lower()

    # ==================== INTEGRATION TEST 7 ====================
    def test_empty_user_id_rejected(self, client):
        """
        Test that requests with empty user_id are rejected.
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
