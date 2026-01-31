"""
Configuration module for ServeMD Documentation Server.
Centralizes all environment variables and settings.
"""

import hashlib
import json
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Determine smart defaults based on environment
        default_docs = "/app/docs" if Path("/app").exists() else "./docs"
        default_cache = "/app/cache" if Path("/app").exists() else "./__cache__"

        # Load environment variables
        self.DOCS_ROOT = Path(os.getenv("DOCS_ROOT", default_docs))
        self.CACHE_ROOT = Path(os.getenv("CACHE_ROOT", default_cache))
        self.BASE_URL = os.getenv("BASE_URL", None)  # Base URL for absolute links in llms.txt
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.PORT = int(os.getenv("PORT", "8080"))

        # MCP Configuration
        self.MCP_ENABLED = os.getenv("MCP_ENABLED", "true").lower() == "true"
        self.MCP_RATE_LIMIT_REQUESTS = int(os.getenv("MCP_RATE_LIMIT_REQUESTS", "120"))
        self.MCP_RATE_LIMIT_WINDOW = int(os.getenv("MCP_RATE_LIMIT_WINDOW", "60"))
        self.MCP_MAX_SEARCH_RESULTS = int(os.getenv("MCP_MAX_SEARCH_RESULTS", "10"))
        self.MCP_SNIPPET_LENGTH = int(os.getenv("MCP_SNIPPET_LENGTH", "200"))

        # Markdown extensions configuration
        self.markdown_extensions = [
            "codehilite",
            "toc",
            "tables",
            "fenced_code",
            "footnotes",
            "attr_list",
            "def_list",
            "abbr",
            "pymdownx.superfences",
            "pymdownx.tasklist",
            "pymdownx.highlight",
            "pymdownx.inlinehilite",
        ]

        self.markdown_extension_configs = {
            "codehilite": {
                "css_class": "highlight",
                "use_pygments": True,
            },
            "toc": {
                "permalink": True,
                "toc_depth": 3,
                "permalink_title": "🔗",  # Use link icon instead of paragraph symbol
            },
            "pymdownx.superfences": {
                "custom_fences": [
                    {
                        "name": "mermaid",
                        "class": "mermaid",
                        "format": lambda source: f'<div class="mermaid">{source}</div>',
                    }
                ]
            },
            "pymdownx.tasklist": {
                "custom_checkbox": True,
            },
        }

        # Initialize directories
        self._init_directories()

    def _calculate_docs_hash(self) -> str:
        """
        Calculate SHA256 hash of all documentation files.

        Includes file paths, modification times, and sizes for accurate
        change detection. Same algorithm used by MCP indexer.

        Returns:
            Hex-encoded SHA256 hash string
        """
        try:
            hasher = hashlib.sha256()

            # Collect all .md files (sorted for deterministic hash)
            md_files: list[Path] = []
            if self.DOCS_ROOT.exists():
                for file_path in sorted(self.DOCS_ROOT.rglob("*.md")):
                    md_files.append(file_path)

            # Hash file metadata (path + mtime + size)
            for file_path in md_files:
                try:
                    stat = file_path.stat()
                    rel_path = str(file_path.relative_to(self.DOCS_ROOT))
                    hash_data = f"{rel_path}:{stat.st_mtime}:{stat.st_size}\n"
                    hasher.update(hash_data.encode("utf-8"))
                except (OSError, ValueError):
                    continue

            return hasher.hexdigest()

        except Exception as e:
            logger.warning(f"Error calculating docs hash: {e}")
            return ""

    def _load_cache_hash(self) -> str | None:
        """Load the cached docs hash from metadata file."""
        metadata_path = self.CACHE_ROOT / "cache_metadata.json"
        try:
            if metadata_path.exists():
                with open(metadata_path, encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("docs_hash")
        except Exception as e:
            logger.debug(f"Could not load cache metadata: {e}")
        return None

    def _save_cache_hash(self, docs_hash: str) -> None:
        """Save the docs hash to metadata file."""
        metadata_path = self.CACHE_ROOT / "cache_metadata.json"
        try:
            self.CACHE_ROOT.mkdir(parents=True, exist_ok=True)
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump({"docs_hash": docs_hash, "docs_root": str(self.DOCS_ROOT.absolute())}, f)
        except Exception as e:
            logger.warning(f"Could not save cache metadata: {e}")

    def _init_directories(self):
        """
        Initialize directories and invalidate cache only when docs change.

        Uses hash-based validation:
        - Calculate SHA256 hash of all .md files (paths + mtimes + sizes)
        - Compare with stored hash from previous run
        - If match: keep all caches (fast startup)
        - If mismatch: clear html/llms caches (docs changed)
        - DEBUG mode: always clear caches for fresh data
        """
        try:
            # Ensure DOCS_ROOT exists
            self.DOCS_ROOT.mkdir(parents=True, exist_ok=True)

            # Ensure cache directory exists
            self.CACHE_ROOT.mkdir(parents=True, exist_ok=True)

            # Calculate current docs hash
            current_hash = self._calculate_docs_hash()
            cached_hash = self._load_cache_hash()

            # Determine if cache should be invalidated
            should_invalidate = False

            if self.DEBUG:
                # DEBUG mode: always invalidate for fresh data
                should_invalidate = True
                logger.debug("DEBUG mode: invalidating cache")
            elif cached_hash is None:
                # No cached hash: first run or cache was manually cleared
                should_invalidate = True
                logger.debug("No cached hash found: invalidating cache")
            elif cached_hash != current_hash:
                # Docs changed: invalidate cache
                should_invalidate = True
                logger.info("📝 Documentation changed: invalidating cache")
            else:
                # Hash matches: keep cache
                logger.debug("Documentation unchanged: keeping cache")

            if should_invalidate:
                # Clean html and llms cache subdirectories
                # MCP index has its own hash-based validation in the indexer
                cache_subdirs_to_clean = ["html", "llms"]
                for subdir in cache_subdirs_to_clean:
                    cache_subdir = self.CACHE_ROOT / subdir
                    if cache_subdir.exists():
                        shutil.rmtree(cache_subdir)
                        logger.debug(f"Cleaned cache: {subdir}/")

                # Save new hash
                self._save_cache_hash(current_hash)

            logger.info(f"📁 DOCS_ROOT: {self.DOCS_ROOT.absolute()}")
            logger.info(f"💾 CACHE_ROOT: {self.CACHE_ROOT.absolute()}")

        except (OSError, PermissionError) as e:
            logger.warning(f"Could not create directories: {e}")
            # In development, we might not have permissions to create /app directories


# Create singleton instance
settings = Settings()
