"""
MCP (Model Context Protocol) module for ServeMD.
Provides JSON-RPC 2.0 endpoint for LLM clients to interactively query documentation.

Features:
- Full-text search with Whoosh (fuzzy search, boolean operators)
- Page retrieval with section filtering
- Page listing with category filtering
- Rate limiting protection
"""

from .indexer import get_index_manager, reset_index_manager
from .search import SearchResult, search_docs
from .server import handle_request
from .tools import call_tool, get_tool_definitions

__all__ = [
    "handle_request",
    "get_index_manager",
    "reset_index_manager",
    "search_docs",
    "SearchResult",
    "call_tool",
    "get_tool_definitions",
]
