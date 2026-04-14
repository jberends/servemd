# Search Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three search-related issues: (1) HTML files not displaying in iframe, (2) missing direct links to heading anchors in search results, and (3) add highlight-on-page functionality for search terms.

**Architecture:** Enhance the HTML embed route to properly serve raw HTML files, extend the search result data structure to include heading anchors, and add client-side JavaScript to highlight search terms on the destination page using URL fragment parameters.

**Tech Stack:** Python/FastAPI (backend), JavaScript (client-side highlighting), Whoosh search indexing

---

## Problem Analysis

### Problem 1: HTML files not displaying
The `/raw/{path}` endpoint exists but the iframe embed is not working. The `_serve_html_in_iframe` function creates an iframe pointing to `/raw/{path}`, but there may be an issue with how raw HTML is served or how the iframe is configured.

### Problem 2: Missing direct links to heading anchors
When searching for "UC-2-002", the search results show the page but don't link directly to the `#uc-2-002` heading anchor. The search index extracts identifiers from headings, but the search result structure doesn't capture which heading matched or what its anchor ID is.

### Problem 3: No highlight-on-page for search terms
After clicking a search result, the destination page should highlight the search term (like browser Cmd-F/Ctrl-F). This requires passing the search query to the destination page and adding client-side JavaScript to highlight matching text.

---

## File Structure

**Files to modify:**
- `src/docs_server/main.py` - Fix raw HTML serving, add query parameter support for highlighting
- `src/docs_server/mcp/search.py` - Extend SearchResult to include anchor information
- `src/docs_server/mcp/indexer.py` - Track heading-to-anchor mapping during indexing
- `src/docs_server/helpers.py` - Update search result formatting to include anchor links
- `src/docs_server/templates.py` - Add client-side highlighting JavaScript

**Files to create:**
- `tests/test_html_embed_fix.py` - Tests for raw HTML serving
- `tests/test_search_anchors.py` - Tests for anchor link generation
- `tests/test_search_highlighting.py` - Tests for highlight functionality

---

## Task 1: Fix HTML File Display in Iframe

**Files:**
- Modify: `src/docs_server/main.py:559-586`
- Test: `tests/test_html_embed_fix.py`

- [ ] **Step 1: Write failing test for raw HTML serving**

Create test file that verifies raw HTML files are served correctly:

```python
"""Tests for raw HTML file serving in iframe embeds."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path


def test_raw_html_file_served_correctly(client: TestClient, tmp_docs_root: Path):
    """Test that raw HTML files are served with correct content-type and content."""
    # Create a test HTML file
    html_content = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body><h1>Test Content</h1><p>This is a test.</p></body>
</html>"""
    html_file = tmp_docs_root / "test_page.html"
    html_file.write_text(html_content, encoding="utf-8")
    
    # Request the raw HTML file
    response = client.get("/raw/test_page.html")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html"
    assert "Test Content" in response.text
    assert "<!DOCTYPE html>" in response.text


def test_raw_html_in_nested_directory(client: TestClient, tmp_docs_root: Path):
    """Test that raw HTML files in subdirectories are served correctly."""
    subdir = tmp_docs_root / "specs"
    subdir.mkdir()
    
    html_content = """<!DOCTYPE html>
<html><body><h1>Nested HTML</h1></body></html>"""
    html_file = subdir / "nested.html"
    html_file.write_text(html_content, encoding="utf-8")
    
    response = client.get("/raw/specs/nested.html")
    
    assert response.status_code == 200
    assert "Nested HTML" in response.text


def test_html_embed_iframe_points_to_raw_endpoint(client: TestClient, tmp_docs_root: Path):
    """Test that HTML embed creates iframe pointing to /raw/ endpoint."""
    html_content = """<!DOCTYPE html>
<html><body><h1>Embedded Page</h1></body></html>"""
    html_file = tmp_docs_root / "embed_test.html"
    html_file.write_text(html_content, encoding="utf-8")
    
    # Request the HTML page (should get iframe wrapper)
    response = client.get("/embed_test.html")
    
    assert response.status_code == 200
    assert '<iframe src="/raw/embed_test.html"' in response.text
    assert 'class="html-embed-frame"' in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_html_embed_fix.py -v`
Expected: FAIL with "test file not found" or similar

- [ ] **Step 3: Inspect current raw HTML serving implementation**

Check the `/raw/{path:path}` endpoint in `main.py` to understand current behavior:

```python
# In main.py around line 559-586
@app.get("/raw/{path:path}")
async def serve_raw_file(path: str):
    """
    Serve a file from DOCS_ROOT as-is, without template wrapping.
    Used by the iframe embed for HTML files to avoid recursive template rendering.
    """
    file_path = get_file_path(path)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    suffix = file_path.suffix.lower()
    media_types = {
        ".html": "text/html",
        ".htm": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    safe_log_path = path.replace("\r", "").replace("\n", "")
    logger.debug(f"Serving raw file: {safe_log_path} ({media_type})")
    return FileResponse(path=str(file_path), media_type=media_type)
```

- [ ] **Step 4: Add charset to HTML media type**

The issue might be missing charset specification. Update the media type for HTML:

