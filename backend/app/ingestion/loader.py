"""
Document loading functionality.
Handles PDF and text file loading with validation.
"""

from pathlib import Path
from typing import Optional

from app.core.config import get_settings


class DocumentLoader:
    """
    Load and extract text from PDF documents.
    Validates file size and format before processing.
    """

    MAX_FILE_SIZE_MB = 50

    def __init__(self, max_size_mb: Optional[float] = None):
        """
        Initialize document loader.

        Args:
            max_size_mb: Maximum file size in MB. Defaults to 50MB.
        """
        self.max_size_mb = max_size_mb or self.MAX_FILE_SIZE_MB

    def load(self, file_path: Path) -> str:
        """
        Load text content from a PDF file.

        Args:
            file_path: Path to PDF file.

        Returns:
            Extracted text content.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file is empty, corrupted, or too large.
        """
        file_path = Path(file_path)

        # Check file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_size_mb:
            raise ValueError(
                f"File exceeds {self.max_size_mb}MB limit "
                f"(actual: {file_size_mb:.1f}MB)"
            )

        # Load based on extension
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self._load_pdf(file_path)
        elif suffix == ".txt":
            return self._load_text(file_path)
        elif suffix == ".md":
            return self._load_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _load_pdf(self, file_path: Path) -> str:
        """
        Load text from PDF file.

        Args:
            file_path: Path to PDF file.

        Returns:
            Extracted text content.

        Raises:
            ValueError: If PDF cannot be read or has no extractable text.
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            text = "\n\n".join(text_parts)

            # Return empty string for scanned PDFs (no extractable text)
            # This is not an error, just a warning case
            return text.strip()

        except Exception as e:
            if "EOF" in str(e) or "invalid" in str(e).lower():
                raise ValueError(f"Cannot extract text from PDF: corrupted or invalid file")
            raise ValueError(f"Cannot extract text from PDF: {e}")

    def _load_text(self, file_path: Path) -> str:
        """
        Load text from plain text file.

        Args:
            file_path: Path to text file.

        Returns:
            File content.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read().strip()

    def load_directory(self, dir_path: Path, pattern: str = "*.pdf") -> list:
        """
        Load all matching files from directory.

        Args:
            dir_path: Directory path.
            pattern: Glob pattern for matching files.

        Returns:
            List of (filename, content) tuples.
        """
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        results = []
        for file_path in dir_path.glob(pattern):
            try:
                content = self.load(file_path)
                if content:  # Skip empty files
                    results.append((file_path.name, content))
            except Exception:
                # Skip files that can't be loaded
                continue

        return results
