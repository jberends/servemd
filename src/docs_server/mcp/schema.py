"""
Whoosh schema definition for MCP search index.
This module defines the schema for full-text search of documentation.

Note: Index building implementation is in Phase 2 (indexer.py).
"""

from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import DATETIME, ID, NUMERIC, TEXT, Schema


def create_whoosh_schema() -> Schema:
    """
    Create the Whoosh schema for documentation indexing.

    Fields:
        path: Unique identifier for the document (file path)
        title: Document title with 2.0x boost for relevance
        content: Full document text for search (not stored to save space)
        content_stored: Full document text stored for snippet extraction
        headings: Section headings with 1.5x boost
        category: Category from sidebar structure
        modified: Last modification timestamp
        size: Document size in bytes

    Returns:
        Whoosh Schema object
    """
    analyzer = StemmingAnalyzer()

    return Schema(
        path=ID(unique=True, stored=True),
        title=TEXT(analyzer=analyzer, stored=True, field_boost=2.0),
        content=TEXT(analyzer=analyzer, stored=False),
        content_stored=TEXT(stored=True),
        headings=TEXT(analyzer=analyzer, stored=True, field_boost=1.5),
        category=ID(stored=True),
        modified=DATETIME(stored=True, sortable=True),
        size=NUMERIC(stored=True),
    )


# Schema version for cache invalidation
SCHEMA_VERSION = "1.0"
