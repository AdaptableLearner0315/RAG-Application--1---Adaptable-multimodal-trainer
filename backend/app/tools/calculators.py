"""
Nutritional and fitness calculators.
Provides BMR, TDEE, and macro target calculations.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ActivityLevel(str, Enum):
    """Activity level for TDEE calculation."""
    SEDENTARY = "sedentary"           # Little/no exercise
    LIGHT = "light"                   # 1-3 days/week
    MODERATE = "moderate"             # 3-5 days/week
    ACTIVE = "active"                 # 6-7 days/week
    VERY_ACTIVE = "very_active"       # Athlete, 2x/day


class Goal(str, Enum):
    """Fitness goal for macro calculation."""
    LOSE_FAT = "lose_fat"
    MAINTAIN = "maintain"
    BUILD_MUSCLE = "build_muscle"


class MacroTargets(BaseModel):
    """Daily macro and calorie targets."""
    calories: int = Field(..., ge=0)
    protein_g: int = Field(..., ge=0)
    carbs_g: int = Field(..., ge=0)
    fat_g: int = Field(..., ge=0)
    fiber_g: int = Field(default=25, ge=0)
    water_ml: int = Field(default=2500, ge=0)


# Activity multipliers for TDEE
ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9
}

# Goal calorie adjustments
GOAL_ADJUSTMENTS = {
    Goal.LOSE_FAT: -500,       # 500 calorie deficit
    Goal.MAINTAIN: 0,
    Goal.BUILD_MUSCLE: 300     # 300 calorie surplus
}


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    is_male: bool = True
) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

    Args:
        weight_kg: Weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        is_male: True for male, False for female.

    Returns:
        BMR in calories/day.

    Raises:
        ValueError: If inputs are invalid.
    """
    if weight_kg <= 0:
        raise ValueError("Weight must be positive")
    if height_cm <= 0:
        raise ValueError("Height must be positive")
    if age <= 0 or age > 120:
        raise ValueError("Age must be between 1 and 120")

    # Mifflin-St Jeor Equation
    if is_male:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    return round(bmr, 1)


def calculate_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    is_male: bool = True,
    activity_level: ActivityLevel = ActivityLevel.MODERATE
) -> float:
    """
    Calculate Total Daily Energy Expenditure.

    Args:
        weight_kg: Weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        is_male: True for male, False for female.
        activity_level: Physical activity level.

    Returns:
        TDEE in calories/day.
    """
    bmr = calculate_bmr(weight_kg, height_cm, age, is_male)
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    return round(bmr * multiplier, 1)


def calculate_macros(
    weight_kg: float,
    height_cm: float,
    age: int,
    is_male: bool = True,
    activity_level: ActivityLevel = ActivityLevel.MODERATE,
    goal: Goal = Goal.MAINTAIN,
    protein_per_kg: Optional[float] = None
) -> MacroTargets:
    """
    Calculate daily macro targets based on user profile and goals.

    Args:
        weight_kg: Weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        is_male: True for male, False for female.
        activity_level: Physical activity level.
        goal: Fitness goal (lose fat, maintain, build muscle).
        protein_per_kg: Protein grams per kg bodyweight (auto-calculated if None).

    Returns:
        MacroTargets with daily calorie and macro goals.

    Raises:
        ValueError: If inputs are invalid.
    """
    # Calculate base TDEE
    tdee = calculate_tdee(weight_kg, height_cm, age, is_male, activity_level)

    # Adjust for goal
    calorie_adjustment = GOAL_ADJUSTMENTS.get(goal, 0)
    target_calories = max(1200, int(tdee + calorie_adjustment))  # Min 1200 for safety

    # Calculate protein
    if protein_per_kg is None:
        # Default protein based on goal
        if goal == Goal.BUILD_MUSCLE:
            protein_per_kg = 2.2  # Higher for muscle gain
        elif goal == Goal.LOSE_FAT:
            protein_per_kg = 2.0  # High to preserve muscle
        else:
            protein_per_kg = 1.6  # Maintenance

    # Adolescent adjustment (higher protein needs for growing bodies)
    if age < 20:
        protein_per_kg += 0.2

    protein_g = int(weight_kg * protein_per_kg)

    # Calculate fat (25-30% of calories)
    fat_percent = 0.25 if goal == Goal.LOSE_FAT else 0.28
    fat_calories = target_calories * fat_percent
    fat_g = int(fat_calories / 9)  # 9 calories per gram of fat

    # Calculate carbs (remaining calories)
    protein_calories = protein_g * 4
    remaining_calories = target_calories - protein_calories - fat_calories
    carbs_g = max(50, int(remaining_calories / 4))  # Min 50g carbs

    # Water intake (30-40ml per kg)
    water_ml = int(weight_kg * 35)

    # Fiber (14g per 1000 calories)
    fiber_g = max(20, int(target_calories / 1000 * 14))

    return MacroTargets(
        calories=target_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        fiber_g=fiber_g,
        water_ml=water_ml
    )


def calculate_macro_percentages(macros: MacroTargets) -> dict:
    """
    Calculate macro percentages from targets.

    Args:
        macros: MacroTargets object.

    Returns:
        Dict with protein_pct, carbs_pct, fat_pct.
    """
    total_calories = (
        (macros.protein_g * 4) +
        (macros.carbs_g * 4) +
        (macros.fat_g * 9)
    )

    if total_calories == 0:
        return {"protein_pct": 0, "carbs_pct": 0, "fat_pct": 0}

    return {
        "protein_pct": round((macros.protein_g * 4 / total_calories) * 100, 1),
        "carbs_pct": round((macros.carbs_g * 4 / total_calories) * 100, 1),
        "fat_pct": round((macros.fat_g * 9 / total_calories) * 100, 1)
    }


def calculate_calories_from_macros(
    protein_g: int,
    carbs_g: int,
    fat_g: int
) -> int:
    """
    Calculate total calories from macro grams.

    Args:
        protein_g: Protein in grams.
        carbs_g: Carbohydrates in grams.
        fat_g: Fat in grams.

    Returns:
        Total calories.
    """
    return (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
