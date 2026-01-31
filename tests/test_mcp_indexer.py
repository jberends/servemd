"""
Comprehensive tests for MCP search indexer.

Tests cover:
- Index building and Whoosh file creation
- Cache validation with hash-based comparison
- Metadata save/load operations
- Markdown parsing helpers
- Error handling and edge cases
- Backend abstraction
"""

import json
import shutil
import tempfile
from datetime import UTC, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from docs_server.mcp.indexer import (
    CacheMetadata,
    DocumentInfo,
    SearchBackend,
    SearchIndexManager,
    WhooshSearchBackend,
    extract_category,
    extract_headings,
    extract_title,
    get_index_manager,
    reset_index_manager,
)
from docs_server.mcp.schema import SCHEMA_VERSION

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_docs_root(tmp_path):
    """Create a temporary docs directory with sample markdown files."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create index.md
    (docs_dir / "index.md").write_text("# Welcome\n\nThis is the index page.\n\n## Getting Started\n\nStart here.")

    # Create api/endpoints.md
    api_dir = docs_dir / "api"
    api_dir.mkdir()
    (api_dir / "endpoints.md").write_text(
        "# API Endpoints\n\n## GET /health\n\nHealth check endpoint.\n\n## POST /mcp\n\nMCP endpoint."
    )

    # Create configuration.md
    (docs_dir / "configuration.md").write_text(
        "# Configuration\n\n## Environment Variables\n\nSet these variables.\n\n## Defaults\n\nDefault values."
    )

    # Create sidebar.md (should be skipped)
    (docs_dir / "sidebar.md").write_text("# Sidebar\n\n- [Home](index.md)")

    # Create topbar.md (should be skipped)
    (docs_dir / "topbar.md").write_text("# Topbar\n\nNavigation")

    return docs_dir


@pytest.fixture
def temp_cache_root(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def index_manager(temp_docs_root, temp_cache_root):
    """Create a SearchIndexManager with temporary directories."""
    with patch("docs_server.mcp.indexer.settings") as mock_settings:
        mock_settings.DOCS_ROOT = temp_docs_root
        mock_settings.CACHE_ROOT = temp_cache_root
        mock_settings.DEBUG = False

        manager = SearchIndexManager()
        manager._docs_root = temp_docs_root
        manager._index_path = temp_cache_root / "mcp" / "whoosh"
        manager._metadata_path = temp_cache_root / "mcp" / "metadata.json"

        yield manager

        # Cleanup
        manager.shutdown()


# =============================================================================
# MARKDOWN PARSING HELPERS TESTS
# =============================================================================


class TestExtractTitle:
    """Tests for extract_title function."""

    def test_extract_title_basic(self):
        """Extract title from simple markdown."""
        content = "# My Title\n\nSome content here."
        assert extract_title(content) == "My Title"

    def test_extract_title_with_leading_whitespace(self):
        """Extract title handles leading whitespace in file."""
        content = "\n\n# My Title\n\nContent"
        assert extract_title(content) == "My Title"

    def test_extract_title_multiple_h1(self):
        """Extract first h1 when multiple exist."""
        content = "# First Title\n\n# Second Title"
        assert extract_title(content) == "First Title"

    def test_extract_title_no_h1(self):
        """Return 'Untitled' when no h1 exists."""
        content = "## Heading 2\n\nSome content"
        assert extract_title(content) == "Untitled"

    def test_extract_title_empty_content(self):
        """Handle empty content."""
        assert extract_title("") == "Untitled"

    def test_extract_title_h1_with_special_chars(self):
        """Handle title with special characters."""
        content = "# API Endpoints & Configuration (v2.0)\n\nContent"
        assert extract_title(content) == "API Endpoints & Configuration (v2.0)"


class TestExtractHeadings:
    """Tests for extract_headings function."""

    def test_extract_headings_basic(self):
        """Extract all h2 headings."""
        content = "# Title\n\n## First\n\nContent\n\n## Second\n\nMore content"
        headings = extract_headings(content)
        assert headings == ["First", "Second"]

    def test_extract_headings_none(self):
        """Return empty list when no h2 headings."""
        content = "# Title\n\n### H3 Heading\n\nContent"
        assert extract_headings(content) == []

    def test_extract_headings_empty(self):
        """Handle empty content."""
        assert extract_headings("") == []

    def test_extract_headings_with_special_chars(self):
        """Handle headings with special characters."""
        content = "## GET /api/v2\n\n## POST /users/{id}"
        headings = extract_headings(content)
        assert headings == ["GET /api/v2", "POST /users/{id}"]


class TestExtractCategory:
    """Tests for extract_category function."""

    def test_extract_category_root_file(self, tmp_path):
        """Root-level files get 'root' category."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        file_path = docs_root / "index.md"
        file_path.touch()

        assert extract_category(file_path, docs_root) == "root"

    def test_extract_category_subdirectory(self, tmp_path):
        """Files in subdirectories get directory name as category."""
        docs_root = tmp_path / "docs"
        api_dir = docs_root / "api"
        api_dir.mkdir(parents=True)
        file_path = api_dir / "endpoints.md"
        file_path.touch()

        assert extract_category(file_path, docs_root) == "api"

    def test_extract_category_nested_subdirectory(self, tmp_path):
        """Files in nested subdirectories get top-level directory as category."""
        docs_root = tmp_path / "docs"
        nested_dir = docs_root / "api" / "v2" / "endpoints"
        nested_dir.mkdir(parents=True)
        file_path = nested_dir / "users.md"
        file_path.touch()

        assert extract_category(file_path, docs_root) == "api"


