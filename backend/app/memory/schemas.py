"""
Memory data schemas using Pydantic models.
Defines structures for working, short-term, and long-term memory.
"""

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class LongTermMemory(BaseModel):
    """
    Permanent user profile stored in SQLite.
    Updated rarely, only when user reports changes.
    """

    user_id: str = Field(..., description="Unique user identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Demographics
    age: int = Field(..., ge=13, le=100, description="User age in years")
    height_cm: float = Field(..., gt=0, le=300, description="Height in centimeters")
    weight_kg: float = Field(..., gt=0, le=500, description="Weight in kilograms")

    # Health constraints
    injuries: List[str] = Field(default_factory=list, description="Current injuries")
    intolerances: List[str] = Field(default_factory=list, description="Food intolerances")
    allergies: List[str] = Field(default_factory=list, description="Food allergies")
    health_conditions: List[str] = Field(default_factory=list, description="Medical conditions like diabetes, hypertension, etc.")
    medications: List[str] = Field(default_factory=list, description="Current medications")
    gender: str = Field(default="prefer_not_to_say", description="Gender: male, female, other, prefer_not_to_say")

    # Preferences
    dietary_pref: str = Field(
        default="omnivore",
        description="Dietary preference: omnivore, vegetarian, vegan"
    )
    fitness_level: str = Field(
        default="beginner",
        description="Fitness level: beginner, intermediate, advanced"
    )

    # Goals
    primary_goal: str = Field(
        default="maintain",
        description="Primary goal: build_muscle, lose_fat, maintain, improve_energy"
    )
    target_weight_kg: Optional[float] = Field(
        default=None,
        gt=0,
        le=500,
        description="Target weight in kg"
    )

    @field_validator("dietary_pref")
    @classmethod
    def validate_dietary_pref(cls, v: str) -> str:
        """Validate dietary preference is valid."""
        allowed = {"omnivore", "vegetarian", "vegan", "pescatarian", "keto"}
        if v.lower() not in allowed:
            raise ValueError(f"dietary_pref must be one of {allowed}")
        return v.lower()

    @field_validator("fitness_level")
    @classmethod
    def validate_fitness_level(cls, v: str) -> str:
        """Validate fitness level is valid."""
        allowed = {"beginner", "intermediate", "advanced"}
        if v.lower() not in allowed:
            raise ValueError(f"fitness_level must be one of {allowed}")
        return v.lower()


class MealLog(BaseModel):
    """Single meal log entry."""

    time: str = Field(..., description="Time of meal (HH:MM)")
    foods: List[str] = Field(..., min_length=1, description="List of foods eaten")
    calories: int = Field(..., ge=0, description="Total calories")
    protein: int = Field(..., ge=0, description="Protein in grams")
    carbs: int = Field(..., ge=0, description="Carbohydrates in grams")
    fat: int = Field(..., ge=0, description="Fat in grams")

    @field_validator("calories", "protein", "carbs", "fat")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure nutritional values are non-negative."""
        if v < 0:
            raise ValueError("Nutritional values cannot be negative")
        return v


class WorkoutLog(BaseModel):
    """Single workout log entry."""

    time: str = Field(..., description="Time of workout (HH:MM)")
    type: str = Field(..., description="Type: strength, cardio, flexibility, sports")
    duration_min: int = Field(..., gt=0, le=480, description="Duration in minutes")
    intensity: str = Field(..., description="Intensity: low, moderate, high")
    exercises: List[str] = Field(default_factory=list, description="Exercises performed")

    @field_validator("duration_min")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Ensure duration is positive."""
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class SleepLog(BaseModel):
    """Single sleep log entry."""

    bed_time: str = Field(..., description="Bed time (HH:MM)")
    wake_time: str = Field(..., description="Wake time (HH:MM)")
    quality: int = Field(..., ge=1, le=5, description="Sleep quality 1-5")


class ShortTermMemory(BaseModel):
    """
    Rolling 7-day activity record.
    Stored in SQLite, auto-expires after retention period.
    """

    user_id: str = Field(..., description="Unique user identifier")
    record_date: date = Field(..., description="Date of this record")

    meals: List[MealLog] = Field(default_factory=list)
    workouts: List[WorkoutLog] = Field(default_factory=list)
    sleep: Optional[SleepLog] = Field(default=None)

    # Derived daily totals
    calories_consumed: int = Field(default=0, ge=0)
    calories_burned: int = Field(default=0, ge=0)
    protein_total: int = Field(default=0, ge=0)


class WorkingMemory(BaseModel):
    """
    Current session state.
    Stored in Redis, cleared on session end.
    """

    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Current session identifier")

    conversation: List[Dict] = Field(
        default_factory=list,
        description="List of {role, content, timestamp}"
    )
    current_agent: Optional[str] = Field(
        default=None,
        description="Currently active agent"
    )
    pending_context: Dict = Field(
        default_factory=dict,
        description="Retrieved docs, tool results"
    )


class MemoryUpdate(BaseModel):
    """Request to update user memory."""

    field: str = Field(..., description="Field to update")
    value: Any = Field(..., description="New value")
    source: str = Field(default="user", description="Update source: user, system, inferred")
