"""
Image analysis endpoint for the Adaptive Coaching Platform.
Handles food image analysis via Claude Vision.
"""

import base64
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.input.image import ImageProcessor, FoodAnalysis
from app.core.config import get_settings

router = APIRouter()


class ImageRequest(BaseModel):
    """Request body for image analysis."""

    image_base64: str = Field(..., description="Base64 encoded image data")
    user_id: str = Field(..., description="User ID for context")


class FoodItem(BaseModel):
    """Single detected food item."""

    name: str = Field(..., description="Food name")
    estimated_calories: Optional[int] = Field(default=None, description="Estimated calories")
    estimated_protein: Optional[int] = Field(default=None, description="Estimated protein (g)")
    estimated_carbs: Optional[int] = Field(default=None, description="Estimated carbs (g)")
    estimated_fat: Optional[int] = Field(default=None, description="Estimated fat (g)")
    portion_size: Optional[str] = Field(default=None, description="Estimated portion size")


class ImageResponse(BaseModel):
    """Response body for image analysis."""

    detected_foods: List[FoodItem] = Field(default_factory=list, description="Detected foods")
    total_calories: Optional[int] = Field(default=None, description="Total estimated calories")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    message: str = Field(..., description="Analysis message")
    low_confidence: bool = Field(default=False, description="Flag for low confidence results")


@router.post("/image/analyze", response_model=ImageResponse)
async def analyze_image(request: ImageRequest) -> ImageResponse:
    """
    Analyze a food image using Claude Vision.

    Args:
        request: Image request with base64 data.

    Returns:
        ImageResponse with detected foods and nutritional estimates.

    Raises:
        HTTPException: If analysis fails.
    """
    settings = get_settings()

    # Decode image
    try:
        image_bytes = base64.b64decode(request.image_base64)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid base64 encoding for image data"
        )

    # Validate size
    max_size_bytes = int(settings.max_image_size_mb * 1024 * 1024)
    if len(image_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum size is {settings.max_image_size_mb}MB"
        )

    # Empty image check
    if len(image_bytes) < 100:
        raise HTTPException(
            status_code=400,
            detail="Image data too small or empty"
        )

    # Process image
    processor = ImageProcessor()

    # Validate format
    try:
        processor.validate(image_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # Analyze food
    try:
        result = processor.analyze_food(image_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(e)}"
        )

    # Convert to response
    food_items = []
    total_calories = 0

    for food in result.detected_foods:
        item = FoodItem(
            name=food.get("name", "Unknown"),
            estimated_calories=food.get("calories"),
            estimated_protein=food.get("protein"),
            estimated_carbs=food.get("carbs"),
            estimated_fat=food.get("fat"),
            portion_size=food.get("portion")
        )
        food_items.append(item)

        if item.estimated_calories:
            total_calories += item.estimated_calories

    # Build response message
    if not food_items:
        message = "No food detected in the image. Please try taking a clearer photo of your meal."
    elif result.low_confidence:
        message = (
            f"Detected {len(food_items)} food item(s), but confidence is low. "
            "Please verify the nutritional estimates or try a clearer photo."
        )
    else:
        message = f"Successfully identified {len(food_items)} food item(s) in your meal."

    return ImageResponse(
        detected_foods=food_items,
        total_calories=total_calories if total_calories > 0 else None,
        confidence=result.confidence,
        message=message,
        low_confidence=result.low_confidence
    )


@router.get("/image/health")
async def health_check() -> dict:
    """
    Health check endpoint for image service.

    Returns:
        Status dict.
    """
    return {"status": "healthy", "service": "image"}
