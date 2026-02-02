"""
Shared pytest fixtures for all tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest

from app.core.config import reset_settings


@pytest.fixture(autouse=True)
def reset_config():
    """Reset configuration singleton before each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set mock environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("DEBUG", "true")


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Generate valid PDF content for testing."""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test content) Tj ET
endstream
endobj
xref
0 5
trailer
<< /Size 5 /Root 1 0 R >>
startxref
0
%%EOF"""


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate valid PNG image bytes for testing."""
    # Minimal valid 1x1 red PNG
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x05, 0xFE,
        0xD4, 0xEF, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])


@pytest.fixture
def sample_user_profile() -> dict:
    """Sample user profile for testing."""
    return {
        "user_id": "test_user_123",
        "age": 17,
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "injuries": ["left knee strain"],
        "intolerances": ["lactose"],
        "allergies": [],
        "dietary_pref": "omnivore",
        "fitness_level": "intermediate",
        "primary_goal": "build_muscle",
        "target_weight_kg": 75.0
    }


@pytest.fixture
def sample_meal_log() -> dict:
    """Sample meal log for testing."""
    return {
        "time": "12:30",
        "foods": ["chicken breast", "brown rice", "broccoli"],
        "calories": 550,
        "protein": 45,
        "carbs": 60,
        "fat": 12
    }


@pytest.fixture
def sample_workout_log() -> dict:
    """Sample workout log for testing."""
    return {
        "time": "16:00",
        "type": "strength",
        "duration_min": 60,
        "intensity": "moderate",
        "exercises": ["squats", "lunges", "leg press"]
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_chroma_collection():
    """Mock ChromaDB collection for testing."""
    mock = MagicMock()
    mock.query.return_value = {
        "ids": [["doc1", "doc2"]],
        "documents": [["content1", "content2"]],
        "distances": [[0.1, 0.2]]
    }
    mock.add.return_value = None
    return mock
