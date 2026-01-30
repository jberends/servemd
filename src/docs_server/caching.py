"""
Caching operations for ServeMD Documentation Server.
Handles HTML and llms.txt content caching.
"""

import logging
from pathlib import Path

from .config import settings

logger = logging.getLogger(__name__)


async def get_cached_html(file_path: Path) -> str | None:
    """
    Get cached HTML content if it exists.
    """
    try:
        # Create cache path
        relative_path = file_path.relative_to(settings.DOCS_ROOT)
        cache_path = settings.CACHE_ROOT / relative_path.with_suffix(".html")

        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as e:
        logger.debug(f"Cache read error: {e}")

    return None


async def save_cached_html(file_path: Path, html_content: str) -> None:
    """
    Save HTML content to cache.
    """
    try:
        # Create cache path
        relative_path = file_path.relative_to(settings.DOCS_ROOT)
        cache_path = settings.CACHE_ROOT / relative_path.with_suffix(".html")

        # Ensure cache directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        cache_path.write_text(html_content, encoding="utf-8")
        logger.debug(f"Cached HTML: {cache_path}")
    except (OSError, ValueError) as e:
        logger.debug(f"Cache write error: {e}")


async def get_cached_llms(cache_file: str) -> str | None:
    """
    Get cached llms content if it exists.
    Similar to get_cached_html() but for llms.txt files.
    """
    try:
        cache_path = settings.CACHE_ROOT / cache_file

        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as e:
        logger.debug(f"Cache read error for {cache_file}: {e}")

    return None


async def save_cached_llms(cache_file: str, content: str) -> None:
    """
    Save llms content to cache.
    Similar to save_cached_html() but for llms.txt files.
    """
    try:
        cache_path = settings.CACHE_ROOT / cache_file

        # Ensure cache directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        cache_path.write_text(content, encoding="utf-8")
        logger.debug(f"Cached llms file: {cache_path}")
    except (OSError, ValueError) as e:
        logger.debug(f"Cache write error for {cache_file}: {e}")
