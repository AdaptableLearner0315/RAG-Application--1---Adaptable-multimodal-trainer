"""
Unit tests for image processing.
Tests 5 edge cases for Claude Vision integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.input.image import (
    ImageProcessor,
    FoodAnalysis,
    ImageProcessingError
)


class TestImageProcessor:
    """Unit tests for ImageProcessor class."""

    @pytest.fixture
    def processor(self) -> ImageProcessor:
        """Create ImageProcessor instance."""
        return ImageProcessor(api_key="test-key", max_size_mb=10.0)

    @pytest.fixture
    def valid_png_bytes(self, sample_image_bytes) -> bytes:
        """Get valid PNG image bytes."""
        return sample_image_bytes

    # ==================== EDGE CASE 1: Oversized image ====================
    def test_validate_oversized_raises_error(self, processor: ImageProcessor):
        """
        GIVEN image exceeding size limit
        WHEN validate() is called
        THEN ValueError is raised
        """
        large_image = b"0" * (11 * 1024 * 1024)  # 11MB

        with pytest.raises(ValueError) as exc_info:
            processor.validate(large_image)

        assert "10" in str(exc_info.value) and "mb" in str(exc_info.value).lower()

    # ==================== EDGE CASE 2: Non-food image ====================
    def test_analyze_non_food_returns_empty(self, processor: ImageProcessor, valid_png_bytes):
        """
        GIVEN image with no food
        WHEN analyze_food() is called
        THEN FoodAnalysis has empty foods list
        """
        with patch.object(processor, "validate"):
            with patch.object(processor, "_call_claude_vision") as mock_vision:
                mock_vision.return_value = "NO_FOOD_DETECTED"

                result = processor.analyze_food(valid_png_bytes)

                assert result.detected_foods == []
                assert "no food" in result.message.lower()

    # ==================== EDGE CASE 3: Blurry image ====================
    def test_analyze_blurry_returns_low_confidence(self, processor: ImageProcessor, valid_png_bytes):
        """
        GIVEN blurry/unclear image
        WHEN analyze_food() is called
        THEN low_confidence flag is set
        """
        with patch.object(processor, "validate"):
            with patch.object(processor, "_call_claude_vision") as mock_vision:
                mock_vision.return_value = """LOW_CONFIDENCE:
FOODS: possibly chicken, maybe rice
CALORIES: 400
PROTEIN: 30
CARBS: 40
FAT: 10"""

                result = processor.analyze_food(valid_png_bytes)

                assert result.low_confidence is True
                assert result.confidence < 0.7

    # ==================== EDGE CASE 4: Multiple foods ====================
    def test_analyze_multiple_foods_lists_all(self, processor: ImageProcessor, valid_png_bytes):
        """
        GIVEN image with multiple foods
        WHEN analyze_food() is called
        THEN all foods are listed
        """
        with patch.object(processor, "validate"):
            with patch.object(processor, "_call_claude_vision") as mock_vision:
                mock_vision.return_value = """FOODS: grilled chicken breast, brown rice, steamed broccoli
CALORIES: 550
PROTEIN: 45
CARBS: 60
FAT: 12"""

                result = processor.analyze_food(valid_png_bytes)

                assert len(result.detected_foods) == 3
                assert "grilled chicken breast" in result.detected_foods
                assert "brown rice" in result.detected_foods
                assert "steamed broccoli" in result.detected_foods

    # ==================== EDGE CASE 5: Unsupported format ====================
    def test_validate_unsupported_format_raises_error(self, processor: ImageProcessor):
        """
        GIVEN image in unsupported format (BMP)
        WHEN validate() is called
        THEN ValueError is raised with supported formats
        """
        # Create a minimal BMP header
        bmp_bytes = b"BM" + b"\x00" * 100

        with pytest.raises(ValueError) as exc_info:
            processor.validate(bmp_bytes)

        error_msg = str(exc_info.value).lower()
        assert "unsupported" in error_msg or "invalid" in error_msg

    # ==================== Additional Tests ====================
    def test_validate_valid_image(self, processor: ImageProcessor, valid_png_bytes):
        """Test that valid image passes validation."""
        # Should not raise
        result = processor.validate(valid_png_bytes)
        assert result is True

    def test_analyze_food_no_api_key(self, valid_png_bytes):
        """Test that missing API key raises error."""
        processor = ImageProcessor(api_key=None)

        with patch.object(processor, "validate"):
            with pytest.raises(ImageProcessingError) as exc_info:
                processor.analyze_food(valid_png_bytes)

            assert "api key" in str(exc_info.value).lower()

    def test_parse_food_response_with_macros(self, processor: ImageProcessor):
        """Test parsing response with all macro data."""
        response = """FOODS: salmon fillet, quinoa
CALORIES: 650
PROTEIN: 50
CARBS: 45
FAT: 28"""

        result = processor._parse_food_response(response)

        assert result.detected_foods == ["salmon fillet", "quinoa"]
        assert result.estimated_calories == 650
        assert result.estimated_protein_g == 50
        assert result.estimated_carbs_g == 45
        assert result.estimated_fat_g == 28

    def test_analyze_from_base64(self, processor: ImageProcessor, valid_png_bytes):
        """Test base64 image analysis."""
        import base64

        with patch.object(processor, "analyze_food") as mock_analyze:
            mock_analyze.return_value = FoodAnalysis(detected_foods=["apple"])
            image_b64 = base64.b64encode(valid_png_bytes).decode()

            result = processor.analyze_from_base64(image_b64)

            assert "apple" in result.detected_foods

    def test_analyze_from_base64_invalid_encoding(self, processor: ImageProcessor):
        """Test invalid base64 raises error."""
        with pytest.raises(ImageProcessingError) as exc_info:
            processor.analyze_from_base64("not-valid-base64!!!")

        assert "base64" in str(exc_info.value).lower()
