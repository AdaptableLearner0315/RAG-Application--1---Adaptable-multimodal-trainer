"""
Agent tools module.
Provides food database, exercise database, and calculation utilities.
"""

from app.tools.food_db import search_usda, get_nutrition_info, FoodNotFoundError
from app.tools.exercise_db import search_exercises, get_exercise_by_muscle, get_injury_modifications
from app.tools.calculators import calculate_bmr, calculate_tdee, calculate_macros, MacroTargets

__all__ = [
    "search_usda",
    "get_nutrition_info",
    "FoodNotFoundError",
    "search_exercises",
    "get_exercise_by_muscle",
    "get_injury_modifications",
    "calculate_bmr",
    "calculate_tdee",
    "calculate_macros",
    "MacroTargets"
]
