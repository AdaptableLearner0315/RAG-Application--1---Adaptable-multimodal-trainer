"""
USDA FoodData Central API integration.
Provides food search and nutrition information lookup.
"""

import time
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel

from app.core.config import get_settings


class NutritionInfo(BaseModel):
    """Nutritional information for a food item."""
    food_name: str
    serving_size: str = "100g"
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    sugar_g: float = 0.0
    sodium_mg: float = 0.0


class FoodNotFoundError(Exception):
    """Raised when food is not found in database."""
    pass


class RateLimitError(Exception):
    """Raised when API rate limit is hit."""
    pass


# USDA API endpoints
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
USDA_SEARCH_ENDPOINT = f"{USDA_BASE_URL}/foods/search"
USDA_FOOD_ENDPOINT = f"{USDA_BASE_URL}/food"

# Nutrient IDs in USDA database
NUTRIENT_IDS = {
    "calories": 1008,
    "protein": 1003,
    "fat": 1004,
    "carbs": 1005,
    "fiber": 1079,
    "sugar": 2000,
    "sodium": 1093
}


def search_usda(
    food_name: str,
    max_results: int = 5,
    api_key: Optional[str] = None
) -> List[Dict]:
    """
    Search USDA FoodData Central for foods.

    Args:
        food_name: Food name to search for.
        max_results: Maximum number of results.
        api_key: USDA API key. Uses demo key if not provided.

    Returns:
        List of food results with fdc_id and description.

    Raises:
        ValueError: If food_name is empty.
        RateLimitError: If API rate limit is hit.
    """
    if not food_name or not food_name.strip():
        raise ValueError("Food name cannot be empty")

    api_key = api_key or "DEMO_KEY"

    params = {
        "api_key": api_key,
        "query": food_name,
        "pageSize": max_results,
        "dataType": ["Foundation", "SR Legacy", "Branded"]
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(USDA_SEARCH_ENDPOINT, params=params)

            if response.status_code == 429:
                raise RateLimitError("USDA API rate limit exceeded")

            response.raise_for_status()
            data = response.json()

    except httpx.TimeoutException:
        # Retry once
        time.sleep(1)
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(USDA_SEARCH_ENDPOINT, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return []
    except RateLimitError:
        raise
    except Exception:
        return []

    foods = data.get("foods", [])
    return [
        {
            "fdc_id": f.get("fdcId"),
            "description": f.get("description", ""),
            "brand": f.get("brandOwner", ""),
            "score": f.get("score", 0)
        }
        for f in foods
    ]


def get_nutrition_info(
    fdc_id: int,
    api_key: Optional[str] = None
) -> NutritionInfo:
    """
    Get detailed nutrition information for a food.

    Args:
        fdc_id: USDA FoodData Central ID.
        api_key: USDA API key.

    Returns:
        NutritionInfo with macro and micronutrient data.

    Raises:
        FoodNotFoundError: If food ID is not found.
    """
    api_key = api_key or "DEMO_KEY"

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{USDA_FOOD_ENDPOINT}/{fdc_id}",
                params={"api_key": api_key}
            )

            if response.status_code == 404:
                raise FoodNotFoundError(f"Food with ID {fdc_id} not found")

            response.raise_for_status()
            data = response.json()

    except FoodNotFoundError:
        raise
    except Exception as e:
        raise FoodNotFoundError(f"Failed to fetch food data: {e}")

    # Extract nutrients
    nutrients = {}
    for nutrient in data.get("foodNutrients", []):
        nutrient_id = nutrient.get("nutrient", {}).get("id")
        value = nutrient.get("amount", 0)

        for name, nid in NUTRIENT_IDS.items():
            if nutrient_id == nid:
                nutrients[name] = value

    return NutritionInfo(
        food_name=data.get("description", "Unknown"),
        serving_size="100g",
        calories=nutrients.get("calories", 0),
        protein_g=nutrients.get("protein", 0),
        carbs_g=nutrients.get("carbs", 0),
        fat_g=nutrients.get("fat", 0),
        fiber_g=nutrients.get("fiber", 0),
        sugar_g=nutrients.get("sugar", 0),
        sodium_mg=nutrients.get("sodium", 0)
    )


def search_and_get_nutrition(
    food_name: str,
    api_key: Optional[str] = None
) -> Optional[NutritionInfo]:
    """
    Search for food and return nutrition info for best match.

    Args:
        food_name: Food to search for.
        api_key: USDA API key.

    Returns:
        NutritionInfo for best match, or None if not found.
    """
    results = search_usda(food_name, max_results=1, api_key=api_key)

    if not results:
        return None

    fdc_id = results[0].get("fdc_id")
    if not fdc_id:
        return None

    try:
        return get_nutrition_info(fdc_id, api_key)
    except FoodNotFoundError:
        return None