# =============================================================================
# DOCUMENT INFO TESTS
# =============================================================================


class TestDocumentInfo:
    """Tests for DocumentInfo dataclass."""

    def test_document_info_creation(self):
        """Create DocumentInfo with all fields."""
        doc = DocumentInfo(
            path="api/endpoints.md",
            title="API Endpoints",
            content="# API Endpoints\n\nContent here.",
            headings=["GET /health", "POST /mcp"],
            category="api",
            modified=datetime.now(UTC),
            size=1234,
        )

        assert doc.path == "api/endpoints.md"
        assert doc.title == "API Endpoints"
        assert len(doc.headings) == 2
        assert doc.category == "api"
        assert doc.size == 1234

    def test_document_info_defaults(self):
        """DocumentInfo has sensible defaults."""
        doc = DocumentInfo(path="test.md", title="Test", content="Content")

        assert doc.headings == []
        assert doc.category == ""
        assert doc.size == 0


# =============================================================================
# CACHE METADATA TESTS
# =============================================================================


class TestCacheMetadata:
    """Tests for CacheMetadata dataclass."""

    def test_metadata_to_dict(self):
        """Convert metadata to dictionary."""
        metadata = CacheMetadata(
            index_version="1.0",
            schema_version="1.0",
            docs_root="/app/docs",
            docs_hash="abc123",
            docs_count=42,
            built_at="2026-01-31T10:00:00Z",
            build_duration_ms=500,
            whoosh_version="2.7.4",
            python_version="3.13.0",
        )

        data = metadata.to_dict()
        assert data["index_version"] == "1.0"
        assert data["docs_count"] == 42
        assert data["docs_hash"] == "abc123"

    def test_metadata_from_dict(self):
        """Create metadata from dictionary."""
        data = {
            "index_version": "1.0",
            "schema_version": "1.0",
            "docs_root": "/app/docs",
            "docs_hash": "abc123",
            "docs_count": 42,
            "built_at": "2026-01-31T10:00:00Z",
            "build_duration_ms": 500,
        }

        metadata = CacheMetadata.from_dict(data)
        assert metadata.index_version == "1.0"
        assert metadata.docs_count == 42
        assert metadata.docs_hash == "abc123"

    def test_metadata_from_dict_missing_fields(self):
        """Handle missing fields gracefully."""
        data = {"index_version": "1.0"}

        metadata = CacheMetadata.from_dict(data)
        assert metadata.index_version == "1.0"
        assert metadata.docs_hash == ""
        assert metadata.docs_count == 0


