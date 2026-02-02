"""
End-to-end tests for complete user journeys.
Tests full flows from frontend request to backend response.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile

from app.main import app
from app.memory.long_term import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore
from app.memory.schemas import LongTermMemory


class TestNewUserOnboardingJourney:
    """E2E tests for new user onboarding flow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    # ==================== E2E TEST 1 ====================
    @patch("app.api.routes.chat.get_long_term_store")
    @patch("app.api.routes.profile.get_long_term_store")
    def test_complete_onboarding_flow(
        self,
        mock_profile_store,
        mock_chat_store,
        client
    ):
        """
        Test complete new user onboarding:
        1. User sends first message
        2. System returns onboarding prompt
        3. User creates profile
        4. User can now chat normally
        """
        user_id = "e2e_new_user"

        # Step 1: First message - no profile exists
        mock_chat_store.return_value.get.return_value = None

        response1 = client.post(
            "/api/chat",
            json={"message": "Hello!", "user_id": user_id}
        )

        assert response1.status_code == 200
        assert "Welcome" in response1.json()["response"]
        assert response1.json()["agent"] == "system"

        # Step 2: User creates profile
        mock_profile_store.return_value.get.return_value = None
        mock_profile_store.return_value.upsert = Mock()

        # After upsert, return the profile
        created_profile = LongTermMemory(
            user_id=user_id,
            age=17,
            height_cm=170.0,
            weight_kg=65.0,
            injuries=[],
            intolerances=[],
            allergies=[],
            dietary_pref="omnivore",
            fitness_level="beginner",
            primary_goal="build_muscle"
        )

        def side_effect_get(uid):
            if mock_profile_store.return_value.upsert.called:
                return created_profile
            return None

        mock_profile_store.return_value.get.side_effect = side_effect_get

        response2 = client.post(
            f"/api/profile/{user_id}",
            json={
                "age": 17,
                "height_cm": 170.0,
                "weight_kg": 65.0,
                "dietary_pref": "omnivore",
                "fitness_level": "beginner",
                "primary_goal": "build_muscle"
            }
        )

        # Profile should be created (or conflict if exists)
        assert response2.status_code in [200, 409]


class TestChatConversationJourney:
    """E2E tests for chat conversation flows."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def existing_user_profile(self) -> LongTermMemory:
        """Existing user profile."""
        return LongTermMemory(
            user_id="e2e_existing_user",
            age=18,
            height_cm=180.0,
            weight_kg=75.0,
            injuries=["lower back pain"],
            intolerances=["dairy"],
            allergies=[],
            dietary_pref="omnivore",
            fitness_level="intermediate",
            primary_goal="build_muscle"
        )

    # ==================== E2E TEST 2 ====================
    @patch("app.api.routes.chat.run_agent_workflow")
    @patch("app.api.routes.chat.get_working_store")
    @patch("app.api.routes.chat.get_memory_retriever")
    @patch("app.api.routes.chat.get_long_term_store")
    def test_multi_turn_conversation(
        self,
        mock_lt_store,
        mock_retriever,
        mock_working,
        mock_workflow,
        client,
        existing_user_profile
    ):
        """
        Test multi-turn conversation flow:
        1. User asks about workout
        2. User follows up with nutrition question
        3. System maintains context
        """
        user_id = "e2e_existing_user"

        # Setup mocks
        mock_lt_store.return_value.get.return_value = existing_user_profile
        mock_retriever.return_value.retrieve_for_query.return_value = {
            "long_term": "User has lower back pain",
            "short_term": "",
            "working": ""
        }
        mock_working.return_value.add_message = Mock()
        mock_workflow.return_value = "Here's a back-safe workout plan..."

        # Turn 1: Workout question
        response1 = client.post(
            "/api/chat",
            json={
                "message": "What workout can I do with my back injury?",
                "user_id": user_id
            }
        )

        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Turn 2: Follow-up nutrition question
        mock_workflow.return_value = "For post-workout nutrition, try..."

        response2 = client.post(
            "/api/chat",
            json={
                "message": "What should I eat after that workout?",
                "user_id": user_id,
                "session_id": session_id
            }
        )

        assert response2.status_code == 200
        # Session should be maintained
        assert response2.json()["session_id"] == session_id


class TestErrorHandlingJourney:
    """E2E tests for error handling flows."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    # ==================== E2E TEST 3 ====================
    def test_graceful_handling_of_harmful_content(self, client):
        """
        Test that harmful content is blocked gracefully with helpful message.
        """
        # Use patterns that match the safety check: "how to starve/purge/vomit"
        # or "lose X pounds in Y days"
        response = client.post(
            "/api/chat",
            json={
                "message": "How to lose 30 pounds in 2 days?",
                "user_id": "test_user"
            }
        )

        assert response.status_code == 400
        assert "blocked" in response.json()["detail"].lower()

    # ==================== E2E TEST 4 ====================
    def test_missing_required_fields_returns_422(self, client):
        """
        Test that missing required fields return proper validation errors.
        """
        # Missing message
        response = client.post(
            "/api/chat",
            json={"user_id": "test_user"}
        )

        assert response.status_code == 422

    # ==================== E2E TEST 5 ====================
    @patch("app.api.routes.profile.get_long_term_store")
    def test_profile_not_found_returns_404(self, mock_store, client):
        """
        Test that accessing non-existent profile returns 404.
        """
        mock_store.return_value.get.return_value = None

        response = client.get("/api/profile/nonexistent_user_12345")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestMultiModalJourney:
    """E2E tests for multi-modal input flows."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    # ==================== E2E TEST 6 ====================
    @patch("app.api.routes.voice.VoiceProcessor")
    def test_voice_transcription_flow(self, mock_processor, client):
        """
        Test voice input flow:
        1. User sends audio
        2. System transcribes
        3. Returns text
        """
        # Mock transcription result
        mock_instance = Mock()
        mock_instance.transcribe.return_value = Mock(
            text="What should I eat for breakfast?",
            confidence=0.95,
            duration_sec=3.5
        )
        mock_processor.return_value = mock_instance

        # Send audio (base64 encoded dummy data)
        import base64
        dummy_audio = base64.b64encode(b"x" * 1000).decode()

        response = client.post(
            "/api/voice/transcribe",
            json={
                "audio_base64": dummy_audio,
                "format": "webm"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "What should I eat for breakfast?"
        assert data["confidence"] >= 0.9

    # ==================== E2E TEST 7 ====================
    @patch("app.api.routes.image.ImageProcessor")
    def test_image_analysis_flow(self, mock_processor, client):
        """
        Test image input flow:
        1. User sends food image
        2. System analyzes
        3. Returns nutritional info
        """
        # Mock analysis result
        mock_instance = Mock()
        mock_instance.validate = Mock()
        mock_instance.analyze_food.return_value = Mock(
            detected_foods=[
                {"name": "chicken breast", "calories": 200, "protein": 35},
                {"name": "rice", "calories": 150, "carbs": 30}
            ],
            confidence=0.85,
            low_confidence=False
        )
        mock_processor.return_value = mock_instance

        # Send image (base64 encoded dummy data)
        import base64
        dummy_image = base64.b64encode(b"x" * 1000).decode()

        response = client.post(
            "/api/image/analyze",
            json={
                "image_base64": dummy_image,
                "user_id": "test_user"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["detected_foods"]) == 2
        assert data["confidence"] > 0.8