```python
# In main.py:559-586, modify the serve_raw_file function
@app.get("/raw/{path:path}")
async def serve_raw_file(path: str):
    """
    Serve a file from DOCS_ROOT as-is, without template wrapping.
    Used by the iframe embed for HTML files to avoid recursive template rendering.
    """
    file_path = get_file_path(path)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    suffix = file_path.suffix.lower()
    media_types = {
        ".html": "text/html; charset=utf-8",
        ".htm": "text/html; charset=utf-8",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    safe_log_path = path.replace("\r", "").replace("\n", "")
    logger.debug(f"Serving raw file: {safe_log_path} ({media_type})")
    return FileResponse(path=str(file_path), media_type=media_type)
```

- [ ] **Step 5: Add X-Frame-Options header to allow iframe embedding**

HTML files might be blocked by X-Frame-Options. Add header to allow same-origin embedding:

```python
# In main.py:559-586, modify the serve_raw_file function
@app.get("/raw/{path:path}")
async def serve_raw_file(path: str):
    """
    Serve a file from DOCS_ROOT as-is, without template wrapping.
    Used by the iframe embed for HTML files to avoid recursive template rendering.
    """
    file_path = get_file_path(path)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    suffix = file_path.suffix.lower()
    media_types = {
        ".html": "text/html; charset=utf-8",
        ".htm": "text/html; charset=utf-8",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    # Add headers to allow iframe embedding for HTML files
    headers = {}
    if suffix in (".html", ".htm"):
        headers["X-Frame-Options"] = "SAMEORIGIN"

    safe_log_path = path.replace("\r", "").replace("\n", "")
    logger.debug(f"Serving raw file: {safe_log_path} ({media_type})")
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers=headers
    )
```

- [ ] **Step 6: Run tests to verify fix**

Run: `uv run pytest tests/test_html_embed_fix.py -v`
Expected: PASS

- [ ] **Step 7: Test manually with actual HTML file**

Create a test HTML file in your docs directory and verify it displays in the iframe:

```bash
echo '<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Test HTML</h1><p>If you see this, iframe embedding works!</p></body></html>' > /path/to/docs/test_embed.html
```

Visit: `http://localhost:8080/test_embed.html`

- [ ] **Step 8: Commit**

```bash
git add src/docs_server/main.py tests/test_html_embed_fix.py
git commit -m "fix: add charset and X-Frame-Options for HTML iframe embedding

- Add charset=utf-8 to HTML media type in /raw/ endpoint
- Add X-Frame-Options: SAMEORIGIN header for HTML files
- Add tests for raw HTML serving and iframe embedding
- Fixes issue where HTML files were not displaying in iframe"
```

---

## Task 2: Add Direct Links to Heading Anchors in Search Results

**Files:**
- Modify: `src/docs_server/mcp/indexer.py:366-432`
- Modify: `src/docs_server/mcp/search.py:54-63,157-196`
- Modify: `src/docs_server/helpers.py:51-99`
- Test: `tests/test_search_anchors.py`

- [ ] **Step 1: Write failing test for anchor link generation**

Create test that verifies search results include anchor links when identifiers match headings:

```python
"""Tests for search result anchor link generation."""

import pytest
from pathlib import Path
from docs_server.mcp.search import search_docs
from docs_server.mcp.indexer import get_index_manager


@pytest.mark.asyncio
async def test_search_result_includes_anchor_for_identifier_match(tmp_docs_root: Path):
    """Test that searching for an identifier returns result with anchor link."""
    # Create a markdown file with an identifier in a heading
    content = """# Use Cases

## UC-2-002 Manage Template Versions

This use case describes how to manage template versions.

### Details

More information about UC-2-002.
"""
    md_file = tmp_docs_root / "use_cases.md"
    md_file.write_text(content, encoding="utf-8")
    
    # Initialize index
    manager = get_index_manager()
    await manager.initialize(force_rebuild=True)
    
    # Search for the identifier
    results = search_docs("UC-2-002")
    
    assert len(results) > 0
    result = results[0]
    assert result.path == "use_cases.md"
    assert result.anchor == "uc-2-002-manage-template-versions"
    assert result.url == "/use_cases.html#uc-2-002-manage-template-versions"


@pytest.mark.asyncio
async def test_search_result_without_anchor_for_content_match(tmp_docs_root: Path):
    """Test that content matches don't include anchor (only identifier matches do)."""
    content = """# Documentation

This page mentions UC-2-002 in the body text.
"""
    md_file = tmp_docs_root / "docs.md"
    md_file.write_text(content, encoding="utf-8")
    
    manager = get_index_manager()
    await manager.initialize(force_rebuild=True)
    
    results = search_docs("UC-2-002")
    
    assert len(results) > 0
    result = results[0]
    # Content match should not have anchor
    assert result.anchor == ""
    assert result.url == "/docs.html"


@pytest.mark.asyncio
async def test_multiple_identifiers_in_same_document(tmp_docs_root: Path):
    """Test that searching returns the correct anchor when multiple identifiers exist."""
    content = """# Use Cases

## UC-2-001 First Use Case

Details about UC-2-001.

## UC-2-002 Second Use Case

Details about UC-2-002.

## UC-2-003 Third Use Case

Details about UC-2-003.
"""
    md_file = tmp_docs_root / "use_cases.md"
    md_file.write_text(content, encoding="utf-8")
    
    manager = get_index_manager()
    await manager.initialize(force_rebuild=True)
    
    results = search_docs("UC-2-002")
    
    assert len(results) > 0
    result = results[0]
    assert result.anchor == "uc-2-002-second-use-case"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_search_anchors.py -v`