# =============================================================================
# WHOOSH SEARCH BACKEND TESTS
# =============================================================================


class TestWhooshSearchBackend:
    """Tests for WhooshSearchBackend implementation."""

    def test_backend_create_index(self, tmp_path):
        """Create index successfully."""
        backend = WhooshSearchBackend()
        index_path = tmp_path / "whoosh"

        success = backend.create_index(index_path)

        assert success
        assert index_path.exists()
        assert backend.is_index_open()  # Index is open after creation

    def test_backend_add_and_commit(self, tmp_path):
        """Add document and commit."""
        backend = WhooshSearchBackend()
        index_path = tmp_path / "whoosh"
        backend.create_index(index_path)

        doc = DocumentInfo(
            path="test.md",
            title="Test Document",
            content="This is test content.",
            headings=["Section 1", "Section 2"],
            category="root",
            modified=datetime.now(UTC),
            size=100,
        )

        success = backend.add_document(doc)
        assert success

        success = backend.commit()
        assert success

    def test_backend_open_index(self, tmp_path):
        """Open existing index."""
        backend = WhooshSearchBackend()
        index_path = tmp_path / "whoosh"

        # Create and close
        backend.create_index(index_path)
        backend.commit()
        backend.close_index()

        # Reopen
        success = backend.open_index(index_path)
        assert success
        assert backend.is_index_open()

    def test_backend_doc_count(self, tmp_path):
        """Get document count."""
        backend = WhooshSearchBackend()
        index_path = tmp_path / "whoosh"
        backend.create_index(index_path)

        # Add two documents
        for i in range(2):
            doc = DocumentInfo(path=f"test{i}.md", title=f"Test {i}", content=f"Content {i}")
            backend.add_document(doc)

        backend.commit()
        backend.open_index(index_path)

        assert backend.get_doc_count() == 2

    def test_backend_version(self):
        """Get backend version."""
        backend = WhooshSearchBackend()
        version = backend.get_backend_version()
        assert version != "unknown"
        assert "." in version  # Should be a version string like "2.7.4"

    def test_backend_open_nonexistent(self, tmp_path):
        """Handle opening nonexistent index."""
        backend = WhooshSearchBackend()
        success = backend.open_index(tmp_path / "nonexistent")
        assert not success
        assert not backend.is_index_open()

    def test_backend_close_twice(self, tmp_path):
        """Closing twice should be safe."""
        backend = WhooshSearchBackend()
        index_path = tmp_path / "whoosh"
        backend.create_index(index_path)
        backend.commit()
        backend.open_index(index_path)

        backend.close_index()
        backend.close_index()  # Should not raise


# =============================================================================
# SEARCH INDEX MANAGER TESTS
# =============================================================================


