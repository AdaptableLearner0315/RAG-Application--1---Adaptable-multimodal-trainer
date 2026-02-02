"""
Embedding generation using sentence-transformers.
Generates vector embeddings for text to enable semantic search.
"""

from typing import List, Optional

from app.core.config import get_settings


class Embedder:
    """
    Generate embeddings for text using sentence-transformers.
    Uses all-MiniLM-L6-v2 by default (384 dimensions).
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedder with specified model.

        Args:
            model_name: Name of sentence-transformers model.
                       Defaults to config setting.

        Raises:
            ValueError: If model cannot be loaded.
        """
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self._model = None
        self._dimension = None

    def _load_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except Exception as e:
                raise ValueError(f"Failed to load model '{self.model_name}': {e}")

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        self._load_model()
        return self._dimension

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for input text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.

        Raises:
            ValueError: If text is empty.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        self._load_model()

        # Truncate if too long (model max is typically 512 tokens)
        max_chars = 2000  # Approximate
        if len(text) > max_chars:
            text = text[:max_chars]

        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        self._load_model()

        results = []
        valid_indices = []
        valid_texts = []

        # Separate valid and empty texts
        for i, text in enumerate(texts):
            if text and text.strip():
                # Truncate if needed
                if len(text) > 2000:
                    text = text[:2000]
                valid_texts.append(text)
                valid_indices.append(i)

        # Embed valid texts in batch
        if valid_texts:
            embeddings = self._model.encode(valid_texts, convert_to_numpy=True)
            embedding_map = {
                idx: emb.tolist()
                for idx, emb in zip(valid_indices, embeddings)
            }
        else:
            embedding_map = {}

        # Build result with zero vectors for empty texts
        zero_vector = [0.0] * self.dimension
        for i in range(len(texts)):
            if i in embedding_map:
                results.append(embedding_map[i])
            else:
                results.append(zero_vector)

        return results

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            Cosine similarity score between -1 and 1.
        """
        import numpy as np

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