Expected: FAIL with "SearchResult has no attribute 'anchor'"

- [ ] **Step 3: Extend SearchResult dataclass with anchor and url fields**

```python
# In src/docs_server/mcp/search.py:54-63
@dataclass
class SearchResult:
    """Represents a single search result."""

    path: str
    title: str
    snippet: str
    score: float
    category: str = ""
    anchor: str = ""  # Heading anchor ID if identifier matched in heading
    url: str = ""  # Full URL with anchor (e.g. /page.html#heading-id)
```

- [ ] **Step 4: Create heading-to-anchor mapping during indexing**

Add a function to generate anchor IDs from heading text (matching the markdown renderer's behavior):

```python
# In src/docs_server/mcp/indexer.py, add after extract_identifiers function (around line 432)

def generate_anchor_id(heading_text: str) -> str:
    """
    Generate an anchor ID from heading text, matching markdown renderer behavior.
    
    Converts heading text to lowercase, replaces spaces with hyphens,
    removes special characters except hyphens and alphanumerics.
    
    Args:
        heading_text: The heading text (e.g. "UC-2-002 Manage Template Versions")
    
    Returns:
        Anchor ID (e.g. "uc-2-002-manage-template-versions")
    """
    # Convert to lowercase
    anchor = heading_text.lower()
    # Replace spaces with hyphens
    anchor = anchor.replace(" ", "-")
    # Remove special characters except hyphens and alphanumerics
    anchor = re.sub(r"[^a-z0-9\-]", "", anchor)
    # Collapse multiple hyphens
    anchor = re.sub(r"-+", "-", anchor)
    # Strip leading/trailing hyphens
    anchor = anchor.strip("-")
    return anchor


def extract_identifier_to_anchor_map(content: str) -> dict[str, str]:
    """
    Extract mapping of identifiers to their heading anchor IDs.
    
    For each heading line containing an identifier, maps the identifier
    (lowercase) to the anchor ID generated from that heading.
    
    Args:
        content: Raw markdown content
    
    Returns:
        Dict mapping identifier (lowercase) to anchor ID
    """
    try:
        mapping: dict[str, str] = {}
        for line in content.splitlines():
            if line.startswith("#"):
                # Extract heading text (remove leading # symbols and whitespace)
                heading_text = re.sub(r"^#+\s*", "", line).strip()
                # Generate anchor ID for this heading
                anchor_id = generate_anchor_id(heading_text)
                # Find all identifiers in this heading
                for match in _IDENTIFIER_RE.finditer(line):
                    identifier = match.group(0).lower()
                    # Map identifier to this heading's anchor
                    mapping[identifier] = anchor_id
        return mapping
    except Exception as e:
        logger.warning(f"Error extracting identifier-to-anchor map: {e}")
        return {}
```

- [ ] **Step 5: Store identifier-to-anchor mapping in DocumentInfo**

```python
# In src/docs_server/mcp/indexer.py:49-61, add field to DocumentInfo
@dataclass
class DocumentInfo:
    """Represents a document to be indexed."""

    path: str
    title: str
    content: str
    headings: list[str] = field(default_factory=list)
    identifiers: list[str] = field(default_factory=list)
    identifier_anchors: dict[str, str] = field(default_factory=dict)  # Maps identifier to anchor ID
    category: str = ""
    modified: datetime = field(default_factory=lambda: datetime.now(UTC))
    size: int = 0
```

- [ ] **Step 6: Update document parsing to extract identifier-anchor mapping**

```python
# In src/docs_server/mcp/indexer.py:764-793, modify _parse_document
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
            identifiers=extract_identifiers(content),
            identifier_anchors=extract_identifier_to_anchor_map(content),
            category=extract_category(file_path, self._docs_root),
            modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            size=stat.st_size,
        )

    except Exception as e:
        logger.warning(f"Error parsing document {file_path}: {e}")
        return None
```

- [ ] **Step 7: Store identifier-anchor mapping in Whoosh index**

Update the schema to include identifier_anchors field:

```python
# In src/docs_server/mcp/schema.py, add field to schema
from whoosh.fields import STORED

# In create_whoosh_schema function, add:
identifier_anchors=STORED,  # JSON-serialized dict of identifier -> anchor_id
```

Update the indexer to serialize and store the mapping:

```python
# In src/docs_server/mcp/indexer.py:273-296, modify add_document
def add_document(self, doc: DocumentInfo) -> bool:
    """Add a document to the index."""
    try:
        if self._writer is None:
            logger.error("Cannot add document: writer not initialized")
            return False

        import json
        
        self._writer.add_document(
            path=doc.path,
            title=doc.title,
            content=doc.content,
            content_stored=doc.content,
            headings=" ".join(doc.headings),
            identifiers=" ".join(doc.identifiers),
            identifier_anchors=json.dumps(doc.identifier_anchors),
            path_text=doc.path,
            category=doc.category,
            modified=doc.modified,
            size=doc.size,
        )
        return True

    except Exception as e:
        logger.error(f"Failed to add document {doc.path}: {e}", exc_info=True)
        return False
```

- [ ] **Step 8: Extract anchor from search hit when identifier matches**

```python
# In src/docs_server/mcp/search.py:157-196, modify _extract_snippet
def _extract_snippet(hit, query: str) -> tuple[str, str]:
    """
    Extract a relevant snippet from the search hit with highlighting,
    and determine the anchor ID if the query matched an identifier.

    Args:
        hit: Whoosh search hit object
        query: Original search query for highlighting

    Returns:
        Tuple of (snippet, anchor_id)
    """
    import json
    
    anchor_id = ""
    
    # Check if query matched an identifier field
    # If so, look up the anchor from the stored mapping
    try:
        identifier_anchors_json = hit.get("identifier_anchors", "{}")
        identifier_anchors = json.loads(identifier_anchors_json)
        
        # Normalize query to lowercase for lookup
        query_lower = query.strip().lower()
        
        # Check if this query is an identifier with a known anchor
        if query_lower in identifier_anchors:
            anchor_id = identifier_anchors[query_lower]
    except Exception as e:
        logger.warning(f"Error extracting anchor from hit: {e}")
    
    try:
        # Try to get highlighted snippet from content_stored field
        snippet = hit.highlights("content_stored", top=1)

        if snippet:
            # Clean up and return the snippet
            return (_clean_snippet(snippet), anchor_id)

        # Fall back to headings if no content match
        snippet = hit.highlights("headings", top=1)
        if snippet:
            return (_clean_snippet(snippet), anchor_id)

        # Last resort: return beginning of stored content
        content = hit.get("content_stored", "")
        if content:
            # Return first N characters
            max_len = settings.MCP_SNIPPET_LENGTH
            if len(content) > max_len:
                # Try to break at word boundary
                content = content[:max_len].rsplit(" ", 1)[0] + "..."
            return (content, anchor_id)

        return (hit.get("title", "No content available"), anchor_id)

    except Exception as e:
        logger.warning(f"Error extracting snippet: {e}")
        return (hit.get("title", "No snippet available"), anchor_id)
```

- [ ] **Step 9: Update search_docs to populate anchor and url fields**

```python
# In src/docs_server/mcp/search.py:65-155, modify search_docs
def search_docs(query: str, limit: int | None = None) -> list[SearchResult]:
    """
    Search documentation using Whoosh full-text search.

    Features:
    - Multi-field search (title, content, headings)
    - Fuzzy search support for typo tolerance (use ~ suffix)
    - Boolean operators (AND, OR, NOT)
    - Field-specific queries (title:xxx, content:xxx)
    - BM25 scoring with title/headings boosting
    - Direct anchor links for identifier matches

    Args:
        query: Search query string. Supports:
            - Simple terms: "authentication"
            - Fuzzy terms: "authentiction~" (typo tolerance)
            - Boolean: "auth AND login"
            - Field-specific: "title:configuration"
            - Phrases: '"rate limiting"'
        limit: Maximum number of results (default: MCP_MAX_SEARCH_RESULTS)

    Returns:
        List of SearchResult objects, sorted by relevance score

    Raises:
        RuntimeError: If search index is not initialized
    """
    from ..helpers import path_to_doc_url
    
    if limit is None:
        limit = settings.MCP_MAX_SEARCH_RESULTS

    manager = get_index_manager()

    if not manager.is_initialized:
        logger.error("Search index not initialized")
        raise RuntimeError("Search index not initialized")

    whoosh_index = manager.get_whoosh_index()
    if whoosh_index is None:
        logger.error("Whoosh index not available")
        raise RuntimeError("Search index not available")

    results: list[SearchResult] = []

    try:
        # Create parser for multi-field search.
        # identifiers field (5x boost) catches exact UC/AUTH/G- lookups first;
        # title (2x), headings (1.5x), content (1x) handle prose searches.
        parser = MultifieldParser(
            ["identifiers", "title", "headings", "content", "path_text"],
            schema=whoosh_index.schema,
            fieldboosts={"identifiers": 5.0, "title": 2.0, "headings": 1.5},
        )

        # Add fuzzy search support for typo tolerance
        parser.add_plugin(FuzzyTermPlugin())

        # Parse the query
        parsed_query = parser.parse(query)
        logger.debug(f"Parsed search query: {parsed_query}")

        with whoosh_index.searcher() as searcher:
            # Execute search
            hits = searcher.search(parsed_query, limit=limit)

            for hit in hits:
                # Extract snippet and anchor
                snippet, anchor_id = _extract_snippet(hit, query)
                
                # Build URL with anchor if available
                doc_url = path_to_doc_url(hit["path"])
                if anchor_id:
                    full_url = f"{doc_url}#{anchor_id}"
                else:
                    full_url = doc_url

                results.append(
                    SearchResult(
                        path=hit["path"],
                        title=hit["title"],
                        snippet=snippet,
                        score=hit.score,
                        category=hit.get("category", ""),
                        anchor=anchor_id,
                        url=full_url,
                    )
                )

        logger.info(f"Search '{_sanitize_for_log(query)}' returned {len(results)} results")
        return results

    except Exception as e:
        safe_query = _sanitize_for_log(query)
        safe_error = _sanitize_for_log(str(e))
        logger.error(
            "Search error for query '%s': %s",
            safe_query,
            safe_error,
            exc_info=True,
        )
        raise RuntimeError(f"Search failed: {e}") from e
```

- [ ] **Step 10: Update HTML search result formatting to use anchor URLs**

```python
# In src/docs_server/helpers.py:51-99, modify format_search_results_human
def format_search_results_human(results: list[Any], query: str = "") -> str:
    """
    Format search results as human-readable HTML cards.

    Each result is rendered as a card with title (linked), path breadcrumb,
    snippet, and score badge. The output is a self-contained HTML fragment
    suitable for injection into the search page results div.

    Args:
        results: List of SearchResult objects (path, title, snippet, score, category, anchor, url).
        query: The original search query (used for highlighting).

    Returns:
        HTML string with result cards, or a "no results" message.
    """
    from html import escape as html_escape

    if not results:
        safe_q = html_escape(query) if query else ""
        if safe_q:
            return f"<p class='search-no-results'>No results found for &lsquo;{safe_q}&rsquo;</p>"
        return "<p class='search-no-results'>Enter a search term to find documentation.</p>"

    count = len(results)
    parts: list[str] = [f"<p class='search-result-count'>Found {count} result{'s' if count != 1 else ''}:</p>"]

    for result in results:
        # Use the full URL with anchor if available
        url = result.url if hasattr(result, 'url') and result.url else path_to_doc_url(result.path)
        safe_title = html_escape(result.title)
        safe_path = html_escape(result.path)
        # Strip Whoosh HTML, escape, then we apply our own highlight
        plain_snippet = _strip_whoosh_highlight_html(result.snippet) if result.snippet else ""
        safe_snippet = html_escape(plain_snippet) if plain_snippet else ""
        safe_category = html_escape(result.category) if result.category else ""

        card = "<div class='search-result-card'>"
        card += f"<a href='{url}' class='search-result-title'>{safe_title}</a>"
        if safe_category:
            card += f"<span class='search-result-category'>{safe_category}</span>"
        card += f"<span class='search-result-path'>{safe_path}</span>"
        if safe_snippet:
            card += f"<p class='search-result-snippet'>{safe_snippet}</p>"
        card += "</div>"
        parts.append(card)

    html_out = "\n".join(parts)
    if query:
        html_out = highlight_search_terms(html_out, query)
    return html_out
```

- [ ] **Step 11: Update JSON search response to include anchor and url**

```python
# In src/docs_server/main.py:368-443, modify _search_json_response
async def _search_json_response(query: str) -> JSONResponse:
    """Return search results as JSON with a pre-rendered HTML fragment."""
    if not query:
        return JSONResponse(content={"query": "", "count": 0, "results": [], "html": ""})

    # Check availability
    if not settings.MCP_ENABLED:
        return JSONResponse(
            content={
                "query": query,
                "count": 0,
                "results": [],
                "html": "<p class='search-no-results'>Search is not available.</p>",
            }
        )

    try:
        from .mcp import get_index_manager

        manager = get_index_manager()
        if not manager.is_initialized:
            return JSONResponse(
                content={
                    "query": query,
                    "count": 0,
                    "results": [],
                    "html": "<p class='search-no-results'>Search will be available once the index is built.</p>",
                }
            )
    except Exception as e:
        logger.warning(f"Search index check failed: {e}")
        return JSONResponse(
            content={
                "query": query,
                "count": 0,
                "results": [],
                "html": "<p class='search-no-results'>Search will be available once the index is built.</p>",
            }
        )

    try:
        from .mcp import search_docs

        results = search_docs(query=query)
    except RuntimeError as e:
        logger.warning(f"Search failed: {e}")
        return JSONResponse(
            content={
                "query": query,
                "count": 0,
                "results": [],
                "html": "<p class='search-no-results'>Search will be available once the index is built.</p>",
            }
        )

    # Build JSON payload with pre-rendered HTML fragment
    results_html = format_search_results_human(results, query)
    results_data = [
        {
            "title": r.title,
            "path": r.path,
            "url": r.url if hasattr(r, 'url') and r.url else path_to_doc_url(r.path),
            "snippet": r.snippet,
            "score": round(r.score, 2),
            "category": r.category,
            "anchor": r.anchor if hasattr(r, 'anchor') else "",
        }
        for r in results
    ]
    return JSONResponse(
        content={
            "query": query,
            "count": len(results),
            "results": results_data,
            "html": results_html,
        }
    )
```

- [ ] **Step 12: Run tests to verify anchor link generation**

Run: `uv run pytest tests/test_search_anchors.py -v`
Expected: PASS

- [ ] **Step 13: Run all search tests to ensure no regressions**

Run: `uv run pytest tests/test_search*.py tests/test_mcp*.py -v`
Expected: All PASS

- [ ] **Step 14: Commit**

```bash
git add src/docs_server/mcp/indexer.py src/docs_server/mcp/search.py src/docs_server/mcp/schema.py src/docs_server/helpers.py src/docs_server/main.py tests/test_search_anchors.py
git commit -m "feat: add direct anchor links to search results for identifier matches

- Extend SearchResult with anchor and url fields
- Extract identifier-to-anchor mapping during indexing
- Store mapping in Whoosh index as JSON field
- Populate anchor links when search query matches identifier
- Update search result HTML and JSON to use anchor URLs
- Add tests for anchor link generation
- Fixes issue where searching for UC-2-002 didn't link directly to heading"
```

---

## Task 3: Add Highlight-on-Page for Search Terms

**Files:**
- Modify: `src/docs_server/templates.py:1984-2039`
- Modify: `src/docs_server/helpers.py:51-99`
- Test: `tests/test_search_highlighting.py`

- [ ] **Step 1: Write failing test for highlight functionality**

Create test that verifies search terms are highlighted on the destination page:

```python
"""Tests for search term highlighting on destination pages."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path


def test_search_result_link_includes_highlight_param(client: TestClient, tmp_docs_root: Path):
    """Test that search result links include highlight query parameter."""
    content = """# Documentation

This page contains information about authentication and authorization.
"""
    md_file = tmp_docs_root / "docs.md"
    md_file.write_text(content, encoding="utf-8")
    
    # Perform search
    response = client.get("/search?q=authentication&format=json")
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] > 0
    
    # Check that URL includes highlight parameter
    result_url = data["results"][0]["url"]
    assert "highlight=" in result_url or "#" in result_url


def test_page_includes_highlight_script_when_param_present(client: TestClient, tmp_docs_root: Path):
    """Test that pages include highlighting JavaScript when highlight param is present."""
    content = """# Test Page

This page contains the word authentication multiple times.
Authentication is important for security.
"""
    md_file = tmp_docs_root / "test.md"
    md_file.write_text(content, encoding="utf-8")
    
    # Request page with highlight parameter
    response = client.get("/test.html?highlight=authentication")
    assert response.status_code == 200
    
    # Check for highlight script
    assert "highlightSearchTerms" in response.text
    assert "search-highlight" in response.text


def test_highlight_script_highlights_multiple_occurrences(client: TestClient, tmp_docs_root: Path):
    """Test that highlight script wraps all occurrences of search term."""
    content = """# Test Page

The word test appears multiple times.
This is a test.
Another test here.
"""
    md_file = tmp_docs_root / "test.md"
    md_file.write_text(content, encoding="utf-8")
    
    response = client.get("/test.html?highlight=test")
    assert response.status_code == 200
    
    # The script should be present and configured with the search term
    assert "highlightSearchTerms" in response.text
    assert response.text.count("search-highlight") >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_search_highlighting.py -v`
Expected: FAIL with "highlight parameter not in URL" or "highlightSearchTerms not found"

- [ ] **Step 3: Update search result URLs to include highlight parameter**

```python
# In src/docs_server/helpers.py:51-99, modify format_search_results_human
def format_search_results_human(results: list[Any], query: str = "") -> str:
    """
    Format search results as human-readable HTML cards.

    Each result is rendered as a card with title (linked), path breadcrumb,
    snippet, and score badge. The output is a self-contained HTML fragment
    suitable for injection into the search page results div.

    Args:
        results: List of SearchResult objects (path, title, snippet, score, category, anchor, url).
        query: The original search query (used for highlighting).

    Returns:
        HTML string with result cards, or a "no results" message.
    """
    from html import escape as html_escape
    from urllib.parse import quote

    if not results:
        safe_q = html_escape(query) if query else ""
        if safe_q:
            return f"<p class='search-no-results'>No results found for &lsquo;{safe_q}&rsquo;</p>"
        return "<p class='search-no-results'>Enter a search term to find documentation.</p>"

    count = len(results)
    parts: list[str] = [f"<p class='search-result-count'>Found {count} result{'s' if count != 1 else ''}:</p>"]

    for result in results:
        # Use the full URL with anchor if available
        base_url = result.url if hasattr(result, 'url') and result.url else path_to_doc_url(result.path)
        
        # Add highlight parameter to URL
        if query:
            separator = "&" if "?" in base_url else "?"
            # If URL has anchor, insert highlight before the anchor
            if "#" in base_url:
                url_parts = base_url.split("#", 1)
                url = f"{url_parts[0]}?highlight={quote(query)}#{url_parts[1]}"
            else:
                url = f"{base_url}?highlight={quote(query)}"
        else:
            url = base_url
        
        safe_title = html_escape(result.title)
        safe_path = html_escape(result.path)
        # Strip Whoosh HTML, escape, then we apply our own highlight
        plain_snippet = _strip_whoosh_highlight_html(result.snippet) if result.snippet else ""
        safe_snippet = html_escape(plain_snippet) if plain_snippet else ""
        safe_category = html_escape(result.category) if result.category else ""

        card = "<div class='search-result-card'>"
        card += f"<a href='{url}' class='search-result-title'>{safe_title}</a>"
        if safe_category:
            card += f"<span class='search-result-category'>{safe_category}</span>"
        card += f"<span class='search-result-path'>{safe_path}</span>"
        if safe_snippet:
            card += f"<p class='search-result-snippet'>{safe_snippet}</p>"
        card += "</div>"
        parts.append(card)

    html_out = "\n".join(parts)
    if query:
        html_out = highlight_search_terms(html_out, query)
    return html_out
```

- [ ] **Step 4: Extract highlight parameter in serve_content route**

```python
# In src/docs_server/main.py:589-720, modify serve_content to accept highlight param
@app.get("/{path:path}")
async def serve_content(path: str, request: Request, highlight: str = ""):
    """
    Main content serving endpoint with dual routing:
    - .md files: serve raw markdown
    - .html files: serve rendered HTML with template
    - other files: serve as static assets
    
    Query parameters:
    - highlight: Search term to highlight on the page
    """
    if not path:
        return RedirectResponse(url="/index.html", status_code=302)

    # Handle .html requests (rendered markdown)
    if path.endswith(".html"):
        md_path = path[:-5] + ".md"  # Convert .html to .md
        file_path = get_file_path(md_path)

        if not file_path:
            # Fallback: check if a raw .html file exists in DOCS_ROOT
            html_file_path = get_file_path(path)
            if html_file_path:
                return _serve_html_in_iframe(path, html_file_path)
            raise HTTPException(status_code=404, detail="File not found")

        # Check cache first (skip cache if highlight param present for fresh render)
        if not highlight:
            cached_html = await get_cached_html(file_path)
            if cached_html:
                logger.debug(f"Serving cached HTML: {path}")
                return HTMLResponse(content=cached_html)

        # Read and render markdown
        try:
            markdown_content = file_path.read_text(encoding="utf-8")
            html_content = await render_markdown_to_html(markdown_content, file_path)

            # Parse navigation
            navigation = parse_sidebar_navigation()
            topbar_sections = parse_topbar_links()

            # Extract table of contents from the rendered HTML
            toc_items = extract_table_of_contents(html_content)

            # Create full HTML document with styling and navigation
            title = f"{file_path.stem.replace('_', ' ').title()} - Documentation"
            page_title = file_path.stem.replace("_", " ").title()
            # Root-relative path for active state (matches sidebar/topbar link format)
            current_path = f"/{path}" if path and not path.startswith("/") else path
            current_doc_path = path[:-5] if path.endswith(".html") else path  # e.g. features/mcp

            # Build page actions (Copy page dropdown with AI links)
            if settings.BASE_URL:
                base_url = settings.BASE_URL
            else:
                base_url = str(request.base_url).rstrip("/")
                # Respect X-Forwarded-Proto from reverse proxies that terminate SSL
                forwarded_proto = request.headers.get("x-forwarded-proto", "")
                if forwarded_proto == "https" and base_url.startswith("http://"):
                    base_url = "https://" + base_url[7:]
            raw_md_url = f"{base_url}/{current_doc_path}.md"
            page_url = f"{base_url}{current_path}" if current_path.startswith("/") else f"{base_url}/{current_path}"
            page_actions = {
                "raw_md_url": raw_md_url,
                "page_url": page_url,
                "page_title": page_title,
                "chatgpt_url": build_chatgpt_url(raw_md_url),
                "claude_url": build_claude_url(raw_md_url),
                "mistral_url": build_mistral_url(raw_md_url),
            }

            full_html = create_html_template(
                html_content,
                title,
                current_path,
                navigation,
                topbar_sections,
                toc_items,
                show_search=settings.MCP_ENABLED,
                show_branding=settings.SERVEMD_BRANDING_ENABLED,
                page_actions=page_actions,
                custom_css_url="/custom.css" if get_custom_css_path() else None,
                highlight_term=highlight,  # Pass highlight term to template
            )

            # Cache the rendered HTML only if no highlight param
            if not highlight:
                await save_cached_html(file_path, full_html)

            logger.info(f"Rendered: {path}" + (f" (highlight: {highlight})" if highlight else ""))
            return HTMLResponse(content=full_html)

        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}") from e

    # ... rest of the function unchanged
```

- [ ] **Step 5: Add highlight_term parameter to create_html_template**

```python
# In src/docs_server/templates.py:276-289, add highlight_term parameter
def create_html_template(
    content: str,
    title: str = "Documentation",
    current_path: str = "",
    navigation: list[dict[str, Any]] = None,
    topbar_sections: dict[str, list[dict[str, str]]] = None,
    toc_items: list[dict[str, str]] = None,
    show_search: bool = False,
    search_query: str = "",
    is_search_page: bool = False,
    show_branding: bool = True,
    page_actions: dict[str, str] | None = None,
    custom_css_url: str | None = None,
    highlight_term: str = "",
) -> str:
    """
    Create a complete HTML document with sidebar navigation and topbar.
    
    Args:
        ... (existing args)
        highlight_term: Search term to highlight on the page
    """
    # ... existing template code ...
```

- [ ] **Step 6: Add client-side highlighting JavaScript to template**

```python
# In src/docs_server/templates.py:1984-2039, add after existing scripts
    highlight_script = ""
    if highlight_term:
        safe_highlight_term = html.escape(highlight_term, quote=True)
        highlight_script = f"""<script>
(function() {{
    // Highlight search terms on page load
    var searchTerm = "{safe_highlight_term}";
    if (!searchTerm) return;
    
    function highlightSearchTerms(term) {{
        // Get the main content area
        var content = document.querySelector('.content');
        if (!content) return;
        
        // Create a case-insensitive regex pattern
        var pattern = new RegExp('(' + term.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');
        
        // Walk through text nodes and highlight matches
        var walker = document.createTreeWalker(
            content,
            NodeFilter.SHOW_TEXT,
            {{
                acceptNode: function(node) {{
                    // Skip script, style, and already-highlighted nodes
                    var parent = node.parentElement;
                    if (!parent) return NodeFilter.FILTER_REJECT;
                    var tagName = parent.tagName.toLowerCase();
                    if (tagName === 'script' || tagName === 'style' || tagName === 'mark') {{
                        return NodeFilter.FILTER_REJECT;
                    }}
                    // Only process nodes with matching text
                    if (pattern.test(node.textContent)) {{
                        return NodeFilter.FILTER_ACCEPT;
                    }}
                    return NodeFilter.FILTER_REJECT;
                }}
            }}
        );
        
        var nodesToReplace = [];
        var node;
        while (node = walker.nextNode()) {{
            nodesToReplace.push(node);
        }}
        
        nodesToReplace.forEach(function(textNode) {{
            var text = textNode.textContent;
            if (!pattern.test(text)) return;
            
            // Create a temporary container
            var temp = document.createElement('span');
            temp.innerHTML = text.replace(pattern, '<mark class="search-highlight">$1</mark>');
            
            // Replace the text node with highlighted content
            var parent = textNode.parentNode;
            while (temp.firstChild) {{
                parent.insertBefore(temp.firstChild, textNode);
            }}
            parent.removeChild(textNode);
        }});
        
        // Scroll to first highlight if no anchor present
        if (!window.location.hash) {{
            var firstHighlight = content.querySelector('.search-highlight');
            if (firstHighlight) {{
                firstHighlight.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
        }}
    }}
    
    // Run highlighting after page loads
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', function() {{
            highlightSearchTerms(searchTerm);
        }});
    }} else {{
        highlightSearchTerms(searchTerm);
    }}
}})();
</script>"""
```

- [ ] **Step 7: Inject highlight script into template**

```python
# In src/docs_server/templates.py:753-2042, modify the return statement
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <!-- ... rest of head ... -->
</head>
<body>
    {sidebar_html}
    {topbar_html}
    {mobile_menu_html}
    <div class="main-content">
        <div class="content">
            {final_content}
        </div>
        {toc_html}
    </div>
    {search_script}
    {search_page_script}
    {mobile_menu_script}
    {highlight_script}
    <script>
    (function() {{
        // ... existing scripts ...
    }})();
    </script>
</body>
</html>"""
```

- [ ] **Step 8: Run tests to verify highlighting works**

Run: `uv run pytest tests/test_search_highlighting.py -v`
Expected: PASS

- [ ] **Step 9: Test manually with browser**

1. Start the server: `DEBUG=true uv run python -m docs_server`
2. Search for a term: `http://localhost:8080/search?q=authentication`
3. Click a search result
4. Verify the search term is highlighted in yellow on the destination page
5. Verify the page scrolls to the first highlight (if no anchor)
6. Verify anchor navigation still works when present

- [ ] **Step 10: Run all tests to ensure no regressions**

Run: `uv run pytest tests/ -v`
Expected: All PASS

- [ ] **Step 11: Commit**

```bash
git add src/docs_server/main.py src/docs_server/helpers.py src/docs_server/templates.py tests/test_search_highlighting.py
git commit -m "feat: add highlight-on-page for search terms

- Add highlight query parameter to search result URLs
- Extract highlight parameter in serve_content route
- Add client-side JavaScript to highlight search terms on page
- Scroll to first highlight when no anchor present
- Skip caching when highlight parameter present
- Add tests for highlight functionality
- Fixes issue where search terms were not highlighted on destination page"
```

---

## Task 4: Update CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add entries to UNRELEASED section**

```markdown
# In CHANGELOG.md, add to UNRELEASED section at the top

## UNRELEASED

### Fixed
- HTML files now display correctly in iframe embeds with proper charset and X-Frame-Options headers
- Search results for identifiers (e.g. UC-2-002) now link directly to the heading anchor
- Search terms are now highlighted on destination pages (like browser Cmd-F/Ctrl-F)

### Added
- Direct anchor links in search results when searching for identifiers found in headings
- Client-side search term highlighting with automatic scroll to first match
- Identifier-to-anchor mapping stored in search index for precise navigation
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for search improvements"
```

---

## Verification

After completing all tasks, verify the fixes work end-to-end:

1. **HTML iframe display:**
   - Create an HTML file in your docs directory
   - Visit `/your-file.html` in browser
   - Verify it displays correctly in the iframe

2. **Direct anchor links:**
   - Search for an identifier like "UC-2-002"
   - Click the search result
   - Verify you land directly on the heading with that identifier

3. **Highlight-on-page:**
   - Search for any term
   - Click a search result
   - Verify the search term is highlighted in yellow on the page
   - Verify the page scrolls to the first highlight

4. **Combined functionality:**
   - Search for an identifier
   - Click the result
   - Verify you land on the correct heading AND the identifier is highlighted

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-14-search-improvements.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