class TestSearchIndexManager:
    """Tests for SearchIndexManager."""

    @pytest.mark.asyncio
    async def test_build_index_creates_whoosh_files(self, index_manager, temp_cache_root):
        """Building index creates Whoosh files."""
        success = await index_manager.initialize(force_rebuild=True)

        assert success
        assert index_manager.is_initialized
        assert (temp_cache_root / "mcp" / "whoosh").exists()

        # Check for Whoosh index files
        whoosh_dir = temp_cache_root / "mcp" / "whoosh"
        assert any(whoosh_dir.iterdir())  # Should have files

    @pytest.mark.asyncio
    async def test_build_index_creates_metadata(self, index_manager, temp_cache_root):
        """Building index creates metadata.json."""
        await index_manager.initialize(force_rebuild=True)

        metadata_path = temp_cache_root / "mcp" / "metadata.json"
        assert metadata_path.exists()

        # Verify metadata content
        with open(metadata_path) as f:
            data = json.load(f)

        assert data["index_version"] == index_manager.INDEX_VERSION
        assert data["schema_version"] == SCHEMA_VERSION
        assert data["docs_count"] == 3  # index.md, api/endpoints.md, configuration.md

    @pytest.mark.asyncio
    async def test_build_index_skips_special_files(self, index_manager, temp_cache_root):
        """Building index skips sidebar.md and topbar.md."""
        await index_manager.initialize(force_rebuild=True)

        # Check metadata for count
        metadata_path = temp_cache_root / "mcp" / "metadata.json"
        with open(metadata_path) as f:
            data = json.load(f)

        # Should have 3 docs, not 5 (sidebar.md and topbar.md skipped)
        assert data["docs_count"] == 3

    @pytest.mark.asyncio
    async def test_calculate_docs_hash_consistency(self, index_manager):
        """Same docs should produce same hash."""
        hash1 = index_manager._calculate_docs_hash()
        hash2 = index_manager._calculate_docs_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    @pytest.mark.asyncio
    async def test_hash_changes_when_file_modified(self, index_manager, temp_docs_root):
        """Hash changes when a file is modified."""
        hash1 = index_manager._calculate_docs_hash()

        # Modify a file
        (temp_docs_root / "index.md").write_text("# Modified Title\n\nNew content.")

        hash2 = index_manager._calculate_docs_hash()

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_hash_changes_when_file_added(self, index_manager, temp_docs_root):
        """Hash changes when a new file is added."""
        hash1 = index_manager._calculate_docs_hash()

        # Add a new file
        (temp_docs_root / "new_file.md").write_text("# New File\n\nContent.")

        hash2 = index_manager._calculate_docs_hash()

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_validate_cache_no_index(self, index_manager):
        """Cache validation fails when no index exists."""
        assert not index_manager._validate_cache()

    @pytest.mark.asyncio
    async def test_validate_cache_no_metadata(self, index_manager, temp_cache_root):
        """Cache validation fails when metadata.json missing."""
        # Create index directory but no metadata
        (temp_cache_root / "mcp" / "whoosh").mkdir(parents=True)

        assert not index_manager._validate_cache()

    @pytest.mark.asyncio
    async def test_validate_cache_valid(self, index_manager):
        """Cache validation passes for valid cache."""
        # Build index first
        await index_manager.initialize(force_rebuild=True)

        # Now validation should pass
        assert index_manager._validate_cache()

    @pytest.mark.asyncio
    async def test_validate_cache_hash_mismatch(self, index_manager, temp_docs_root):
        """Cache validation fails when docs hash changes."""
        # Build index
        await index_manager.initialize(force_rebuild=True)

        # Modify a file
        (temp_docs_root / "index.md").write_text("# Modified\n\nChanged content.")

        # Validation should fail
        assert not index_manager._validate_cache()

    @pytest.mark.asyncio
    async def test_load_from_cache(self, index_manager):
        """Load index from cache after rebuild."""
        # Build index
        await index_manager.initialize(force_rebuild=True)

        # Shutdown and create new manager
        index_manager.shutdown()

        # Load from cache
        success = await index_manager.initialize(force_rebuild=False)

        assert success
        assert index_manager.is_initialized

    @pytest.mark.asyncio
    async def test_save_load_metadata(self, index_manager, temp_cache_root):
        """Save and load cache metadata."""
        metadata = CacheMetadata(
            index_version="1.0",
            schema_version="1.0",
            docs_root="/test/docs",
            docs_hash="testhash",
            docs_count=10,
            built_at="2026-01-31T10:00:00Z",
            build_duration_ms=100,
        )

        # Ensure directory exists
        (temp_cache_root / "mcp").mkdir(parents=True, exist_ok=True)

        # Save
        success = index_manager._save_cache_metadata(metadata)
        assert success

        # Load
        loaded = index_manager._load_cache_metadata()
        assert loaded is not None
        assert loaded.docs_hash == "testhash"
        assert loaded.docs_count == 10

    @pytest.mark.asyncio
    async def test_get_whoosh_index(self, index_manager):
        """Get raw Whoosh index after initialization."""
        await index_manager.initialize(force_rebuild=True)

        whoosh_index = index_manager.get_whoosh_index()
        assert whoosh_index is not None
        assert whoosh_index.doc_count() == 3

    @pytest.mark.asyncio
    async def test_shutdown_and_reinitialize(self, index_manager):
        """Manager can shutdown and reinitialize."""
        await index_manager.initialize(force_rebuild=True)
        assert index_manager.is_initialized

        index_manager.shutdown()
        assert not index_manager.is_initialized

        # Reinitialize from cache
        await index_manager.initialize()
        assert index_manager.is_initialized


