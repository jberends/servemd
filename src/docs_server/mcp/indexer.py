"""
MCP Search Index Manager.

This module provides a robust, encapsulated search indexing system.
The implementation uses an abstract backend protocol to allow easy
replacement of the underlying search engine.

Design Principles:
1. ENCAPSULATION: All index operations go through SearchIndexManager
2. ROBUSTNESS: Every operation has error handling and fallbacks
3. REPLACEABILITY: SearchBackend protocol allows swapping implementations
4. VALIDATION: Hash-based cache validation ensures index integrity

Usage:
    from docs_server.mcp.indexer import get_index_manager

    manager = get_index_manager()
    await manager.initialize()  # Build or load index
    results = manager.search("query")  # Search
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from ..config import settings
from .schema import SCHEMA_VERSION, create_whoosh_schema

if TYPE_CHECKING:
    from whoosh.index import Index

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class DocumentInfo:
    """Represents a document to be indexed."""

    path: str
    title: str
    content: str
    headings: list[str] = field(default_factory=list)
    category: str = ""
    modified: datetime = field(default_factory=lambda: datetime.now(UTC))
    size: int = 0


@dataclass
class CacheMetadata:
    """Metadata for cache validation."""

    index_version: str
    schema_version: str
    docs_root: str
    docs_hash: str
    docs_count: int
    built_at: str
    build_duration_ms: int
    whoosh_version: str = ""
    python_version: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "index_version": self.index_version,
            "schema_version": self.schema_version,
            "docs_root": self.docs_root,
            "docs_hash": self.docs_hash,
            "docs_count": self.docs_count,
            "built_at": self.built_at,
            "build_duration_ms": self.build_duration_ms,
            "whoosh_version": self.whoosh_version,
            "python_version": self.python_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CacheMetadata:
        """Create from dictionary."""
        return cls(
            index_version=data.get("index_version", ""),
            schema_version=data.get("schema_version", ""),
            docs_root=data.get("docs_root", ""),
            docs_hash=data.get("docs_hash", ""),
            docs_count=data.get("docs_count", 0),
            built_at=data.get("built_at", ""),
            build_duration_ms=data.get("build_duration_ms", 0),
            whoosh_version=data.get("whoosh_version", ""),
            python_version=data.get("python_version", ""),
        )


# =============================================================================
# ABSTRACT SEARCH BACKEND PROTOCOL
# =============================================================================


class SearchBackend(ABC):
    """
    Abstract base class for search backends.

    Implement this protocol to add a new search engine.
    All methods must be thread-safe and handle their own errors gracefully.
    """

    @abstractmethod
    def create_index(self, index_path: Path) -> bool:
        """
        Create a new empty index at the specified path.

        Args:
            index_path: Directory path for the index

        Returns:
            True if successful, False otherwise
        """
        ...

    @abstractmethod
    def open_index(self, index_path: Path) -> bool:
        """
        Open an existing index.

        Args:
            index_path: Directory path to the index

        Returns:
            True if successful, False otherwise
        """
        ...

    @abstractmethod
    def close_index(self) -> None:
        """Close the index and release resources."""
        ...

    @abstractmethod
    def is_index_open(self) -> bool:
        """Check if an index is currently open."""
        ...

    @abstractmethod
    def add_document(self, doc: DocumentInfo) -> bool:
        """
        Add a document to the index.

        Args:
            doc: Document information to index

        Returns:
            True if successful, False otherwise
        """
        ...

    @abstractmethod
    def commit(self) -> bool:
        """
        Commit pending changes to the index.

        Returns:
            True if successful, False otherwise
        """
        ...

    @abstractmethod
    def get_doc_count(self) -> int:
        """Get the number of documents in the index."""
        ...

    @abstractmethod
    def get_backend_version(self) -> str:
        """Get the version string of the backend implementation."""
        ...


# =============================================================================
# WHOOSH SEARCH BACKEND IMPLEMENTATION
# =============================================================================


class WhooshSearchBackend(SearchBackend):
    """
    Whoosh-based search backend implementation.

    This implementation is designed to be robust:
    - All operations are wrapped in try/except
    - Index operations are atomic where possible
    - Resources are properly managed
    """

    def __init__(self):
        self._index: Index | None = None
        self._writer = None
        self._schema = create_whoosh_schema()

    def create_index(self, index_path: Path) -> bool:
        """Create a new Whoosh index."""
        try:
            from whoosh.index import create_in

            # Ensure clean directory
            if index_path.exists():
                shutil.rmtree(index_path)
            index_path.mkdir(parents=True, exist_ok=True)

            self._index = create_in(str(index_path), self._schema)
            self._writer = self._index.writer()
            logger.debug(f"Created Whoosh index at {index_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create Whoosh index: {e}", exc_info=True)
            self._index = None
            self._writer = None
            return False

    def open_index(self, index_path: Path) -> bool:
        """Open an existing Whoosh index."""
        try:
            from whoosh.index import open_dir

            if not index_path.exists():
                logger.warning(f"Index path does not exist: {index_path}")
                return False

            self._index = open_dir(str(index_path))
            logger.debug(f"Opened Whoosh index from {index_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to open Whoosh index: {e}", exc_info=True)
            self._index = None
            return False

    def close_index(self) -> None:
        """Close the Whoosh index."""
        try:
            if self._writer is not None:
                try:
                    self._writer.cancel()
                except Exception:
                    pass  # Writer might already be committed
                self._writer = None

            if self._index is not None:
                self._index.close()
                self._index = None
                logger.debug("Closed Whoosh index")

        except Exception as e:
            logger.warning(f"Error closing Whoosh index: {e}")
            self._index = None
            self._writer = None

    def is_index_open(self) -> bool:
        """Check if index is open."""
        return self._index is not None

    def add_document(self, doc: DocumentInfo) -> bool:
        """Add a document to the index."""
        try:
            if self._writer is None:
                logger.error("Cannot add document: writer not initialized")
                return False

            self._writer.add_document(
                path=doc.path,
                title=doc.title,
                content=doc.content,
                content_stored=doc.content,
                headings=" ".join(doc.headings),
                category=doc.category,
                modified=doc.modified,
                size=doc.size,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to add document {doc.path}: {e}", exc_info=True)
            return False

    def commit(self) -> bool:
        """Commit changes to the index."""
        try:
            if self._writer is None:
                logger.warning("Cannot commit: writer not initialized")
                return False

            self._writer.commit()
            self._writer = None  # Writer is consumed after commit
            logger.debug("Committed Whoosh index")
            return True

        except Exception as e:
            logger.error(f"Failed to commit Whoosh index: {e}", exc_info=True)
            return False

    def get_doc_count(self) -> int:
        """Get document count."""
        try:
            if self._index is None:
                return 0
            return self._index.doc_count()
        except Exception as e:
            logger.warning(f"Error getting doc count: {e}")
            return 0

    def get_backend_version(self) -> str:
        """Get Whoosh version."""
        try:
            import whoosh

            return whoosh.versionstring()
        except Exception:
            return "unknown"

    def get_index(self) -> Index | None:
        """Get the raw Whoosh index (for search operations)."""
        return self._index


# =============================================================================
# MARKDOWN PARSING HELPERS
# =============================================================================


def extract_title(content: str) -> str:
    """
    Extract the title from markdown content.

    Looks for the first # heading in the document.

    Args:
        content: Raw markdown content

    Returns:
        Title string, or "Untitled" if not found
    """
    try:
        # Match first h1 heading: # Title
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled"
    except Exception as e:
        logger.warning(f"Error extracting title: {e}")
        return "Untitled"


def extract_headings(content: str) -> list[str]:
    """
    Extract all h2 headings from markdown content.

    Args:
        content: Raw markdown content

    Returns:
        List of h2 heading strings
    """
    try:
        # Match all h2 headings: ## Heading
        matches = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
        return [h.strip() for h in matches]
    except Exception as e:
        logger.warning(f"Error extracting headings: {e}")
        return []


def extract_category(file_path: Path, docs_root: Path) -> str:
    """
    Extract category from file path.

    Uses the parent directory name as category.
    Root-level files get category "root".

    Args:
        file_path: Path to the markdown file
        docs_root: Root documentation directory

    Returns:
        Category string
    """
    try:
        rel_path = file_path.relative_to(docs_root)
        parent = rel_path.parent

        if parent == Path("."):
            return "root"
        return str(parent.parts[0]) if parent.parts else "root"
    except Exception as e:
        logger.warning(f"Error extracting category from {file_path}: {e}")
        return "unknown"


# =============================================================================
# SEARCH INDEX MANAGER
# =============================================================================


class SearchIndexManager:
    """
    Manages the search index lifecycle.

    This is the main entry point for all index operations.
    It handles:
    - Index creation and loading
    - Cache validation
    - Metadata management
    - Error recovery

    The manager is designed to be resilient:
    - If cache is invalid, it rebuilds
    - If rebuild fails, it provides empty results (graceful degradation)
    - All operations are logged for debugging
    """

    # Special files to skip during indexing
    SKIP_FILES = {"sidebar.md", "topbar.md", "llms.txt"}

    # Index version for cache invalidation
    INDEX_VERSION = "1.0"

    def __init__(self, backend: SearchBackend | None = None):
        """
        Initialize the index manager.

        Args:
            backend: Search backend to use (defaults to Whoosh)
        """
        self._backend = backend or WhooshSearchBackend()
        self._initialized = False
        self._index_path = settings.CACHE_ROOT / "mcp" / "whoosh"
        self._metadata_path = settings.CACHE_ROOT / "mcp" / "metadata.json"
        self._docs_root = settings.DOCS_ROOT

    @property
    def is_initialized(self) -> bool:
        """Check if the index is ready for use."""
        return self._initialized and self._backend.is_index_open()

    async def initialize(self, force_rebuild: bool = False) -> bool:
        """
        Initialize the search index.

        This is the main entry point. It will:
        1. Validate existing cache
        2. Load from cache if valid
        3. Rebuild if invalid or forced

        Args:
            force_rebuild: Force index rebuild even if cache is valid

        Returns:
            True if index is ready, False otherwise
        """
        import time

        start_time = time.perf_counter()

        try:
            # In DEBUG mode, always rebuild for fresh data
            if settings.DEBUG:
                logger.info("DEBUG mode: forcing index rebuild")
                force_rebuild = True

            # Check if we can use cached index
            if not force_rebuild and self._validate_cache():
                success = await self._load_from_cache()
                if success:
                    elapsed = (time.perf_counter() - start_time) * 1000
                    doc_count = self._backend.get_doc_count()
                    logger.info(f"[MCP] index loaded from cache: {doc_count} docs ({elapsed:.1f}ms)")
                    self._initialized = True
                    return True
                else:
                    logger.warning("Cache validation passed but load failed, rebuilding...")

            # Build new index
            success = await self._build_index()
            elapsed = (time.perf_counter() - start_time) * 1000

            if success:
                doc_count = self._backend.get_doc_count()
                logger.info(f"[MCP] index built: {doc_count} docs ({elapsed:.1f}ms)")
                self._initialized = True
            else:
                logger.error(f"[MCP] index build failed ({elapsed:.1f}ms)")
                self._initialized = False

            return success

        except Exception as e:
            logger.error(f"Failed to initialize MCP index: {e}", exc_info=True)
            self._initialized = False
            return False

    def _validate_cache(self) -> bool:
        """
        Validate the cached index using hash-based comparison.

        Returns:
            True if cache is valid and can be used
        """
        try:
            # Check if index directory exists
            if not self._index_path.exists():
                logger.debug("Cache invalid: index path does not exist")
                return False

            # Check if metadata exists
            if not self._metadata_path.exists():
                logger.debug("Cache invalid: metadata.json does not exist")
                return False

            # Load and validate metadata
            metadata = self._load_cache_metadata()
            if metadata is None:
                logger.debug("Cache invalid: could not load metadata")
                return False

            # Check index version
            if metadata.index_version != self.INDEX_VERSION:
                logger.debug(f"Cache invalid: version mismatch ({metadata.index_version} != {self.INDEX_VERSION})")
                return False

            # Check schema version
            if metadata.schema_version != SCHEMA_VERSION:
                logger.debug("Cache invalid: schema version mismatch")
                return False

            # Check docs root path
            if metadata.docs_root != str(self._docs_root.absolute()):
                logger.debug("Cache invalid: DOCS_ROOT path changed")
                return False

            # Calculate current docs hash and compare
            current_hash = self._calculate_docs_hash()
            if current_hash != metadata.docs_hash:
                logger.debug("Cache invalid: docs hash changed")
                return False

            logger.debug("Cache validation passed")
            return True

        except Exception as e:
            logger.warning(f"Cache validation error: {e}")
            return False

    def _calculate_docs_hash(self) -> str:
        """
        Calculate SHA256 hash of all documentation files.

        The hash includes:
        - File paths (sorted for determinism)
        - File modification times
        - File sizes

        This allows detecting any changes to documentation.

        Returns:
            Hex-encoded SHA256 hash string
        """
        try:
            hasher = hashlib.sha256()

            # Collect all .md files
            md_files: list[Path] = []
            for file_path in sorted(self._docs_root.rglob("*.md")):
                if file_path.name not in self.SKIP_FILES:
                    md_files.append(file_path)

            # Hash file metadata (path + mtime + size)
            for file_path in md_files:
                try:
                    stat = file_path.stat()
                    rel_path = str(file_path.relative_to(self._docs_root))
                    hash_data = f"{rel_path}:{stat.st_mtime}:{stat.st_size}\n"
                    hasher.update(hash_data.encode("utf-8"))
                except (OSError, ValueError) as e:
                    logger.warning(f"Error hashing {file_path}: {e}")
                    continue

            return hasher.hexdigest()

        except Exception as e:
            logger.error(f"Error calculating docs hash: {e}")
            return ""

    def _load_cache_metadata(self) -> CacheMetadata | None:
        """Load cache metadata from disk."""
        try:
            with open(self._metadata_path, encoding="utf-8") as f:
                data = json.load(f)
            return CacheMetadata.from_dict(data)
        except Exception as e:
            logger.warning(f"Error loading cache metadata: {e}")
            return None

    def _save_cache_metadata(self, metadata: CacheMetadata) -> bool:
        """Save cache metadata to disk."""
        try:
            self._metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving cache metadata: {e}")
            return False

    async def _load_from_cache(self) -> bool:
        """Load index from cache."""
        try:
            success = self._backend.open_index(self._index_path)
            if success:
                logger.debug(f"Loaded index with {self._backend.get_doc_count()} documents")
            return success
        except Exception as e:
            logger.error(f"Error loading index from cache: {e}")
            return False

    async def _build_index(self) -> bool:
        """
        Build a fresh search index from documentation files.

        Returns:
            True if successful
        """
        import sys
        import time

        start_time = time.perf_counter()

        try:
            # Close any existing index
            self._backend.close_index()

            # Create new index
            if not self._backend.create_index(self._index_path):
                logger.error("Failed to create index")
                return False

            # Collect and index all markdown files
            indexed_count = 0
            error_count = 0

            for file_path in sorted(self._docs_root.rglob("*.md")):
                # Skip special files
                if file_path.name in self.SKIP_FILES:
                    continue

                try:
                    doc = self._parse_document(file_path)
                    if doc and self._backend.add_document(doc):
                        indexed_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.warning(f"Error indexing {file_path}: {e}")
                    error_count += 1

            # Commit the index
            if not self._backend.commit():
                logger.error("Failed to commit index")
                return False

            # Reopen index for reading
            if not self._backend.open_index(self._index_path):
                logger.error("Failed to reopen index after build")
                return False

            # Calculate build duration
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            # Save metadata
            metadata = CacheMetadata(
                index_version=self.INDEX_VERSION,
                schema_version=SCHEMA_VERSION,
                docs_root=str(self._docs_root.absolute()),
                docs_hash=self._calculate_docs_hash(),
                docs_count=indexed_count,
                built_at=datetime.now(UTC).isoformat(),
                build_duration_ms=elapsed_ms,
                whoosh_version=self._backend.get_backend_version(),
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            )
            self._save_cache_metadata(metadata)

            if error_count > 0:
                logger.warning(f"Indexed {indexed_count} docs with {error_count} errors")
            else:
                logger.debug(f"Indexed {indexed_count} documents")

            return True

        except Exception as e:
            logger.error(f"Error building index: {e}", exc_info=True)
            return False

    def _parse_document(self, file_path: Path) -> DocumentInfo | None:
        """
        Parse a markdown file into a DocumentInfo.

        Args:
            file_path: Path to the markdown file

        Returns:
            DocumentInfo or None if parsing fails
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            stat = file_path.stat()

            rel_path = str(file_path.relative_to(self._docs_root))

            return DocumentInfo(
                path=rel_path,
                title=extract_title(content),
                content=content,
                headings=extract_headings(content),
                category=extract_category(file_path, self._docs_root),
                modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                size=stat.st_size,
            )

        except Exception as e:
            logger.warning(f"Error parsing document {file_path}: {e}")
            return None

    def get_backend(self) -> SearchBackend:
        """Get the search backend (for search operations)."""
        return self._backend

    def get_whoosh_index(self) -> Index | None:
        """
        Get the raw Whoosh index for search operations.

        Note: This is Whoosh-specific. Use get_backend() for generic access.
        """
        if isinstance(self._backend, WhooshSearchBackend):
            return self._backend.get_index()
        return None

    def shutdown(self) -> None:
        """Shutdown the index manager and release resources."""
        try:
            self._backend.close_index()
            self._initialized = False
            logger.debug("Search index manager shut down")
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")


# =============================================================================
# GLOBAL SINGLETON
# =============================================================================

# Global singleton instance
_index_manager: SearchIndexManager | None = None


def get_index_manager() -> SearchIndexManager:
    """
    Get the global SearchIndexManager instance.

    Creates a new instance if one doesn't exist.

    Returns:
        The global SearchIndexManager
    """
    global _index_manager
    if _index_manager is None:
        _index_manager = SearchIndexManager()
    return _index_manager


def reset_index_manager() -> None:
    """
    Reset the global index manager.

    This is primarily for testing purposes.
    """
    global _index_manager
    if _index_manager is not None:
        _index_manager.shutdown()
        _index_manager = None
