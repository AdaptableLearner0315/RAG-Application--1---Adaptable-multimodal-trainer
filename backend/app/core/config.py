"""
Centralized configuration for the Adaptive Coaching Platform.
All settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None  # For Whisper

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = base_dir / "data"
    storage_dir: Path = base_dir / "storage"
    chroma_dir: Path = storage_dir / "chroma_db"

    # LLM Configuration
    llm_model: str = "claude-sonnet-4-20250514"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7

    # Token Budgets
    system_prompt_budget: int = 500
    long_term_memory_budget: int = 400
    short_term_memory_budget: int = 800
    working_memory_budget: int = 500
    rag_context_budget: int = 1500
    query_budget: int = 200

    # Memory Configuration
    short_term_retention_days: int = 7
    max_conversation_turns: int = 10

    # Retrieval Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_top_k: int = 5
    similarity_threshold: float = 0.5

    # Chunking Configuration
    chunk_min_size: int = 200
    chunk_max_size: int = 800
    chunk_overlap: int = 50

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Image Configuration
    max_image_size_mb: float = 10.0
    max_image_dimension: int = 2048
    supported_image_formats: tuple = ("jpg", "jpeg", "png", "webp")

    # Voice Configuration
    max_audio_duration_sec: int = 30
    whisper_model: str = "whisper-1"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application configuration singleton.
    """
    return Settings()


def reset_settings() -> None:
    """Reset settings cache. Useful for testing."""
    get_settings.cache_clear()