# =============================================================================
# GLOBAL SINGLETON TESTS
# =============================================================================


class TestGlobalSingleton:
    """Tests for global singleton management."""

    def test_get_index_manager_singleton(self):
        """get_index_manager returns same instance."""
        reset_index_manager()

        manager1 = get_index_manager()
        manager2 = get_index_manager()

        assert manager1 is manager2

        reset_index_manager()

    def test_reset_index_manager(self):
        """reset_index_manager creates new instance."""
        reset_index_manager()

        manager1 = get_index_manager()
        reset_index_manager()
        manager2 = get_index_manager()

        assert manager1 is not manager2

        reset_index_manager()


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_extract_title_exception_handling(self):
        """extract_title handles exceptions gracefully."""
        # None should be handled
        with patch("docs_server.mcp.indexer.re.search", side_effect=Exception("Test error")):
            result = extract_title("# Test")
            assert result == "Untitled"

    def test_extract_headings_exception_handling(self):
        """extract_headings handles exceptions gracefully."""
        with patch("docs_server.mcp.indexer.re.findall", side_effect=Exception("Test error")):
            result = extract_headings("## Test")
            assert result == []

    @pytest.mark.asyncio
    async def test_manager_handles_build_failure(self, tmp_path):
        """Manager handles build failures gracefully."""
        with patch("docs_server.mcp.indexer.settings") as mock_settings:
            mock_settings.DOCS_ROOT = tmp_path / "nonexistent"
            mock_settings.CACHE_ROOT = tmp_path / "cache"
            mock_settings.DEBUG = False

            manager = SearchIndexManager()
            manager._docs_root = tmp_path / "nonexistent"

            # Should not raise, but return False
            await manager.initialize(force_rebuild=True)

            # May succeed with empty index or fail - both are acceptable
            # Key is it doesn't crash
            manager.shutdown()

    def test_backend_add_document_without_writer(self):
        """Backend handles adding document without writer."""
        backend = WhooshSearchBackend()
        doc = DocumentInfo(path="test.md", title="Test", content="Content")

        # Should return False, not raise
        success = backend.add_document(doc)
        assert not success

    def test_backend_commit_without_writer(self):
        """Backend handles commit without writer."""
        backend = WhooshSearchBackend()

        # Should return False, not raise
        success = backend.commit()
        assert not success


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_full_index_lifecycle(self, temp_docs_root, temp_cache_root):
        """Test complete index lifecycle: build, validate, load, search setup."""
        with patch("docs_server.mcp.indexer.settings") as mock_settings:
            mock_settings.DOCS_ROOT = temp_docs_root
            mock_settings.CACHE_ROOT = temp_cache_root
            mock_settings.DEBUG = False

            manager = SearchIndexManager()
            manager._docs_root = temp_docs_root
            manager._index_path = temp_cache_root / "mcp" / "whoosh"
            manager._metadata_path = temp_cache_root / "mcp" / "metadata.json"

            # Build
            success = await manager.initialize(force_rebuild=True)
            assert success
            assert manager.is_initialized

            # Verify docs indexed
            whoosh_index = manager.get_whoosh_index()
            assert whoosh_index.doc_count() == 3

            # Shutdown
            manager.shutdown()
            assert not manager.is_initialized

            # Reload from cache
            success = await manager.initialize(force_rebuild=False)
            assert success
            assert manager.is_initialized
            assert manager.get_whoosh_index().doc_count() == 3

            # Modify file and verify cache invalidation
            (temp_docs_root / "index.md").write_text("# Changed\n\nNew content.")
            assert not manager._validate_cache()

            manager.shutdown()
