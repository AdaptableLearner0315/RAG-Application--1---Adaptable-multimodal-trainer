"""
Semantic text chunking for RAG.
Splits documents into coherent chunks while preserving context.
"""

import re
from typing import List, Optional

from app.core.config import get_settings


class SemanticChunker:
    """
    Split text into semantically coherent chunks for embedding.
    Respects sentence boundaries when possible.
    """

    def __init__(
        self,
        min_chunk_size: Optional[int] = None,
        max_chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ):
        """
        Initialize semantic chunker.

        Args:
            min_chunk_size: Minimum chunk size in characters.
            max_chunk_size: Maximum chunk size in characters.
            overlap: Overlap between chunks in characters.
        """
        settings = get_settings()

        # Convert token-based config to character-based (approx 4 chars/token)
        self.min_chunk_size = (min_chunk_size or settings.chunk_min_size) * 4
        self.max_chunk_size = (max_chunk_size or settings.chunk_max_size) * 4
        self.overlap = (overlap or settings.chunk_overlap) * 4

    def chunk(self, text: str) -> List[str]:
        """
        Split text into semantically coherent chunks.

        Args:
            text: Raw text to chunk.

        Returns:
            List of text chunks within size limits.
        """
        # Handle empty or whitespace-only text
        if not text or not text.strip():
            return []

        text = text.strip()

        # If text is shorter than min_chunk_size, return as single chunk
        if len(text) <= self.min_chunk_size:
            return [text]

        # Split into paragraphs first
        paragraphs = self._split_paragraphs(text)

        # Build chunks from paragraphs
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # If paragraph alone exceeds max, split it further
            if len(para) > self.max_chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # Split large paragraph into sentences
                para_chunks = self._split_large_paragraph(para)
                chunks.extend(para_chunks)
                continue

            # Check if adding paragraph exceeds max
            if len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                if chunks and self.overlap > 0:
                    overlap_text = self._get_overlap(chunks[-1])
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Filter out any empty chunks
        return [c for c in chunks if c.strip()]

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Input text.

        Returns:
            List of paragraphs.
        """
        # Split on double newlines or multiple newlines
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_large_paragraph(self, para: str) -> List[str]:
        """
        Split a large paragraph into smaller chunks at sentence boundaries.

        Args:
            para: Large paragraph text.

        Returns:
            List of chunks.
        """
        # Split into sentences
        sentences = self._split_sentences(para)

        if not sentences:
            # Force split if no sentence boundaries
            return self._force_split(para)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If single sentence exceeds max, force split it
            if len(sentence) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.extend(self._force_split(sentence))
                continue

            # Check if adding sentence exceeds max
            if len(current_chunk) + len(sentence) + 1 > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Input text.

        Returns:
            List of sentences.
        """
        # Simple sentence splitting on common delimiters
        # Handles periods, question marks, exclamation points
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _force_split(self, text: str) -> List[str]:
        """
        Force split text at max_chunk_size with word boundary respect.

        Args:
            text: Text to split.

        Returns:
            List of chunks.
        """
        chunks = []
        words = text.split()
        current_chunk = ""

        for word in words:
            if len(current_chunk) + len(word) + 1 > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _get_overlap(self, text: str) -> str:
        """
        Get overlap text from end of previous chunk.

        Args:
            text: Previous chunk text.

        Returns:
            Overlap text.
        """
        if len(text) <= self.overlap:
            return text

        # Try to break at word boundary
        overlap_text = text[-self.overlap:]
        space_idx = overlap_text.find(' ')
        if space_idx > 0:
            overlap_text = overlap_text[space_idx + 1:]

        return overlap_text

    def chunk_with_metadata(
        self,
        text: str,
        source: str = ""
    ) -> List[dict]:
        """
        Chunk text and include metadata.

        Args:
            text: Text to chunk.
            source: Source identifier for metadata.

        Returns:
            List of dicts with 'content' and 'metadata' keys.
        """
        chunks = self.chunk(text)

        return [
            {
                "content": chunk,
                "metadata": {
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "char_count": len(chunk)
                }
            }
            for i, chunk in enumerate(chunks)
        ]
