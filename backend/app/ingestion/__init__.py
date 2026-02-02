"""Document ingestion module for loading and chunking documents."""

from app.ingestion.loader import DocumentLoader
from app.ingestion.chunker import SemanticChunker

__all__ = ["DocumentLoader", "SemanticChunker"]
