"""
Centralized exception hierarchy for the Adaptive Coaching Platform.
All custom exceptions inherit from base classes defined here.
"""


class AACPError(Exception):
    """Base exception for all Adaptive Coaching Platform errors."""

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


# Input Processing Errors
class InputProcessingError(AACPError):
    """Base class for input processing errors."""
    pass


class VoiceProcessingError(InputProcessingError):
    """Error during voice/audio processing."""
    pass


class ImageProcessingError(InputProcessingError):
    """Error during image processing."""
    pass


class TextProcessingError(InputProcessingError):
    """Error during text processing."""
    pass


# Data/Resource Errors
class ResourceNotFoundError(AACPError):
    """Requested resource not found."""
    pass


class FoodNotFoundError(ResourceNotFoundError):
    """Food item not found in database."""
    pass


class ExerciseNotFoundError(ResourceNotFoundError):
    """Exercise not found in database."""
    pass


class UserNotFoundError(ResourceNotFoundError):
    """User profile not found."""
    pass


# Validation Errors
class ValidationError(AACPError):
    """Data validation failed."""
    pass


class FileTooLargeError(ValidationError):
    """File exceeds maximum allowed size."""
    pass


class UnsupportedFormatError(ValidationError):
    """File format not supported."""
    pass


class SafetyViolationError(ValidationError):
    """Content violates safety guidelines."""
    pass


# External Service Errors
class ExternalServiceError(AACPError):
    """Error communicating with external service."""
    pass


class APIRateLimitError(ExternalServiceError):
    """External API rate limit exceeded."""
    pass


class APITimeoutError(ExternalServiceError):
    """External API request timed out."""
    pass


# Memory/Storage Errors
class MemoryError(AACPError):
    """Error in memory operations."""
    pass


class StorageError(AACPError):
    """Error in storage operations."""
    pass
