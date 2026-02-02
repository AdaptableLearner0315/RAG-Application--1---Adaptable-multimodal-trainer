"""
Unit tests for food database tools.
Tests 5 edge cases for USDA API integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.tools.food_db import (
    search_usda,
    get_nutrition_info,
    search_and_get_nutrition,
    NutritionInfo,
    FoodNotFoundError,
    RateLimitError
)


class TestFoodDatabase:
    """Unit tests for food database functions."""

    # ==================== EDGE CASE 1: Food not found ====================
    def test_search_unknown_food_returns_empty(self):
        """
        GIVEN a food not in USDA database
        WHEN search_usda() is called
        THEN empty list is returned
        """
        with patch("app.tools.food_db.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"foods": []}
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = search_usda("xyzzyfood123456")

            assert result == []

    # ==================== EDGE CASE 2: API rate limit ====================
    def test_search_rate_limit_raises_error(self):
        """
        GIVEN USDA API returns 429 rate limit
        WHEN search_usda() is called
        THEN RateLimitError is raised
        """
        with patch("app.tools.food_db.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            with pytest.raises(RateLimitError):
                search_usda("chicken")

    # ==================== EDGE CASE 3: Ambiguous food name ====================
    def test_search_ambiguous_returns_multiple(self):
        """
        GIVEN ambiguous food name with multiple matches
        WHEN search_usda() is called
        THEN multiple results returned sorted by score
        """
        with patch("app.tools.food_db.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "foods": [
                    {"fdcId": 1, "description": "Chicken breast, raw", "score": 100},
                    {"fdcId": 2, "description": "Chicken thigh, raw", "score": 90},
                    {"fdcId": 3, "description": "Chicken wing, raw", "score": 80}
                ]
            }
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = search_usda("chicken", max_results=5)

            assert len(result) == 3
            assert result[0]["description"] == "Chicken breast, raw"

    # ==================== EDGE CASE 4: Malformed API response ====================
    def test_search_malformed_response_returns_empty(self):
        """
        GIVEN API returns malformed/unexpected response
        WHEN search_usda() is called
        THEN empty list returned gracefully
        """
        with patch("app.tools.food_db.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"unexpected": "format"}
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = search_usda("apple")

            assert result == []

    # ==================== EDGE CASE 5: Network timeout ====================
    def test_search_timeout_retries_then_empty(self):
        """
        GIVEN network timeout on API call
        WHEN search_usda() is called
        THEN retry once, then return empty
        """
        import httpx

        with patch("app.tools.food_db.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("timeout")

            result = search_usda("apple")

            # Should retry and return empty on failure
            assert result == []

    # ==================== Additional Tests ====================
    def test_search_empty_query_raises_error(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            search_usda("")

        assert "empty" in str(exc_info.value).lower()

    def test_get_nutrition_info_not_found(self):
        """Test getting nutrition for nonexistent food ID."""
        with patch("app.tools.food_db.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            with pytest.raises(FoodNotFoundError):
                get_nutrition_info(999999999)

    def test_search_and_get_nutrition_success(self):
        """Test combined search and nutrition lookup."""
        with patch("app.tools.food_db.search_usda") as mock_search:
            with patch("app.tools.food_db.get_nutrition_info") as mock_nutrition:
                mock_search.return_value = [{"fdc_id": 123, "description": "Apple"}]
                mock_nutrition.return_value = NutritionInfo(
                    food_name="Apple",
                    calories=52,
                    protein_g=0.3,
                    carbs_g=14,
                    fat_g=0.2
                )

                result = search_and_get_nutrition("apple")

                assert result is not None
                assert result.food_name == "Apple"
                assert result.calories == 52

    def test_search_and_get_nutrition_not_found(self):
        """Test combined search when food not found."""
        with patch("app.tools.food_db.search_usda") as mock_search:
            mock_search.return_value = []

            result = search_and_get_nutrition("nonexistent_food")

            assert result is None
