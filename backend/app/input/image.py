"""
Image input processing using Claude Vision.
Handles food image analysis with validation.
"""

import base64
import io
from typing import List, Optional

import httpx
from PIL import Image
from pydantic import BaseModel

from app.core.config import get_settings


class FoodAnalysis(BaseModel):
    """Result of food image analysis."""
    detected_foods: List[str] = []
    estimated_calories: float = 0.0
    estimated_protein_g: float = 0.0
    estimated_carbs_g: float = 0.0
    estimated_fat_g: float = 0.0
    confidence: float = 0.0
    message: str = ""
    low_confidence: bool = False


class ImageProcessingError(Exception):
    """Raised when image processing fails."""
    pass


class ImageProcessor:
    """
    Process food images using Claude Vision.
    Validates images and extracts nutritional estimates.
    """

    SUPPORTED_FORMATS = {"jpg", "jpeg", "png", "webp", "gif"}
    MAX_SIZE_MB = 10.0
    MAX_DIMENSION = 2048

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_size_mb: float = 10.0
    ):
        """
        Initialize image processor.

        Args:
            api_key: Anthropic API key for Claude Vision.
            max_size_mb: Maximum image size in MB.
        """
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.max_size_mb = max_size_mb
        self.claude_url = "https://api.anthropic.com/v1/messages"

    def validate(self, image_bytes: bytes) -> bool:
        """
        Validate image meets requirements.

        Args:
            image_bytes: Raw image data.

        Returns:
            True if valid.

        Raises:
            ValueError: If image fails validation.
        """
        # Check size
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise ValueError(
                f"Image exceeds {self.max_size_mb}MB limit "
                f"(actual: {size_mb:.1f}MB)"
            )

        # Check format and dimensions using PIL
        try:
            img = Image.open(io.BytesIO(image_bytes))
            format_lower = img.format.lower() if img.format else ""

            if format_lower not in self.SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported image format '{format_lower}'. "
                    f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
                )

            width, height = img.size
            if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
                raise ValueError(
                    f"Image dimensions ({width}x{height}) exceed "
                    f"maximum ({self.MAX_DIMENSION}x{self.MAX_DIMENSION})"
                )

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")

        return True

    def analyze_food(self, image_bytes: bytes) -> FoodAnalysis:
        """
        Analyze food in image using Claude Vision.

        Args:
            image_bytes: Raw image data.

        Returns:
            FoodAnalysis with detected foods and estimates.

        Raises:
            ImageProcessingError: If analysis fails.
        """
        # Validate image
        self.validate(image_bytes)

        if not self.api_key:
            raise ImageProcessingError("Anthropic API key not configured")

        # Convert to base64
        img = Image.open(io.BytesIO(image_bytes))
        format_str = img.format.lower() if img.format else "jpeg"
        media_type = f"image/{format_str}"

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # Build prompt for food analysis
        prompt = """Analyze this image for food content.

If food is detected, provide:
1. List of foods visible (be specific, e.g., "grilled chicken breast" not just "chicken")
2. Estimated total calories
3. Estimated protein (grams)
4. Estimated carbohydrates (grams)
5. Estimated fat (grams)

If no food is detected, respond with "NO_FOOD_DETECTED".

If the image is blurry or unclear, start your response with "LOW_CONFIDENCE:"

Respond in this exact format:
FOODS: [comma-separated list]
CALORIES: [number]
PROTEIN: [number]
CARBS: [number]
FAT: [number]"""

        # Call Claude API
        try:
            response = self._call_claude_vision(image_base64, media_type, prompt)
            return self._parse_food_response(response)
        except Exception as e:
            raise ImageProcessingError(f"Food analysis failed: {e}")

    def _call_claude_vision(
        self,
        image_base64: str,
        media_type: str,
        prompt: str
    ) -> str:
        """Call Claude Vision API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                self.claude_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        # Extract text from response
        content = data.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0].get("text", "")
        return ""

    def _parse_food_response(self, response: str) -> FoodAnalysis:
        """Parse Claude's food analysis response."""
        response = response.strip()

        # Check for no food
        if "NO_FOOD_DETECTED" in response.upper():
            return FoodAnalysis(
                detected_foods=[],
                message="No food detected in image",
                confidence=0.9
            )

        # Check for low confidence
        low_confidence = response.upper().startswith("LOW_CONFIDENCE")
        if low_confidence:
            response = response.split(":", 1)[-1].strip()

        # Parse structured response
        foods = []
        calories = 0.0
        protein = 0.0
        carbs = 0.0
        fat = 0.0

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("FOODS:"):
                foods_str = line.replace("FOODS:", "").strip()
                foods = [f.strip() for f in foods_str.split(",") if f.strip()]
            elif line.startswith("CALORIES:"):
                try:
                    calories = float(line.replace("CALORIES:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("PROTEIN:"):
                try:
                    protein = float(line.replace("PROTEIN:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("CARBS:"):
                try:
                    carbs = float(line.replace("CARBS:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("FAT:"):
                try:
                    fat = float(line.replace("FAT:", "").strip())
                except ValueError:
                    pass

        confidence = 0.5 if low_confidence else 0.85

        return FoodAnalysis(
            detected_foods=foods,
            estimated_calories=calories,
            estimated_protein_g=protein,
            estimated_carbs_g=carbs,
            estimated_fat_g=fat,
            confidence=confidence,
            low_confidence=low_confidence,
            message="Food analysis complete" if foods else "Could not identify foods"
        )

    def analyze_from_base64(self, image_base64: str) -> FoodAnalysis:
        """
        Analyze food from base64-encoded image.

        Args:
            image_base64: Base64 encoded image.

        Returns:
            FoodAnalysis result.
        """
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            raise ImageProcessingError(f"Invalid base64 encoding: {e}")

        return self.analyze_food(image_bytes)
