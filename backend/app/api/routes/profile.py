"""
User profile endpoints for the Adaptive Coaching Platform.
Handles profile CRUD operations.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_long_term_store, validate_user_id
from app.memory.schemas import LongTermMemory

router = APIRouter()


class ProfileCreate(BaseModel):
    """Request body for creating a user profile."""

    age: int = Field(..., ge=13, le=100, description="Age in years")
    height_cm: float = Field(..., gt=0, le=300, description="Height in cm")
    weight_kg: float = Field(..., gt=0, le=500, description="Weight in kg")

    injuries: List[str] = Field(default_factory=list, description="Current injuries")
    intolerances: List[str] = Field(default_factory=list, description="Food intolerances")
    allergies: List[str] = Field(default_factory=list, description="Food allergies")

    dietary_pref: str = Field(default="omnivore", description="Dietary preference")
    fitness_level: str = Field(default="beginner", description="Fitness level")
    primary_goal: str = Field(default="maintain", description="Primary goal")
    target_weight_kg: Optional[float] = Field(default=None, description="Target weight")


class ProfileUpdate(BaseModel):
    """Request body for updating a user profile."""

    age: Optional[int] = Field(default=None, ge=13, le=100)
    height_cm: Optional[float] = Field(default=None, gt=0, le=300)
    weight_kg: Optional[float] = Field(default=None, gt=0, le=500)

    injuries: Optional[List[str]] = Field(default=None)
    intolerances: Optional[List[str]] = Field(default=None)
    allergies: Optional[List[str]] = Field(default=None)

    dietary_pref: Optional[str] = Field(default=None)
    fitness_level: Optional[str] = Field(default=None)
    primary_goal: Optional[str] = Field(default=None)
    target_weight_kg: Optional[float] = Field(default=None)


class ProfileResponse(BaseModel):
    """Response body for profile operations."""

    user_id: str
    age: int
    height_cm: float
    weight_kg: float

    injuries: List[str]
    intolerances: List[str]
    allergies: List[str]

    dietary_pref: str
    fitness_level: str
    primary_goal: str
    target_weight_kg: Optional[float]


class InjuryRequest(BaseModel):
    """Request body for adding an injury."""

    injury: str = Field(..., min_length=1, max_length=256, description="Injury description")


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str) -> ProfileResponse:
    """
    Get user profile by ID.

    Args:
        user_id: User identifier.

    Returns:
        ProfileResponse with user profile data.

    Raises:
        HTTPException: If user not found.
    """
    try:
        user_id = validate_user_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    store = get_long_term_store()
    profile = store.get(user_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Profile not found for user: {user_id}"
        )

    return ProfileResponse(
        user_id=profile.user_id,
        age=profile.age,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        injuries=profile.injuries,
        intolerances=profile.intolerances,
        allergies=profile.allergies,
        dietary_pref=profile.dietary_pref,
        fitness_level=profile.fitness_level,
        primary_goal=profile.primary_goal,
        target_weight_kg=profile.target_weight_kg
    )


@router.post("/profile/{user_id}", response_model=ProfileResponse)
async def create_profile(user_id: str, profile_data: ProfileCreate) -> ProfileResponse:
    """
    Create a new user profile.

    Args:
        user_id: User identifier.
        profile_data: Profile creation data.

    Returns:
        ProfileResponse with created profile.

    Raises:
        HTTPException: If profile already exists.
    """
    try:
        user_id = validate_user_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    store = get_long_term_store()

    # Check if profile exists
    existing = store.get(user_id)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Profile already exists for user: {user_id}"
        )

    # Create profile
    try:
        store.upsert(user_id, profile_data.model_dump())
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    profile = store.get(user_id)

    return ProfileResponse(
        user_id=profile.user_id,
        age=profile.age,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        injuries=profile.injuries,
        intolerances=profile.intolerances,
        allergies=profile.allergies,
        dietary_pref=profile.dietary_pref,
        fitness_level=profile.fitness_level,
        primary_goal=profile.primary_goal,
        target_weight_kg=profile.target_weight_kg
    )


@router.put("/profile/{user_id}", response_model=ProfileResponse)
async def update_profile(user_id: str, profile_data: ProfileUpdate) -> ProfileResponse:
    """
    Update an existing user profile.

    Args:
        user_id: User identifier.
        profile_data: Profile update data (partial).

    Returns:
        ProfileResponse with updated profile.

    Raises:
        HTTPException: If user not found.
    """
    try:
        user_id = validate_user_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    store = get_long_term_store()

    # Check if profile exists
    existing = store.get(user_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"Profile not found for user: {user_id}"
        )

    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No update data provided"
        )

    try:
        store.upsert(user_id, update_data)
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    profile = store.get(user_id)

    return ProfileResponse(
        user_id=profile.user_id,
        age=profile.age,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        injuries=profile.injuries,
        intolerances=profile.intolerances,
        allergies=profile.allergies,
        dietary_pref=profile.dietary_pref,
        fitness_level=profile.fitness_level,
        primary_goal=profile.primary_goal,
        target_weight_kg=profile.target_weight_kg
    )


@router.delete("/profile/{user_id}")
async def delete_profile(user_id: str) -> dict:
    """
    Delete user profile (GDPR compliance).

    Args:
        user_id: User identifier.

    Returns:
        Success message.

    Raises:
        HTTPException: If user not found.
    """
    try:
        user_id = validate_user_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    store = get_long_term_store()
    deleted = store.delete(user_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Profile not found for user: {user_id}"
        )

    return {"message": f"Profile deleted for user: {user_id}"}


@router.post("/profile/{user_id}/injury")
async def add_injury(user_id: str, injury_data: InjuryRequest) -> dict:
    """
    Add an injury to user profile.

    Args:
        user_id: User identifier.
        injury_data: Injury to add.

    Returns:
        Success message.

    Raises:
        HTTPException: If user not found.
    """
    try:
        user_id = validate_user_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    store = get_long_term_store()

    existing = store.get(user_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"Profile not found for user: {user_id}"
        )

    store.add_injury(user_id, injury_data.injury)

    return {"message": f"Injury added: {injury_data.injury}"}


@router.get("/profile/health")
async def health_check() -> dict:
    """
    Health check endpoint for profile service.

    Returns:
        Status dict.
    """
    return {"status": "healthy", "service": "profile"}
