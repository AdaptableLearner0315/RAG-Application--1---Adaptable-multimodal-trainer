"""
Unit tests for fitness calculators.
Tests 5 edge cases for BMR, TDEE, and macro calculations.
"""

import pytest

from app.tools.calculators import (
    calculate_bmr,
    calculate_tdee,
    calculate_macros,
    calculate_macro_percentages,
    calculate_calories_from_macros,
    ActivityLevel,
    Goal,
    MacroTargets
)


class TestCalculators:
    """Unit tests for calculator functions."""

    # ==================== EDGE CASE 1: Zero/negative weight ====================
    def test_bmr_zero_weight_raises_error(self):
        """
        GIVEN zero weight
        WHEN calculate_bmr() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_bmr(weight_kg=0, height_cm=175, age=17)

        assert "weight" in str(exc_info.value).lower()

    def test_bmr_negative_weight_raises_error(self):
        """
        GIVEN negative weight
        WHEN calculate_bmr() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_bmr(weight_kg=-70, height_cm=175, age=17)

        assert "weight" in str(exc_info.value).lower()

    # ==================== EDGE CASE 2: Invalid age ====================
    def test_bmr_invalid_age_raises_error(self):
        """
        GIVEN invalid age (0 or >120)
        WHEN calculate_bmr() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError):
            calculate_bmr(weight_kg=70, height_cm=175, age=0)

        with pytest.raises(ValueError):
            calculate_bmr(weight_kg=70, height_cm=175, age=150)

    # ==================== EDGE CASE 3: Extreme goal calorie limits ====================
    def test_macros_minimum_calories_enforced(self):
        """
        GIVEN very low TDEE with fat loss goal
        WHEN calculate_macros() is called
        THEN minimum 1200 calories enforced
        """
        result = calculate_macros(
            weight_kg=40,  # Very light
            height_cm=150,
            age=16,
            is_male=False,
            activity_level=ActivityLevel.SEDENTARY,
            goal=Goal.LOSE_FAT
        )

        assert result.calories >= 1200

    # ==================== EDGE CASE 4: Adolescent protein adjustment ====================
    def test_macros_adolescent_higher_protein(self):
        """
        GIVEN user under 20 years old
        WHEN calculate_macros() is called
        THEN protein is increased for growth
        """
        teen_macros = calculate_macros(
            weight_kg=70,
            height_cm=175,
            age=17,
            is_male=True
        )

        adult_macros = calculate_macros(
            weight_kg=70,
            height_cm=175,
            age=25,
            is_male=True
        )

        # Teen should have higher protein per kg
        teen_protein_per_kg = teen_macros.protein_g / 70
        adult_protein_per_kg = adult_macros.protein_g / 70

        assert teen_protein_per_kg > adult_protein_per_kg

    # ==================== EDGE CASE 5: Zero macros edge case ====================
    def test_macro_percentages_zero_calories(self):
        """
        GIVEN MacroTargets with zero macros
        WHEN calculate_macro_percentages() is called
        THEN returns zeros without division error
        """
        macros = MacroTargets(
            calories=0,
            protein_g=0,
            carbs_g=0,
            fat_g=0
        )

        result = calculate_macro_percentages(macros)

        assert result["protein_pct"] == 0
        assert result["carbs_pct"] == 0
        assert result["fat_pct"] == 0

    # ==================== Additional Tests ====================
    def test_bmr_male_vs_female(self):
        """Test that male BMR is higher than female for same stats."""
        male_bmr = calculate_bmr(70, 175, 17, is_male=True)
        female_bmr = calculate_bmr(70, 175, 17, is_male=False)

        assert male_bmr > female_bmr

    def test_tdee_increases_with_activity(self):
        """Test that TDEE increases with activity level."""
        sedentary = calculate_tdee(70, 175, 17, activity_level=ActivityLevel.SEDENTARY)
        active = calculate_tdee(70, 175, 17, activity_level=ActivityLevel.ACTIVE)

        assert active > sedentary

    def test_macros_muscle_gain_higher_calories(self):
        """Test that muscle gain goal has higher calories than fat loss."""
        muscle = calculate_macros(70, 175, 17, goal=Goal.BUILD_MUSCLE)
        fat_loss = calculate_macros(70, 175, 17, goal=Goal.LOSE_FAT)

        assert muscle.calories > fat_loss.calories

    def test_macros_protein_scales_with_weight(self):
        """Test that protein scales with bodyweight."""
        light = calculate_macros(60, 175, 17)
        heavy = calculate_macros(90, 175, 17)

        assert heavy.protein_g > light.protein_g

    def test_calculate_calories_from_macros(self):
        """Test calorie calculation from macros."""
        calories = calculate_calories_from_macros(
            protein_g=150,
            carbs_g=200,
            fat_g=70
        )

        # 150*4 + 200*4 + 70*9 = 600 + 800 + 630 = 2030
        assert calories == 2030

    def test_macro_percentages_sum_to_100(self):
        """Test that macro percentages approximately sum to 100."""
        macros = MacroTargets(
            calories=2000,
            protein_g=150,
            carbs_g=200,
            fat_g=67
        )

        pcts = calculate_macro_percentages(macros)
        total = pcts["protein_pct"] + pcts["carbs_pct"] + pcts["fat_pct"]

        assert 99 <= total <= 101  # Allow small rounding error
