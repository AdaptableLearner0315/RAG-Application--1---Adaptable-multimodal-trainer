"""
Vector store operations using ChromaDB.
Handles document storage and similarity search.
"""

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.core.config import get_settings
from app.retrieval.embedder import Embedder


class Document(BaseModel):
    """Document with content and metadata."""
    id: str
    content: str
    metadata: Dict = {}
    score: Optional[float] = None


class VectorStore:
    """
    ChromaDB-based vector store for document storage and retrieval.
    Supports adding, querying, and deleting documents.
    """

    def __init__(
        self,
        collection_name: str = "default",
        persist_dir: Optional[Path] = None,
        embedder: Optional[Embedder] = None
    ):
        """
        Initialize vector store.

        Args:
            collection_name: Name of the ChromaDB collection.
            persist_dir: Directory to persist data. Defaults to config.
            embedder: Embedder instance for generating vectors.
        """
        settings = get_settings()
        self.persist_dir = persist_dir or settings.chroma_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.collection_name = collection_name
        self.embedder = embedder or Embedder()
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy initialize ChromaDB client."""
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.persist_dir),
                anonymized_telemetry=False
            ))
        return self._client

    def _get_collection(self):
        """Get or create collection."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def add(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.

        Args:
            documents: List of documents to add.
        """
        if not documents:
            return

        collection = self._get_collection()

        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # Generate embeddings
        embeddings = self.embedder.embed_batch(contents)

        collection.add(
            ids=ids,
            documents=contents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add texts to the vector store.

        Args:
            texts: List of text content.
            metadatas: Optional metadata for each text.
            ids: Optional IDs. Auto-generated if not provided.

        Returns:
            List of document IDs.
        """
        import uuid

        if not texts:
            return []

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        if metadatas is None:
            metadatas = [{} for _ in texts]

        documents = [
            Document(id=id_, content=text, metadata=meta)
            for id_, text, meta in zip(ids, texts, metadatas)
        ]

        self.add(documents)
        return ids

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """
        Query the vector store for similar documents.

        Args:
            query_text: Query text to search for.
            top_k: Number of results to return.
            filter_metadata: Optional metadata filter.

        Returns:
            List of similar documents with scores.

        Raises:
            ValueError: If query is empty.
        """
        if not query_text or not query_text.strip():
            raise ValueError("Query text cannot be empty")

        collection = self._get_collection()

        # Generate query embedding
        query_embedding = self.embedder.embed(query_text)

        # Build query params
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }

        if filter_metadata:
            query_params["where"] = filter_metadata

        results = collection.query(**query_params)

        # Parse results
        documents = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                content = results["documents"][0][i] if results["documents"] else ""
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                # Convert distance to similarity score (1 - distance for cosine)
                score = 1 - distance

                documents.append(Document(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    score=score
                ))

        return documents

    def delete(self, ids: List[str]) -> None:
        """
        Delete documents by ID.

        Args:
            ids: List of document IDs to delete.
        """
        if not ids:
            return

        collection = self._get_collection()
        collection.delete(ids=ids)

    def get(self, ids: List[str]) -> List[Document]:
        """
        Get documents by ID.

        Args:
            ids: List of document IDs.

        Returns:
            List of documents.
        """
        if not ids:
            return []

        collection = self._get_collection()
        results = collection.get(ids=ids)

        documents = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                content = results["documents"][i] if results["documents"] else ""
                metadata = results["metadatas"][i] if results["metadatas"] else {}

                documents.append(Document(
                    id=doc_id,
                    content=content,
                    metadata=metadata
                ))

        return documents

    def count(self) -> int:
        """Get number of documents in collection."""
        collection = self._get_collection()
        return collection.count()

    def clear(self) -> None:
        """Delete all documents in collection."""
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = None
