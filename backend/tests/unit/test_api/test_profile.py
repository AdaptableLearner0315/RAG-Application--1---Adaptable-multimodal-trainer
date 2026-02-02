"""
Unit tests for profile API endpoint.
Tests 5 edge cases for the profile routes.
"""

import pytest
from unittest.mock import Mock, patch
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
        injuries=["left knee"],
        intolerances=["lactose"],
        allergies=[],
        dietary_pref="omnivore",
        fitness_level="beginner",
        primary_goal="build_muscle"
    )


class TestGetProfile:
    """Unit tests for GET /api/profile/{user_id} endpoint."""

    # Edge Case 1: Profile not found
    @patch("app.api.routes.profile.get_long_term_store")
    def test_get_profile_not_found_returns_404(self, mock_store, client):
        """
        GIVEN a non-existent user_id
        WHEN get profile endpoint is called
        THEN 404 error is returned.
        """
        mock_store.return_value.get.return_value = None

        response = client.get("/api/profile/nonexistent_user")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    # Edge Case 2: Valid profile retrieved
    @patch("app.api.routes.profile.get_long_term_store")
    def test_get_profile_success(self, mock_store, client, mock_profile):
        """
        GIVEN an existing user_id
        WHEN get profile endpoint is called
        THEN profile data is returned.
        """
        mock_store.return_value.get.return_value = mock_profile

        response = client.get("/api/profile/test_user_123")

        assert response.status_code == 200
        data = response.json()
        assert data["age"] == 17
        assert data["height_cm"] == 175.0
        assert "left knee" in data["injuries"]


class TestCreateProfile:
    """Unit tests for POST /api/profile/{user_id} endpoint."""

    # Edge Case 3: Profile already exists
    @patch("app.api.routes.profile.get_long_term_store")
    def test_create_profile_conflict_returns_409(self, mock_store, client, mock_profile):
        """
        GIVEN a user_id with existing profile
        WHEN create profile endpoint is called
        THEN 409 conflict error is returned.
        """
        mock_store.return_value.get.return_value = mock_profile

        response = client.post(
            "/api/profile/test_user_123",
            json={
                "age": 18,
                "height_cm": 180.0,
                "weight_kg": 75.0
            }
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    # Edge Case 4: Invalid age range
    @patch("app.api.routes.profile.get_long_term_store")
    def test_create_profile_invalid_age_rejected(self, mock_store, client):
        """
        GIVEN an age below minimum (13)
        WHEN create profile endpoint is called
        THEN 422 validation error is returned.
        """
        mock_store.return_value.get.return_value = None

        response = client.post(
            "/api/profile/new_user",
            json={
                "age": 10,  # Below minimum
                "height_cm": 150.0,
                "weight_kg": 40.0
            }
        )

        assert response.status_code == 422


class TestUpdateProfile:
    """Unit tests for PUT /api/profile/{user_id} endpoint."""

    # Edge Case 5: Update non-existent profile
    @patch("app.api.routes.profile.get_long_term_store")
    def test_update_profile_not_found_returns_404(self, mock_store, client):
        """
        GIVEN a non-existent user_id
        WHEN update profile endpoint is called
        THEN 404 error is returned.
        """
        mock_store.return_value.get.return_value = None

        response = client.put(
            "/api/profile/nonexistent_user",
            json={"weight_kg": 72.0}
        )

        assert response.status_code == 404


class TestDeleteProfile:
    """Unit tests for DELETE /api/profile/{user_id} endpoint."""

    @patch("app.api.routes.profile.get_long_term_store")
    def test_delete_profile_success(self, mock_store, client):
        """
        GIVEN an existing user_id
        WHEN delete profile endpoint is called
        THEN success message is returned.
        """
        mock_store.return_value.delete.return_value = True

        response = client.delete("/api/profile/test_user_123")

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    @patch("app.api.routes.profile.get_long_term_store")
    def test_delete_profile_not_found(self, mock_store, client):
        """
        GIVEN a non-existent user_id
        WHEN delete profile endpoint is called
        THEN 404 error is returned.
        """
        mock_store.return_value.delete.return_value = False

        response = client.delete("/api/profile/nonexistent_user")

        assert response.status_code == 404


class TestAddInjury:
    """Unit tests for POST /api/profile/{user_id}/injury endpoint."""

    @patch("app.api.routes.profile.get_long_term_store")
    def test_add_injury_success(self, mock_store, client, mock_profile):
        """
        GIVEN an existing profile
        WHEN add injury endpoint is called
        THEN success message is returned.
        """
        mock_store.return_value.get.return_value = mock_profile

        response = client.post(
            "/api/profile/test_user_123/injury",
            json={"injury": "right shoulder"}
        )

        assert response.status_code == 200
        assert "added" in response.json()["message"].lower()
