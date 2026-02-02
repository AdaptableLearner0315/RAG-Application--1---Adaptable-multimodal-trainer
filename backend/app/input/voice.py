"""
Voice input processing using Whisper API.
Handles audio transcription with validation and error handling.
"""

import base64
import io
from typing import Optional, Tuple

import httpx
from pydantic import BaseModel

from app.core.config import get_settings


class TranscriptionResult(BaseModel):
    """Result of voice transcription."""
    text: str
    confidence: float = 1.0
    language: str = "en"
    duration_sec: float = 0.0


class VoiceProcessingError(Exception):
    """Raised when voice processing fails."""
    pass


class VoiceProcessor:
    """
    Process voice input via Whisper API.
    Handles audio validation, transcription, and error recovery.
    """

    SUPPORTED_FORMATS = {"webm", "mp3", "wav", "m4a", "ogg", "flac"}
    MAX_DURATION_SEC = 30
    MAX_FILE_SIZE_MB = 25

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_duration_sec: int = 30
    ):
        """
        Initialize voice processor.

        Args:
            api_key: OpenAI API key for Whisper.
            max_duration_sec: Maximum audio duration in seconds.
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.max_duration_sec = max_duration_sec
        self.whisper_url = "https://api.openai.com/v1/audio/transcriptions"

    def validate_audio(self, audio_bytes: bytes, format: str) -> None:
        """
        Validate audio file meets requirements.

        Args:
            audio_bytes: Raw audio data.
            format: Audio format (webm, mp3, etc).

        Raises:
            ValueError: If audio fails validation.
        """
        # Check format
        format_lower = format.lower().lstrip(".")
        if format_lower not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format '{format}'. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Check file size
        size_mb = len(audio_bytes) / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"Audio file too large ({size_mb:.1f}MB). "
                f"Maximum: {self.MAX_FILE_SIZE_MB}MB"
            )

        # Basic audio header validation
        if len(audio_bytes) < 100:
            raise ValueError("Audio file too small to be valid")

    def transcribe(
        self,
        audio_bytes: bytes,
        format: str = "webm"
    ) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Raw audio data.
            format: Audio format.

        Returns:
            Transcribed text.

        Raises:
            VoiceProcessingError: If transcription fails.
        """
        result = self.transcribe_with_metadata(audio_bytes, format)
        return result.text

    def transcribe_with_metadata(
        self,
        audio_bytes: bytes,
        format: str = "webm"
    ) -> TranscriptionResult:
        """
        Transcribe audio and return metadata.

        Args:
            audio_bytes: Raw audio data.
            format: Audio format.

        Returns:
            TranscriptionResult with text and confidence.

        Raises:
            VoiceProcessingError: If transcription fails.
        """
        # Validate
        self.validate_audio(audio_bytes, format)

        # Check API key
        if not self.api_key:
            raise VoiceProcessingError("OpenAI API key not configured")

        # Prepare request
        format_lower = format.lower().lstrip(".")
        filename = f"audio.{format_lower}"

        files = {
            "file": (filename, io.BytesIO(audio_bytes), f"audio/{format_lower}"),
            "model": (None, "whisper-1"),
            "response_format": (None, "verbose_json")
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Call API with retry
        max_retries = 2
        last_error = None

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        self.whisper_url,
                        files=files,
                        headers=headers
                    )

                    if response.status_code == 429:
                        raise VoiceProcessingError("API rate limit exceeded")

                    response.raise_for_status()
                    data = response.json()

                    text = data.get("text", "").strip()
                    duration = data.get("duration", 0)
                    language = data.get("language", "en")

                    # Check for empty transcription
                    if not text:
                        return TranscriptionResult(
                            text="",
                            confidence=0.0,
                            language=language,
                            duration_sec=duration
                        )

                    # Estimate confidence from word-level data if available
                    confidence = self._estimate_confidence(data)

                    return TranscriptionResult(
                        text=text,
                        confidence=confidence,
                        language=language,
                        duration_sec=duration
                    )

            except httpx.TimeoutException:
                last_error = VoiceProcessingError("Transcription timed out")
            except VoiceProcessingError:
                raise
            except Exception as e:
                last_error = VoiceProcessingError(f"Transcription failed: {e}")

        raise last_error or VoiceProcessingError("Transcription failed")

    def _estimate_confidence(self, response_data: dict) -> float:
        """
        Estimate transcription confidence from API response.

        Args:
            response_data: Whisper API response.

        Returns:
            Confidence score 0.0 to 1.0.
        """
        # If segments available, average their no_speech_prob
        segments = response_data.get("segments", [])
        if segments:
            no_speech_probs = [s.get("no_speech_prob", 0) for s in segments]
            avg_no_speech = sum(no_speech_probs) / len(no_speech_probs)
            return round(1 - avg_no_speech, 2)

        # Default to high confidence if no segment data
        return 0.9

    def transcribe_from_base64(
        self,
        audio_base64: str,
        format: str = "webm"
    ) -> str:
        """
        Transcribe base64-encoded audio.

        Args:
            audio_base64: Base64 encoded audio.
            format: Audio format.

        Returns:
            Transcribed text.
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            raise VoiceProcessingError(f"Invalid base64 encoding: {e}")

        return self.transcribe(audio_bytes, format)
