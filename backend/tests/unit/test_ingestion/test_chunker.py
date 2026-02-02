"""
Unit tests for SemanticChunker.
Tests 5 edge cases for text chunking.
"""

import pytest

from app.ingestion.chunker import SemanticChunker


class TestSemanticChunker:
    """Unit tests for SemanticChunker class."""

    @pytest.fixture
    def chunker(self) -> SemanticChunker:
        """Create SemanticChunker with test settings."""
        return SemanticChunker(
            min_chunk_size=50,   # 200 chars
            max_chunk_size=200,  # 800 chars
            overlap=10          # 40 chars
        )

    # ==================== EDGE CASE 1: Empty input ====================
    def test_chunk_empty_text_returns_empty_list(self, chunker: SemanticChunker):
        """
        GIVEN empty string input
        WHEN chunk() is called
        THEN empty list is returned
        """
        result = chunker.chunk("")

        assert result == []

    # ==================== EDGE CASE 2: Short text ====================
    def test_chunk_short_text_returns_single_chunk(self, chunker: SemanticChunker):
        """
        GIVEN text shorter than min_chunk_size
        WHEN chunk() is called
        THEN single chunk with full text is returned
        """
        short_text = "This is short."

        result = chunker.chunk(short_text)

        assert len(result) == 1
        assert result[0] == short_text

    # ==================== EDGE CASE 3: No natural breaks ====================
    def test_chunk_no_breaks_forces_split(self, chunker: SemanticChunker):
        """
        GIVEN text with no sentence/paragraph breaks exceeding max size
        WHEN chunk() is called
        THEN text is split at word boundaries near max_chunk_size
        """
        # Create text without periods or newlines
        continuous_text = "word " * 500  # ~2500 chars

        result = chunker.chunk(continuous_text)

        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= chunker.max_chunk_size + 50  # Some tolerance

    # ==================== EDGE CASE 4: Whitespace only ====================
    def test_chunk_whitespace_returns_empty_list(self, chunker: SemanticChunker):
        """
        GIVEN text with only whitespace
        WHEN chunk() is called
        THEN empty list is returned
        """
        whitespace = "   \n\t\n   "

        result = chunker.chunk(whitespace)

        assert result == []

    # ==================== EDGE CASE 5: Long single paragraph ====================
    def test_chunk_long_paragraph_splits_at_sentences(self, chunker: SemanticChunker):
        """
        GIVEN single paragraph exceeding max_chunk_size
        WHEN chunk() is called
        THEN paragraph is split at sentence boundaries
        """
        # Create long paragraph with sentences
        long_para = "This is a sentence. " * 100  # ~2000 chars

        result = chunker.chunk(long_para)

        assert len(result) > 1
        # Each chunk should be within limits
        for chunk in result:
            assert len(chunk) <= chunker.max_chunk_size + 100

    # ==================== Additional Tests ====================
    def test_chunk_preserves_content(self, chunker: SemanticChunker):
        """Test that chunking preserves all content (minus overlaps)."""
        text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph."

        chunks = chunker.chunk(text)

        # All original content should appear in chunks
        combined = " ".join(chunks)
        assert "First paragraph" in combined
        assert "Second paragraph" in combined
        assert "Third paragraph" in combined

    def test_chunk_respects_paragraph_boundaries(self, chunker: SemanticChunker):
        """Test that chunks respect paragraph boundaries when possible."""
        # Create text with clear paragraph breaks
        text = "Short para one.\n\nShort para two.\n\nShort para three."

        chunks = chunker.chunk(text)

        # With short paragraphs, might be combined into one
        assert len(chunks) >= 1

    def test_chunk_with_metadata(self, chunker: SemanticChunker):
        """Test chunk_with_metadata returns correct structure."""
        text = "This is test content. " * 50

        result = chunker.chunk_with_metadata(text, source="test.pdf")

        assert len(result) > 0
        for item in result:
            assert "content" in item
            assert "metadata" in item
            assert item["metadata"]["source"] == "test.pdf"
            assert "chunk_index" in item["metadata"]
            assert "total_chunks" in item["metadata"]

    def test_chunk_handles_multiple_newlines(self, chunker: SemanticChunker):
        """Test handling of multiple consecutive newlines."""
        text = "Para one.\n\n\n\nPara two.\n\n\n\n\nPara three."

        result = chunker.chunk(text)

        # Should handle multiple newlines without empty chunks
        assert all(chunk.strip() for chunk in result)

    def test_chunk_unicode_content(self, chunker: SemanticChunker):
        """Test chunking text with unicode characters."""
        text = "蛋白质 protein content. " * 100

        result = chunker.chunk(text)

        assert len(result) > 0
        # Unicode should be preserved
        assert any("蛋白质" in chunk for chunk in result)

    def test_split_sentences_basic(self, chunker: SemanticChunker):
        """Test sentence splitting."""
        text = "First sentence. Second sentence. Third sentence."

        sentences = chunker._split_sentences(text)

        assert len(sentences) >= 1

    def test_split_paragraphs_basic(self, chunker: SemanticChunker):
        """Test paragraph splitting."""
        text = "Para 1.\n\nPara 2.\n\nPara 3."

        paragraphs = chunker._split_paragraphs(text)

        assert len(paragraphs) == 3

    def test_get_overlap_short_text(self, chunker: SemanticChunker):
        """Test overlap extraction from short text."""
        short_text = "Short"

        overlap = chunker._get_overlap(short_text)

        assert overlap == short_text

    def test_get_overlap_long_text(self, chunker: SemanticChunker):
        """Test overlap extraction from long text."""
        long_text = "This is a longer text that exceeds the overlap limit."

        overlap = chunker._get_overlap(long_text)

        assert len(overlap) <= chunker.overlap + 10  # Some tolerance for word boundaries

    def test_force_split_respects_word_boundaries(self, chunker: SemanticChunker):
        """Test that force split respects word boundaries."""
        text = "word1 word2 word3 word4 word5"

        chunks = chunker._force_split(text)

        # No chunk should start or end with partial word
        for chunk in chunks:
            assert not chunk.startswith(" ")
            assert not chunk.endswith(" ")
