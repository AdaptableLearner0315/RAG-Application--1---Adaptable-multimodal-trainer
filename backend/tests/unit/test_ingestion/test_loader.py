"""
Unit tests for DocumentLoader.
Tests 5 edge cases for document loading.
"""

import pytest
from pathlib import Path

from app.ingestion.loader import DocumentLoader


class TestDocumentLoader:
    """Unit tests for DocumentLoader class."""

    @pytest.fixture
    def loader(self) -> DocumentLoader:
        """Create DocumentLoader instance."""
        return DocumentLoader(max_size_mb=50)

    @pytest.fixture
    def valid_pdf_path(self, temp_dir: Path, sample_pdf_content: bytes) -> Path:
        """Create valid PDF file for testing."""
        pdf_path = temp_dir / "valid.pdf"
        pdf_path.write_bytes(sample_pdf_content)
        return pdf_path

    @pytest.fixture
    def valid_text_path(self, temp_dir: Path) -> Path:
        """Create valid text file for testing."""
        txt_path = temp_dir / "valid.txt"
        txt_path.write_text("This is test content.\nWith multiple lines.")
        return txt_path

    # ==================== EDGE CASE 1: File not found ====================
    def test_load_nonexistent_file_raises_error(self, loader: DocumentLoader):
        """
        GIVEN a path to a nonexistent file
        WHEN load() is called
        THEN FileNotFoundError is raised
        """
        fake_path = Path("/nonexistent/file.pdf")

        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load(fake_path)

        assert "not found" in str(exc_info.value).lower()

    # ==================== EDGE CASE 2: Corrupted PDF ====================
    def test_load_corrupted_pdf_raises_error(
        self,
        loader: DocumentLoader,
        temp_dir: Path
    ):
        """
        GIVEN a corrupted PDF file
        WHEN load() is called
        THEN ValueError is raised with descriptive message
        """
        corrupted = temp_dir / "corrupted.pdf"
        corrupted.write_bytes(b"not a real pdf content at all")

        with pytest.raises(ValueError) as exc_info:
            loader.load(corrupted)

        error_msg = str(exc_info.value).lower()
        assert "cannot extract" in error_msg or "corrupted" in error_msg or "invalid" in error_msg

    # ==================== EDGE CASE 3: Scanned PDF (no text) ====================
    def test_load_scanned_pdf_returns_empty(
        self,
        loader: DocumentLoader,
        temp_dir: Path
    ):
        """
        GIVEN a PDF with no extractable text (simulated)
        WHEN load() is called
        THEN empty string is returned
        """
        # Create minimal valid PDF with no text content
        minimal_pdf = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer << /Size 4 /Root 1 0 R >>
startxref
193
%%EOF"""

        scanned = temp_dir / "scanned.pdf"
        scanned.write_bytes(minimal_pdf)

        result = loader.load(scanned)

        # Should return empty string, not raise error
        assert result == ""

    # ==================== EDGE CASE 4: Oversized PDF ====================
    def test_load_oversized_pdf_raises_error(
        self,
        temp_dir: Path
    ):
        """
        GIVEN a PDF exceeding size limit
        WHEN load() is called
        THEN ValueError is raised
        """
        loader = DocumentLoader(max_size_mb=0.001)  # Very small limit

        large_file = temp_dir / "large.pdf"
        # Create file > 1KB
        large_file.write_bytes(b"0" * 2000)

        with pytest.raises(ValueError) as exc_info:
            loader.load(large_file)

        assert "limit" in str(exc_info.value).lower() or "exceeds" in str(exc_info.value).lower()

    # ==================== EDGE CASE 5: Unicode path ====================
    def test_load_unicode_path_works(
        self,
        loader: DocumentLoader,
        temp_dir: Path
    ):
        """
        GIVEN a file with unicode characters in path
        WHEN load() is called
        THEN file is loaded successfully
        """
        unicode_path = temp_dir / "документ_日本語.txt"
        unicode_path.write_text("Test content with unicode: 蛋白质")

        result = loader.load(unicode_path)

        assert "Test content" in result
        assert "蛋白质" in result

    # ==================== Additional Tests ====================
    def test_load_text_file(
        self,
        loader: DocumentLoader,
        valid_text_path: Path
    ):
        """Test loading plain text file."""
        result = loader.load(valid_text_path)

        assert "This is test content" in result
        assert "multiple lines" in result

    def test_load_markdown_file(
        self,
        loader: DocumentLoader,
        temp_dir: Path
    ):
        """Test loading markdown file."""
        md_path = temp_dir / "readme.md"
        md_path.write_text("# Title\n\nSome content here.")

        result = loader.load(md_path)

        assert "# Title" in result
        assert "Some content here" in result

    def test_load_unsupported_format_raises_error(
        self,
        loader: DocumentLoader,
        temp_dir: Path
    ):
        """Test that unsupported file formats raise error."""
        unsupported = temp_dir / "file.xyz"
        unsupported.write_text("content")

        with pytest.raises(ValueError) as exc_info:
            loader.load(unsupported)

        assert "unsupported" in str(exc_info.value).lower()

    def test_load_directory_returns_list(
        self,
        loader: DocumentLoader,
        temp_dir: Path
    ):
        """Test loading all files from directory."""
        # Create multiple text files
        for i in range(3):
            (temp_dir / f"file{i}.txt").write_text(f"Content {i}")

        result = loader.load_directory(temp_dir, "*.txt")

        assert len(result) == 3
        assert all(isinstance(item, tuple) for item in result)

    def test_load_directory_skips_unreadable(
        self,
        loader: DocumentLoader,
        temp_dir: Path
    ):
        """Test that load_directory skips files that can't be loaded."""
        # Create one valid and one invalid file
        (temp_dir / "valid.txt").write_text("Valid content")
        (temp_dir / "invalid.pdf").write_bytes(b"not a pdf")

        result = loader.load_directory(temp_dir, "*.*")

        # Should have at least the valid file
        assert len(result) >= 1

    def test_load_directory_not_a_directory_raises_error(
        self,
        loader: DocumentLoader,
        temp_dir: Path
    ):
        """Test that load_directory raises error for non-directory path."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        with pytest.raises(ValueError) as exc_info:
            loader.load_directory(file_path)

        assert "not a directory" in str(exc_info.value).lower()
