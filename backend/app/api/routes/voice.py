"""
Voice transcription endpoint for the Adaptive Coaching Platform.
Handles audio input via Whisper API.
"""

import base64
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.input.voice import VoiceProcessor

router = APIRouter()


class VoiceRequest(BaseModel):
    """Request body for voice transcription."""

    audio_base64: str = Field(..., description="Base64 encoded audio data")
    format: str = Field(default="webm", description="Audio format: webm, mp3, wav, m4a")


class VoiceResponse(BaseModel):
    """Response body for voice transcription."""

    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    duration_sec: Optional[float] = Field(default=None, description="Audio duration in seconds")


@router.post("/voice/transcribe", response_model=VoiceResponse)
async def transcribe_voice(request: VoiceRequest) -> VoiceResponse:
    """
    Transcribe audio to text using Whisper API.

    Args:
        request: Voice request with base64 audio and format.

    Returns:
        VoiceResponse with transcribed text and confidence.

    Raises:
        HTTPException: If transcription fails.
    """
    # Validate format
    supported_formats = {"webm", "mp3", "wav", "m4a", "ogg", "flac"}
    if request.format.lower() not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported: {', '.join(supported_formats)}"
        )

    # Decode audio
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid base64 encoding for audio data"
        )

    # Validate size (max 25MB for Whisper)
    max_size_bytes = 25 * 1024 * 1024
    if len(audio_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Audio file too large. Maximum size is 25MB, received {len(audio_bytes) / (1024*1024):.1f}MB"
        )

    # Empty audio check
    if len(audio_bytes) < 100:
        raise HTTPException(
            status_code=400,
            detail="Audio data too small or empty"
        )

    # Process voice
    processor = VoiceProcessor()

    try:
        result = processor.transcribe(audio_bytes, format=request.format)
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Transcription timed out. Please try again with shorter audio."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

    # Handle empty transcription
    if not result.text or result.text.strip() == "":
        return VoiceResponse(
            text="",
            confidence=0.0,
            duration_sec=result.duration_sec
        )

    return VoiceResponse(
        text=result.text,
        confidence=result.confidence,
        duration_sec=result.duration_sec
    )


@router.get("/voice/health")
async def health_check() -> dict:
    """
    Health check endpoint for voice service.

    Returns:
        Status dict.
    """
    return {"status": "healthy", "service": "voice"}
