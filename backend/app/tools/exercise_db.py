"""
Exercise database integration.
Provides exercise search, muscle group lookup, and injury modifications.
"""

from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel


class Exercise(BaseModel):
    """Exercise with instructions and metadata."""
    id: str
    name: str
    muscle_groups: List[str] = []
    equipment: List[str] = []
    difficulty: str = "intermediate"
    instructions: List[str] = []
    contraindications: List[str] = []


class ModifiedExercise(BaseModel):
    """Exercise modification for injury."""
    original: Exercise
    modification: str
    reason: str
    alternative: Optional[Exercise] = None


# wger.de API
WGER_BASE_URL = "https://wger.de/api/v2"

# Local exercise database for common exercises
LOCAL_EXERCISES = {
    "squats": Exercise(
        id="squat_001",
        name="Barbell Back Squat",
        muscle_groups=["quadriceps", "glutes", "hamstrings"],
        equipment=["barbell", "squat rack"],
        difficulty="intermediate",
        instructions=[
            "Position bar on upper back",
            "Feet shoulder-width apart",
            "Descend until thighs parallel to ground",
            "Drive through heels to stand"
        ],
        contraindications=["knee injury", "lower back injury"]
    ),
    "deadlift": Exercise(
        id="deadlift_001",
        name="Conventional Deadlift",
        muscle_groups=["hamstrings", "glutes", "lower back", "traps"],
        equipment=["barbell"],
        difficulty="intermediate",
        instructions=[
            "Stand with feet hip-width apart",
            "Grip bar just outside legs",
            "Keep back straight, chest up",
            "Drive through legs and extend hips"
        ],
        contraindications=["lower back injury", "herniated disc"]
    ),
    "bench_press": Exercise(
        id="bench_001",
        name="Barbell Bench Press",
        muscle_groups=["chest", "triceps", "front delts"],
        equipment=["barbell", "bench"],
        difficulty="intermediate",
        instructions=[
            "Lie on bench with feet flat",
            "Grip bar slightly wider than shoulders",
            "Lower to chest with control",
            "Press up to full extension"
        ],
        contraindications=["shoulder injury", "rotator cuff injury"]
    ),
    "pull_up": Exercise(
        id="pullup_001",
        name="Pull-up",
        muscle_groups=["lats", "biceps", "rear delts"],
        equipment=["pull-up bar"],
        difficulty="intermediate",
        instructions=[
            "Hang with arms fully extended",
            "Pull until chin over bar",
            "Lower with control"
        ],
        contraindications=["shoulder injury", "elbow injury"]
    ),
    "lunges": Exercise(
        id="lunge_001",
        name="Walking Lunges",
        muscle_groups=["quadriceps", "glutes", "hamstrings"],
        equipment=["none"],
        difficulty="beginner",
        instructions=[
            "Step forward with one leg",
            "Lower until back knee nearly touches ground",
            "Push through front heel to step forward"
        ],
        contraindications=["knee injury", "ankle injury"]
    )
}

# Injury modification mappings
INJURY_MODIFICATIONS = {
    "knee injury": {
        "squats": ModifiedExercise(
            original=LOCAL_EXERCISES["squats"],
            modification="Reduce depth to quarter squat, use lighter weight",
            reason="Reduces stress on knee joint",
            alternative=Exercise(
                id="leg_press_001",
                name="Leg Press (limited range)",
                muscle_groups=["quadriceps", "glutes"],
                equipment=["leg press machine"],
                difficulty="beginner",
                instructions=["Use limited range of motion", "Keep weight moderate"]
            )
        ),
        "lunges": ModifiedExercise(
            original=LOCAL_EXERCISES["lunges"],
            modification="Perform reverse lunges with shorter stride",
            reason="Reduces forward knee stress",
            alternative=Exercise(
                id="step_up_001",
                name="Low Box Step-ups",
                muscle_groups=["quadriceps", "glutes"],
                equipment=["low box"],
                difficulty="beginner",
                instructions=["Use low platform", "Focus on control"]
            )
        )
    },
    "lower back injury": {
        "squats": ModifiedExercise(
            original=LOCAL_EXERCISES["squats"],
            modification="Use goblet squat with lighter weight",
            reason="Reduces spinal loading",
            alternative=Exercise(
                id="goblet_001",
                name="Goblet Squat",
                muscle_groups=["quadriceps", "glutes"],
                equipment=["dumbbell", "kettlebell"],
                difficulty="beginner",
                instructions=["Hold weight at chest", "Keep torso upright"]
            )
        ),
        "deadlift": ModifiedExercise(
            original=LOCAL_EXERCISES["deadlift"],
            modification="Avoid conventional deadlift, use trap bar or Romanian DL with light weight",
            reason="Reduces lower back stress",
            alternative=Exercise(
                id="rdl_001",
                name="Romanian Deadlift (light)",
                muscle_groups=["hamstrings", "glutes"],
                equipment=["dumbbell"],
                difficulty="beginner",
                instructions=["Keep slight knee bend", "Hinge at hips", "Light weight only"]
            )
        )
    },
    "shoulder injury": {
        "bench_press": ModifiedExercise(
            original=LOCAL_EXERCISES["bench_press"],
            modification="Use floor press or reduce range of motion",
            reason="Limits shoulder extension",
            alternative=Exercise(
                id="floor_press_001",
                name="Dumbbell Floor Press",
                muscle_groups=["chest", "triceps"],
                equipment=["dumbbell"],
                difficulty="beginner",
                instructions=["Lie on floor", "Press with neutral grip", "Limited ROM"]
            )
        ),
        "pull_up": ModifiedExercise(
            original=LOCAL_EXERCISES["pull_up"],
            modification="Use lat pulldown with controlled range",
            reason="Allows controlled shoulder movement",
            alternative=Exercise(
                id="lat_pull_001",
                name="Lat Pulldown",
                muscle_groups=["lats", "biceps"],
                equipment=["cable machine"],
                difficulty="beginner",
                instructions=["Use moderate weight", "Control the movement"]
            )
        )
    }
}

