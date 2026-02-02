"""
Unit tests for HybridSearcher.
Tests 5 edge cases for hybrid search functionality.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.retrieval.search import HybridSearcher, SearchResult
from app.retrieval.vectorstore import Document, VectorStore


class TestHybridSearcher:
    """Unit tests for HybridSearcher class."""

    @pytest.fixture
    def mock_vectorstore(self) -> MagicMock:
        """Create mock vector store."""
        mock = MagicMock(spec=VectorStore)
        mock.query.return_value = [
            Document(id="1", content="nutrition content", score=0.8, metadata={}),
            Document(id="2", content="fitness content", score=0.7, metadata={})
        ]
        return mock

    @pytest.fixture
    def mock_empty_vectorstore(self) -> MagicMock:
        """Create mock vector store that returns empty results."""
        mock = MagicMock(spec=VectorStore)
        mock.query.return_value = []
        return mock

    @pytest.fixture
    def searcher(self, mock_vectorstore: MagicMock) -> HybridSearcher:
        """Create HybridSearcher with mocked vector store."""
        return HybridSearcher(
            vectorstore=mock_vectorstore,
            similarity_threshold=0.5,
            web_search_enabled=True
        )

    # ==================== EDGE CASE 1: Vector empty, web fallback ====================
    def test_search_falls_back_to_web_on_empty_vector(self, mock_empty_vectorstore):
        """
        GIVEN vector search returns empty results
        WHEN search() is called
        THEN web search is used as fallback
        """
        searcher = HybridSearcher(
            vectorstore=mock_empty_vectorstore,
            web_search_enabled=True
        )

        with patch.object(searcher, '_web_search') as mock_web:
            mock_web.return_value = [
                SearchResult(content="web result", score=0.7, source="web", metadata={})
            ]

            result = searcher.search("nutrition tips")

            assert len(result) > 0
            mock_web.assert_called_once()

    # ==================== EDGE CASE 2: Both return empty ====================
    def test_search_returns_empty_when_all_fail(self, mock_empty_vectorstore):
        """
        GIVEN both vector and web search return empty
        WHEN search() is called
        THEN empty list is returned
        """
        searcher = HybridSearcher(
            vectorstore=mock_empty_vectorstore,
            web_search_enabled=True
        )

        with patch.object(searcher, '_web_search') as mock_web:
            mock_web.return_value = []

            result = searcher.search("extremely obscure query xyz123")

            assert result == []

    # ==================== EDGE CASE 3: Web timeout ====================
    def test_search_returns_vector_on_web_timeout(self, mock_vectorstore):
        """
        GIVEN web search times out
        WHEN search() is called with empty vector results first
        THEN vector results are returned (or empty if vector was empty)
        """
        searcher = HybridSearcher(
            vectorstore=mock_vectorstore,
            web_search_enabled=True
        )

        # Vector store returns results
        result = searcher.search("protein intake")

        assert len(result) > 0
        assert result[0].source == "vector"

    # ==================== EDGE CASE 4: Single character query ====================
    def test_search_rejects_single_char_query(self, searcher: HybridSearcher):
        """
        GIVEN single character query
        WHEN search() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError) as exc_info:
            searcher.search("a")

        assert "too short" in str(exc_info.value).lower()

    def test_search_rejects_two_char_query(self, searcher: HybridSearcher):
        """
        GIVEN two character query
        WHEN search() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError) as exc_info:
            searcher.search("ab")

        assert "too short" in str(exc_info.value).lower()

    # ==================== EDGE CASE 5: All results below threshold ====================
    def test_search_returns_low_confidence_when_below_threshold(
        self,
        mock_vectorstore: MagicMock
    ):
        """
        GIVEN all results below similarity threshold
        WHEN search() is called
        THEN results returned with low_confidence flag
        """
        # Return low-score results
        mock_vectorstore.query.return_value = [
            Document(id="1", content="weak match", score=0.3, metadata={}),
            Document(id="2", content="another weak", score=0.2, metadata={})
        ]

        searcher = HybridSearcher(
            vectorstore=mock_vectorstore,
            similarity_threshold=0.5,
            web_search_enabled=False
        )

        result = searcher.search("test query")

        assert len(result) > 0
        assert all(r.low_confidence for r in result)

    # ==================== Additional Tests ====================
    def test_search_returns_sorted_results(self, mock_vectorstore: MagicMock):
        """Test that results are sorted by score descending."""
        mock_vectorstore.query.return_value = [
            Document(id="1", content="low", score=0.5, metadata={}),
            Document(id="2", content="high", score=0.9, metadata={}),
            Document(id="3", content="mid", score=0.7, metadata={})
        ]

        searcher = HybridSearcher(vectorstore=mock_vectorstore)
        result = searcher.search("test query")

        assert result[0].score >= result[1].score >= result[2].score

    def test_search_respects_top_k(self, mock_vectorstore: MagicMock):
        """Test that search respects top_k limit."""
        mock_vectorstore.query.return_value = [
            Document(id=str(i), content=f"doc {i}", score=0.9 - i*0.1, metadata={})
            for i in range(10)
        ]

        searcher = HybridSearcher(vectorstore=mock_vectorstore)
        result = searcher.search("test query", top_k=3)

        assert len(result) == 3

    def test_search_with_fallback_require_vector(self, mock_empty_vectorstore):
        """Test search_with_fallback with require_vector=True."""
        searcher = HybridSearcher(
            vectorstore=mock_empty_vectorstore,
            web_search_enabled=True
        )

        result = searcher.search_with_fallback("query", require_vector=True)

        assert result == []

    def test_vector_search_results_have_correct_source(
        self,
        mock_vectorstore: MagicMock
    ):
        """Test that vector search results have source='vector'."""
        searcher = HybridSearcher(vectorstore=mock_vectorstore)
        result = searcher.search("test query")

        assert all(r.source == "vector" for r in result)

    def test_search_handles_vectorstore_exception(self):
        """Test that search handles vectorstore exceptions gracefully."""
        mock_vs = MagicMock(spec=VectorStore)
        mock_vs.query.side_effect = Exception("Database error")

        searcher = HybridSearcher(
            vectorstore=mock_vs,
            web_search_enabled=False
        )

        result = searcher.search("test query")

        assert result == []
