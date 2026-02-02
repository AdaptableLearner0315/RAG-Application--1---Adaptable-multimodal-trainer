"""
Hybrid search combining vector search with web search fallback.
Provides relevant context for RAG queries.
"""

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import get_settings
from app.retrieval.vectorstore import Document, VectorStore


@dataclass
class SearchResult:
    """Search result with source information."""
    content: str
    score: float
    source: str  # "vector" or "web"
    metadata: dict
    low_confidence: bool = False


class HybridSearcher:
    """
    Combine vector search with web search fallback.
    Returns ranked results from multiple sources.
    """

    def __init__(
        self,
        vectorstore: VectorStore,
        similarity_threshold: float = 0.5,
        web_search_enabled: bool = True
    ):
        """
        Initialize hybrid searcher.

        Args:
            vectorstore: Vector store for document search.
            similarity_threshold: Minimum similarity score.
            web_search_enabled: Whether to fall back to web search.
        """
        settings = get_settings()
        self.vectorstore = vectorstore
        self.similarity_threshold = similarity_threshold
        self.web_search_enabled = web_search_enabled
        self.top_k = settings.vector_top_k

    def search(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Search for relevant documents using hybrid approach.

        Args:
            query: Search query.
            top_k: Number of results to return.

        Returns:
            List of SearchResult objects ranked by relevance.

        Raises:
            ValueError: If query is too short.
        """
        if len(query.strip()) < 3:
            raise ValueError("Query too short (minimum 3 characters)")

        top_k = top_k or self.top_k
        results = []

        # Try vector search first
        try:
            vector_results = self._vector_search(query, top_k)
            results.extend(vector_results)
        except Exception:
            vector_results = []

        # Fall back to web if no vector results
        if not results and self.web_search_enabled:
            try:
                web_results = self._web_search(query, top_k)
                results.extend(web_results)
            except Exception:
                pass

        # Check if all results are below threshold
        if results and all(r.score < self.similarity_threshold for r in results):
            for r in results:
                r.low_confidence = True

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def _vector_search(self, query: str, top_k: int) -> List[SearchResult]:
        """
        Search vector store.

        Args:
            query: Search query.
            top_k: Number of results.

        Returns:
            List of search results from vector store.
        """
        documents = self.vectorstore.query(query, top_k=top_k)

        results = []
        for doc in documents:
            results.append(SearchResult(
                content=doc.content,
                score=doc.score or 0.0,
                source="vector",
                metadata=doc.metadata
            ))

        return results

    def _web_search(self, query: str, top_k: int) -> List[SearchResult]:
        """
        Search web using DuckDuckGo.

        Args:
            query: Search query.
            top_k: Number of results.

        Returns:
            List of search results from web.
        """
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                web_results = list(ddgs.text(
                    f"nutrition health fitness {query}",
                    max_results=top_k
                ))

            results = []
            for i, item in enumerate(web_results):
                # Assign decreasing score based on position
                score = 0.9 - (i * 0.1)
                results.append(SearchResult(
                    content=f"{item.get('title', '')}: {item.get('body', '')}",
                    score=max(score, 0.3),
                    source="web",
                    metadata={
                        "url": item.get("href", ""),
                        "title": item.get("title", "")
                    }
                ))

            return results

        except Exception:
            return []

    def search_with_fallback(
        self,
        query: str,
        top_k: Optional[int] = None,
        require_vector: bool = False
    ) -> List[SearchResult]:
        """
        Search with explicit fallback handling.

        Args:
            query: Search query.
            top_k: Number of results.
            require_vector: If True, don't use web fallback.

        Returns:
            List of search results.
        """
        top_k = top_k or self.top_k

        # Try vector first
        vector_results = []
        try:
            vector_results = self._vector_search(query, top_k)
        except Exception:
            pass

        if vector_results:
            return vector_results

        if require_vector:
            return []

        # Fallback to web
        if self.web_search_enabled:
            try:
                return self._web_search(query, top_k)
            except Exception:
                pass

        return []
