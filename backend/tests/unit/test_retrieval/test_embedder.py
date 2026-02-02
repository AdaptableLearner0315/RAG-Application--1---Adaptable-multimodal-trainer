"""
Unit tests for Embedder.
Tests 5 edge cases for embedding generation.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.retrieval.embedder import Embedder


class TestEmbedder:
    """Unit tests for Embedder class."""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer for testing without loading real model."""
        with patch("app.retrieval.embedder.SentenceTransformer") as mock:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = MagicMock(
                tolist=lambda: [0.1] * 384
            )
            mock.return_value = mock_model
            yield mock

    @pytest.fixture
    def embedder(self, mock_sentence_transformer) -> Embedder:
        """Create Embedder with mocked model."""
        emb = Embedder(model_name="test-model")
        emb._load_model()  # Force load with mock
        return emb

    # ==================== EDGE CASE 1: Empty string input ====================
    def test_embed_empty_string_raises_error(self, embedder: Embedder):
        """
        GIVEN empty string input
        WHEN embed() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError) as exc_info:
            embedder.embed("")

        assert "empty" in str(exc_info.value).lower()

    def test_embed_whitespace_only_raises_error(self, embedder: Embedder):
        """
        GIVEN whitespace-only string input
        WHEN embed() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError) as exc_info:
            embedder.embed("   \n\t  ")

        assert "empty" in str(exc_info.value).lower()

    # ==================== EDGE CASE 2: Text exceeds model max length ====================
    def test_embed_long_text_truncates(self, mock_sentence_transformer):
        """
        GIVEN text exceeding 2000 characters
        WHEN embed() is called
        THEN text is truncated before embedding
        """
        embedder = Embedder(model_name="test-model")
        long_text = "word " * 1000  # ~5000 chars

        result = embedder.embed(long_text)

        # Should succeed and return embedding
        assert isinstance(result, list)
        # Verify truncation happened by checking the encode call
        call_args = mock_sentence_transformer.return_value.encode.call_args
        encoded_text = call_args[0][0]
        assert len(encoded_text) <= 2000

    # ==================== EDGE CASE 3: Batch with empty strings ====================
    def test_embed_batch_handles_empty_strings(self, embedder: Embedder):
        """
        GIVEN batch with some empty strings
        WHEN embed_batch() is called
        THEN empty strings get zero vectors, valid texts get embeddings
        """
        texts = ["valid text", "", "another valid", "   "]

        result = embedder.embed_batch(texts)

        assert len(result) == 4
        # Empty strings should have zero vectors
        assert all(v == 0.0 for v in result[1])
        assert all(v == 0.0 for v in result[3])
        # Valid texts should have non-zero vectors
        assert not all(v == 0.0 for v in result[0])
        assert not all(v == 0.0 for v in result[2])

    # ==================== EDGE CASE 4: Model not available ====================
    def test_embed_missing_model_raises_error(self):
        """
        GIVEN invalid model name
        WHEN Embedder loads model
        THEN clear error is raised
        """
        with patch("app.retrieval.embedder.SentenceTransformer") as mock:
            mock.side_effect = Exception("Model not found")

            embedder = Embedder(model_name="nonexistent-model-xyz")

            with pytest.raises(ValueError) as exc_info:
                embedder.embed("test text")

            assert "model" in str(exc_info.value).lower()

    # ==================== EDGE CASE 5: Unicode/emoji in text ====================
    def test_embed_unicode_text_works(self, embedder: Embedder):
        """
        GIVEN text with unicode characters and emoji
        WHEN embed() is called
        THEN embedding is generated successfully
        """
        unicode_text = "Protein intake 蛋白质 🍗🥗 recommended daily"

        result = embedder.embed(unicode_text)

        assert isinstance(result, list)
        assert len(result) == 384

    # ==================== Additional Tests ====================
    def test_embed_returns_correct_dimension(self, embedder: Embedder):
        """Test that embedding has correct dimension."""
        result = embedder.embed("test text")
        assert len(result) == 384

    def test_embed_batch_empty_list(self, embedder: Embedder):
        """Test embedding empty list returns empty list."""
        result = embedder.embed_batch([])
        assert result == []

    def test_dimension_property(self, embedder: Embedder):
        """Test dimension property returns correct value."""
        assert embedder.dimension == 384

    def test_similarity_identical_vectors(self, embedder: Embedder):
        """Test similarity of identical vectors is 1.0."""
        vec = [0.1, 0.2, 0.3, 0.4]
        similarity = embedder.similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.0001

    def test_similarity_orthogonal_vectors(self, embedder: Embedder):
        """Test similarity of orthogonal vectors is 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = embedder.similarity(vec1, vec2)
        assert abs(similarity) < 0.0001

    def test_similarity_zero_vector(self, embedder: Embedder):
        """Test similarity with zero vector returns 0.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        similarity = embedder.similarity(vec1, vec2)
        assert similarity == 0.0
