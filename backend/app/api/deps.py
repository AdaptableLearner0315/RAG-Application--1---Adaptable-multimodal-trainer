"""
Dependency injection for FastAPI routes.
Provides database connections, memory stores, and other shared resources.
"""

from functools import lru_cache
from typing import Generator, Optional

from app.core.config import Settings, get_settings
from app.memory.long_term import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore
from app.memory.working import WorkingMemoryStore
from app.memory.retriever import MemoryRetriever
from app.retrieval.search import HybridSearcher
from app.retrieval.embedder import Embedder
from app.retrieval.vectorstore import VectorStore


def get_long_term_store() -> LongTermMemoryStore:
    """
    Get long-term memory store instance.

    Returns:
        LongTermMemoryStore: SQLite-backed permanent profile store.
    """
    settings = get_settings()
    db_path = settings.storage_dir / "long_term.db"
    return LongTermMemoryStore(db_path=db_path)


def get_short_term_store() -> ShortTermMemoryStore:
    """
    Get short-term memory store instance.

    Returns:
        ShortTermMemoryStore: SQLite-backed rolling 7-day store.
    """
    settings = get_settings()
    db_path = settings.storage_dir / "short_term.db"
    return ShortTermMemoryStore(
        db_path=db_path,
        retention_days=settings.short_term_retention_days
    )


def get_working_store() -> WorkingMemoryStore:
    """
    Get working memory store instance.

    Returns:
        WorkingMemoryStore: Redis or in-memory session store.
    """
    settings = get_settings()

    # Try to connect to Redis, fall back to in-memory if unavailable
    redis_client = None
    try:
        import redis
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db
        )
        redis_client.ping()  # Test connection
    except Exception:
        redis_client = None  # Use in-memory fallback

    return WorkingMemoryStore(redis_client=redis_client)


def get_memory_retriever() -> MemoryRetriever:
    """
    Get memory retriever with all three stores.

    Returns:
        MemoryRetriever: Query-aware memory fetcher.
    """
    settings = get_settings()
    return MemoryRetriever(
        working=get_working_store(),
        short_term=get_short_term_store(),
        long_term=get_long_term_store(),
        token_budgets={
            "working": settings.working_memory_budget,
            "short_term": settings.short_term_memory_budget,
            "long_term": settings.long_term_memory_budget
        }
    )


@lru_cache
def get_embedder() -> Embedder:
    """
    Get cached embedder instance.

    Returns:
        Embedder: Sentence-transformers embedder.
    """
    settings = get_settings()
    return Embedder(model_name=settings.embedding_model)


def get_vectorstore() -> VectorStore:
    """
    Get vector store instance.

    Returns:
        VectorStore: ChromaDB vector store.
    """
    settings = get_settings()
    return VectorStore(
        persist_directory=str(settings.chroma_dir),
        embedder=get_embedder()
    )


def get_searcher() -> HybridSearcher:
    """
    Get hybrid searcher instance.

    Returns:
        HybridSearcher: Combined vector and web search.
    """
    settings = get_settings()
    return HybridSearcher(
        vectorstore=get_vectorstore(),
        similarity_threshold=settings.similarity_threshold
    )


def validate_user_id(user_id: str) -> str:
    """
    Validate user ID format.

    Args:
        user_id: User identifier to validate.

    Returns:
        Validated user ID.

    Raises:
        ValueError: If user ID is invalid.
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id cannot be empty")

    if len(user_id) > 128:
        raise ValueError("user_id cannot exceed 128 characters")

    return user_id.strip()


def validate_session_id(session_id: str) -> str:
    """
    Validate session ID format.

    Args:
        session_id: Session identifier to validate.

    Returns:
        Validated session ID.

    Raises:
        ValueError: If session ID is invalid.
    """
    if not session_id or not session_id.strip():
        raise ValueError("session_id cannot be empty")

    return session_id.strip()