# Muscle group to exercise mapping
MUSCLE_EXERCISES = {
    "quadriceps": ["squats", "lunges", "leg_press"],
    "hamstrings": ["deadlift", "lunges", "leg_curl"],
    "glutes": ["squats", "deadlift", "lunges", "hip_thrust"],
    "chest": ["bench_press", "push_ups", "dumbbell_fly"],
    "back": ["pull_up", "rows", "deadlift"],
    "lats": ["pull_up", "lat_pulldown", "rows"],
    "shoulders": ["overhead_press", "lateral_raise"],
    "biceps": ["pull_up", "bicep_curl"],
    "triceps": ["bench_press", "tricep_extension", "dips"],
    "core": ["plank", "crunches", "leg_raise"]
}


def search_exercises(
    query: str,
    max_results: int = 5
) -> List[Exercise]:
    """
    Search for exercises by name or keyword.

    Args:
        query: Search query.
        max_results: Maximum results to return.

    Returns:
        List of matching exercises.
    """
    if not query or not query.strip():
        return []

    query_lower = query.lower()
    results = []

    # Search local database first
    for key, exercise in LOCAL_EXERCISES.items():
        if query_lower in key or query_lower in exercise.name.lower():
            results.append(exercise)
        elif any(query_lower in mg.lower() for mg in exercise.muscle_groups):
            results.append(exercise)

    # Try wger API for more results
    if len(results) < max_results:
        try:
            api_results = _search_wger(query, max_results - len(results))
            results.extend(api_results)
        except Exception:
            pass

    return results[:max_results]


def _search_wger(query: str, limit: int) -> List[Exercise]:
    """Search wger.de API for exercises."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{WGER_BASE_URL}/exercise/",
                params={"language": 2, "limit": limit, "search": query}
            )
            response.raise_for_status()
            data = response.json()

        exercises = []
        for item in data.get("results", []):
            exercises.append(Exercise(
                id=f"wger_{item.get('id')}",
                name=item.get("name", "Unknown"),
                muscle_groups=[],
                equipment=[],
                difficulty="intermediate",
                instructions=[item.get("description", "")[:200]] if item.get("description") else []
            ))
        return exercises

    except Exception:
        return []


def get_exercise_by_muscle(muscle_group: str) -> List[Exercise]:
    """
    Get exercises targeting a specific muscle group.

    Args:
        muscle_group: Target muscle group.

    Returns:
        List of exercises for that muscle.
    """
    muscle_lower = muscle_group.lower()

    if muscle_lower not in MUSCLE_EXERCISES:
        # Try to find partial match
        for muscle, exercises in MUSCLE_EXERCISES.items():
            if muscle_lower in muscle or muscle in muscle_lower:
                return [LOCAL_EXERCISES[e] for e in exercises if e in LOCAL_EXERCISES]
        return []

    exercise_keys = MUSCLE_EXERCISES[muscle_lower]
    return [LOCAL_EXERCISES[e] for e in exercise_keys if e in LOCAL_EXERCISES]


def get_injury_modifications(
    exercise_name: str,
    injury: str
) -> Optional[ModifiedExercise]:
    """
    Get injury-safe modification for an exercise.

    Args:
        exercise_name: Name of exercise.
        injury: User's injury.

    Returns:
        ModifiedExercise with modification and alternative.
    """
    injury_lower = injury.lower()
    exercise_lower = exercise_name.lower().replace(" ", "_")

    # Find matching injury category
    matched_injury = None
    for injury_key in INJURY_MODIFICATIONS.keys():
        if injury_key in injury_lower or injury_lower in injury_key:
            matched_injury = injury_key
            break

    if not matched_injury:
        return None

    # Find matching exercise
    injury_mods = INJURY_MODIFICATIONS[matched_injury]
    for ex_key, modification in injury_mods.items():
        if ex_key in exercise_lower or exercise_lower in ex_key:
            return modification

    return None
