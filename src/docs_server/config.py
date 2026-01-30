"""
Configuration module for ServeMD Documentation Server.
Centralizes all environment variables and settings.
"""

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

    def _init_directories(self):
        """Initialize and clean directories on startup."""
        try:
            # Ensure DOCS_ROOT exists
            self.DOCS_ROOT.mkdir(parents=True, exist_ok=True)

            # Clean cache directory on startup
            if self.CACHE_ROOT.exists():
                shutil.rmtree(self.CACHE_ROOT)
                logger.info(f"🧹 Cleaned cache directory: {self.CACHE_ROOT.absolute()}")

            # Create fresh cache directory
            self.CACHE_ROOT.mkdir(parents=True, exist_ok=True)

            logger.info(f"📁 DOCS_ROOT: {self.DOCS_ROOT.absolute()}")
            logger.info(f"💾 CACHE_ROOT: {self.CACHE_ROOT.absolute()}")

        except (OSError, PermissionError) as e:
            logger.warning(f"Could not create directories: {e}")
            # In development, we might not have permissions to create /app directories


# Create singleton instance
settings = Settings()
