"""
Unit tests for voice processing.
Tests 5 edge cases for Whisper API integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.input.voice import (
    VoiceProcessor,
    TranscriptionResult,
    VoiceProcessingError
)


class TestVoiceProcessor:
    """Unit tests for VoiceProcessor class."""

    @pytest.fixture
    def processor(self) -> VoiceProcessor:
        """Create VoiceProcessor instance."""
        return VoiceProcessor(api_key="test-key", max_duration_sec=30)

    # ==================== EDGE CASE 1: Audio too long ====================
    def test_validate_long_audio_size_check(self, processor: VoiceProcessor):
        """
        GIVEN audio file exceeding size limit
        WHEN validate_audio() is called
        THEN ValueError is raised
        """
        large_audio = b"0" * (26 * 1024 * 1024)  # 26MB

        with pytest.raises(ValueError) as exc_info:
            processor.validate_audio(large_audio, "mp3")

        assert "too large" in str(exc_info.value).lower()

    # ==================== EDGE CASE 2: Silent audio ====================
    def test_transcribe_silent_returns_empty(self, processor: VoiceProcessor):
        """
        GIVEN audio with no speech
        WHEN transcribe() is called
        THEN empty string is returned
        """
        with patch("app.input.voice.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "text": "",
                "duration": 5.0,
                "language": "en"
            }
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            result = processor.transcribe(b"0" * 1000, "webm")

            assert result == ""

    # ==================== EDGE CASE 3: Unsupported format ====================
    def test_validate_unsupported_format_raises_error(self, processor: VoiceProcessor):
        """
        GIVEN unsupported audio format
        WHEN validate_audio() is called
        THEN ValueError is raised with supported formats
        """
        with pytest.raises(ValueError) as exc_info:
            processor.validate_audio(b"audio_data", "xyz")

        error_msg = str(exc_info.value).lower()
        assert "unsupported" in error_msg
        assert "mp3" in error_msg or "webm" in error_msg

    # ==================== EDGE CASE 4: API timeout ====================
    def test_transcribe_timeout_retries(self, processor: VoiceProcessor):
        """
        GIVEN Whisper API times out
        WHEN transcribe() is called
        THEN retry once before failing
        """
        import httpx

        with patch("app.input.voice.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = [
                httpx.TimeoutException("timeout"),
                MagicMock(
                    status_code=200,
                    json=lambda: {"text": "hello", "duration": 1.0}
                )
            ]

            result = processor.transcribe(b"0" * 1000, "webm")

            assert result == "hello"

    # ==================== EDGE CASE 5: Noisy audio low confidence ====================
    def test_transcribe_noisy_returns_low_confidence(self, processor: VoiceProcessor):
        """
        GIVEN audio with high noise
        WHEN transcribe_with_metadata() is called
        THEN result has low confidence score
        """
        with patch("app.input.voice.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "text": "maybe hello",
                "duration": 2.0,
                "language": "en",
                "segments": [{"no_speech_prob": 0.7}]  # High noise
            }
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            result = processor.transcribe_with_metadata(b"0" * 1000, "webm")

            assert result.confidence < 0.5

    # ==================== Additional Tests ====================
    def test_validate_empty_audio_raises_error(self, processor: VoiceProcessor):
        """Test that very small audio file is rejected."""
        with pytest.raises(ValueError) as exc_info:
            processor.validate_audio(b"tiny", "mp3")

        assert "small" in str(exc_info.value).lower()

    def test_transcribe_no_api_key_raises_error(self):
        """Test that missing API key raises error."""
        processor = VoiceProcessor(api_key=None)

        with pytest.raises(VoiceProcessingError) as exc_info:
            processor.transcribe(b"0" * 1000, "webm")

        assert "api key" in str(exc_info.value).lower()

    def test_transcribe_from_base64(self, processor: VoiceProcessor):
        """Test base64 transcription."""
        import base64

        with patch.object(processor, "transcribe") as mock_transcribe:
            mock_transcribe.return_value = "hello world"
            audio_b64 = base64.b64encode(b"audio_data").decode()

            result = processor.transcribe_from_base64(audio_b64, "webm")

            assert result == "hello world"
            mock_transcribe.assert_called_once()

    def test_transcribe_from_base64_invalid_encoding(self, processor: VoiceProcessor):
        """Test invalid base64 raises error."""
        with pytest.raises(VoiceProcessingError) as exc_info:
            processor.transcribe_from_base64("not-valid-base64!!!", "webm")

        assert "base64" in str(exc_info.value).lower()

    def test_supported_formats(self, processor: VoiceProcessor):
        """Test all supported formats are accepted."""
        for fmt in ["webm", "mp3", "wav", "m4a", "ogg", "flac"]:
            # Should not raise
            processor.validate_audio(b"0" * 1000, fmt)
