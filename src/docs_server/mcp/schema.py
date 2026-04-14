"""
Whoosh schema definition for MCP search index.
This module defines the schema for full-text search of documentation.

Note: Index building implementation is in Phase 2 (indexer.py).
"""

from whoosh.analysis import LowercaseFilter, RegexTokenizer, StemFilter, StopFilter
from whoosh.fields import DATETIME, ID, NUMERIC, STORED, TEXT, Schema

# Whitespace-only tokenizer: preserves hyphenated identifiers like UC-2-002
# as a single token so they can be matched exactly.
_identifier_analyzer = RegexTokenizer(r"\S+") | LowercaseFilter()

# Prose analyzer with two improvements over the default StemmingAnalyzer:
#   1. Extended tokenizer emits hyphenated tokens (e.g. UC-2-002) as a single
#      token in addition to the usual word tokens, so prose fields can still
#      match identifiers that appear inline in body text.
#   2. StopFilter minsize=1 keeps single-character tokens (e.g. the "2" in
#      UC-2-002) so that identifiers like UC-3-002 and UC-4-002 remain
#      distinguishable after tokenisation.
_prose_analyzer = RegexTokenizer(r"[\w][\w\-]*[\w]|[\w]+") | LowercaseFilter() | StopFilter(minsize=1) | StemFilter()


def create_whoosh_schema() -> Schema:
    """
    Create the Whoosh schema for documentation indexing.

    Fields:
        path: Unique identifier for the document (file path)
        title: Document title with 2.0x boost for relevance
        content: Full document text for search (not stored to save space)
        content_stored: Full document text stored for snippet extraction
        headings: Section headings h2-h4 with 1.5x boost
        identifiers: Structured identifiers extracted from headings (UC-2-002,
                     AUTH-01, G-02 …) preserved verbatim with 5.0x boost
        path_text: Tokenised file path for filename-fragment searches
        category: Category from sidebar structure
        modified: Last modification timestamp
        size: Document size in bytes

    Returns:
        Whoosh Schema object
    """
    # Simple word tokenizer for path fragments (splits on /, _, -, .)
    _path_analyzer = RegexTokenizer(r"\w+") | LowercaseFilter()

    return Schema(
        path=ID(unique=True, stored=True),
        title=TEXT(analyzer=_prose_analyzer, stored=True, field_boost=2.0),
        content=TEXT(analyzer=_prose_analyzer, stored=False),
        content_stored=TEXT(stored=True),
        headings=TEXT(analyzer=_prose_analyzer, stored=True, field_boost=1.5),
        identifiers=TEXT(analyzer=_identifier_analyzer, stored=True, field_boost=5.0),
        path_text=TEXT(analyzer=_path_analyzer, stored=False),
        identifier_anchors=STORED(),
        category=ID(stored=True),
        modified=DATETIME(stored=True, sortable=True),
        size=NUMERIC(stored=True),
    )


# Schema version for cache invalidation — bump whenever field definitions change.
SCHEMA_VERSION = "3.1"
