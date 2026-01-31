# TODO: MCP Integration Implementation

**Ticket:** KLO-[TBD]  
**Feature:** Model Context Protocol (MCP) Support  
**Priority:** Medium  
**Estimated Effort:** 3-4 weeks (part-time) or 1.5-2 weeks (full-time)  
**Created:** 2026-01-31

---

## Overview

Add Model Context Protocol (MCP) support to ServeMD to enable LLMs to interactively query documentation through HTTP/JSON-RPC 2.0. MCP complements existing `llms.txt`/`llms-full.txt` endpoints by providing on-demand search instead of static dumps.

**Key Benefits:**
- 250x less context usage for typical queries (2KB vs 500KB)
- Interactive search and retrieval for LLM clients
- Scales to 1000+ documentation pages
- Self-contained (no external services)

**Design Constraints:**
- ✅ Immutable doc root (baked into Docker)
- ✅ Disk-based index cache (fast k8s pod startup)
- ✅ No external services (self-contained)
- ✅ HTTP/JSON-RPC transport (FastAPI-native)

---

## Implementation Approach

### Phase 1: Foundation & Infrastructure

**Goal:** Basic MCP endpoint with JSON-RPC 2.0 handling

- [x] Add dependencies to `pyproject.toml`:
  - [x] `whoosh>=2.7.4` for full-text search
  - [x] `slowapi>=0.1.9` for rate limiting
  - [x] Run `uv sync` to update lock file
- [x] Create MCP package structure:
  - [x] `src/docs_server/mcp/__init__.py`
  - [x] `src/docs_server/mcp/server.py` - JSON-RPC handler
  - [x] `src/docs_server/mcp/models.py` - Pydantic models
  - [x] `src/docs_server/mcp/schema.py` - Whoosh schema definition
- [x] Implement JSON-RPC 2.0 handler in `server.py`:
  - [x] `parse_request(body: dict)` - Validate JSON-RPC format
  - [x] `handle_request(request: dict)` - Route to method handlers
  - [x] `format_response(id, result)` - Format success responses
  - [x] `format_error(id, code, message, data)` - Format error responses
- [x] Add `/mcp` endpoint in `main.py`:
  - [x] POST route handler
  - [x] Parse JSON body
  - [x] Call `mcp.server.handle_request()`
  - [x] Return JSON response
- [x] Implement `initialize` method:
  - [x] Return `serverInfo` with name/version
  - [x] Declare `capabilities` with `tools` only (no resources)
  - [x] Handle protocol version negotiation
- [x] Add MCP configuration in `config.py`:
  - [x] `MCP_ENABLED: bool = True`
  - [x] `MCP_RATE_LIMIT_REQUESTS: int = 120`
  - [x] `MCP_RATE_LIMIT_WINDOW: int = 60`
  - [x] `MCP_MAX_SEARCH_RESULTS: int = 10`
  - [x] `MCP_SNIPPET_LENGTH: int = 200`
- [x] Write basic tests:
  - [x] `tests/test_mcp_server.py` - JSON-RPC parsing
  - [x] Test `initialize` method
  - [x] Test error handling (invalid JSON, missing fields)

**Deliverable:** `/mcp` endpoint responds to `initialize` requests

---

### Phase 2: Whoosh Index Building

**Goal:** Whoosh index builds on startup and caches to disk

- [x] Create `src/docs_server/mcp/schema.py`:
  - [x] Define Whoosh schema with fields:
    - [x] `path` (ID, unique, stored)
    - [x] `title` (TEXT, stored, boosted 2.0x)
    - [x] `content` (TEXT, not stored - save space)
    - [x] `content_stored` (TEXT, stored - for snippets)
    - [x] `headings` (TEXT, stored, boosted 1.5x)
    - [x] `category` (ID, stored)
    - [x] `modified` (DATETIME, stored, sortable)
    - [x] `size` (NUMERIC, stored)
  - [x] Use `StemmingAnalyzer()` for better word matching
- [x] Create `src/docs_server/mcp/indexer.py`:
  - [x] `build_search_index()` - Build Whoosh index
    - [x] Create index dir: `CACHE_ROOT/mcp/whoosh/`
    - [x] Create Whoosh index with schema
    - [x] Scan all `.md` files in `DOCS_ROOT`
    - [x] Skip special files (sidebar.md, topbar.md)
    - [x] Add each document to Whoosh index
    - [x] Commit index
  - [x] `calculate_docs_hash() -> str` - SHA256 of files + mtimes
  - [x] `save_cache_metadata(metadata: dict)` - Save to `metadata.json`
  - [x] `load_cache_metadata() -> dict | None` - Load metadata
  - [x] `validate_cache() -> bool` - Hash-based validation
    - [x] Check index exists
    - [x] Check metadata.json exists
    - [x] Compare docs_hash
    - [x] Check index_version
    - [x] Check DOCS_ROOT path
    - [x] Force rebuild in DEBUG mode
- [x] Implement markdown parsing helpers:
  - [x] `extract_title(content: str) -> str` - Get first # heading
  - [x] `extract_headings(content: str) -> list[str]` - All ## headings
  - [x] `extract_category(file_path: Path) -> str` - From path or sidebar
- [x] Add startup event in `main.py`:
  - [x] Lifespan context manager (modern FastAPI approach)
  - [x] Check `if settings.MCP_ENABLED`
  - [x] Call `await validate_cache()`
  - [x] If valid: `await load_index()` (10-20ms)
  - [x] If invalid: `await build_search_index()` (1-2s)
  - [x] Log timing and status
- [x] Store index reference globally:
  - [x] `_index_manager = None` in `indexer.py`
  - [x] `get_index_manager()` accessor function
- [x] Write tests:
  - [x] `tests/test_mcp_indexer.py` (47 tests)
  - [x] Test `build_search_index()` creates Whoosh files
  - [x] Test `calculate_docs_hash()` consistency
  - [x] Test `validate_cache()` scenarios
  - [x] Test `save/load_cache_metadata()`
  - [x] Test hash changes when files modified

**Additional Robustness Features Implemented:**
- [x] Abstract `SearchBackend` protocol for easy backend replacement
- [x] `WhooshSearchBackend` implementation with comprehensive error handling
- [x] `SearchIndexManager` class encapsulating all index lifecycle operations
- [x] `DocumentInfo` and `CacheMetadata` dataclasses for clean data handling
- [x] Graceful degradation - MCP failure doesn't crash the server
- [x] Full integration tests and error handling tests

**Deliverable:** Whoosh index builds on startup, loads from cache on restart (<20ms)

---

### Phase 3: Whoosh Search Implementation

**Goal:** `search_docs` tool with Whoosh full-text search

- [x] Create `src/docs_server/mcp/search.py`:
  - [x] `search_docs(query: str, limit: int) -> list[dict]` - Whoosh search
    - [x] Open Whoosh index with `get_search_index()`
    - [x] Create `MultifieldParser` for title, content, headings
    - [x] Add `FuzzyTermPlugin()` for typo tolerance
    - [x] Parse query string (handles operators, fuzzy, etc.)
    - [x] Search with Whoosh searcher
    - [x] Extract highlights/snippets with `result.highlights()`
    - [x] Format results (path, title, snippet, score)
    - [x] Return top N results
  - [x] Whoosh handles all scoring (BM25) and boosting (title 2x, headings 1.5x)
- [x] Create Pydantic model in `models.py`:
  - [x] `SearchDocsInput` with `query` (1-500 chars) and `limit` (1-50, default 10)
- [x] Implement `tools/list` method in `server.py`:
  - [x] Return list of available tools with descriptions
  - [x] Auto-generate JSON schemas from Pydantic models
  - [x] Include `search_docs` tool definition with fuzzy search note
- [x] Create `src/docs_server/mcp/tools.py`:
  - [x] `call_search_docs(arguments: dict) -> dict` - Tool handler
  - [x] Validate input with `SearchDocsInput` Pydantic model
  - [x] Call `search.search_docs()`
  - [x] Format results as MCP content (text format)
  - [x] Include fuzzy search tip in description
  - [x] Handle errors (empty query, no results, Whoosh errors)
- [x] Update `handle_request()` to route `tools/call`:
  - [x] Parse tool name from params
  - [x] Route to appropriate tool handler
  - [x] Return formatted result
- [x] Write tests:
  - [x] `tests/test_mcp_search.py`
  - [x] Test Whoosh search with various queries
  - [x] Test fuzzy search (typos)
  - [x] Test boolean operators (AND, OR, NOT)
  - [x] Test field-specific queries (title:xxx)
  - [x] Test snippet extraction/highlighting
  - [x] Test multi-word queries
  - [x] `tests/test_mcp_tools.py`
  - [x] Test `search_docs` integration
  - [x] Test with real Whoosh index

**Deliverable:** Search works with Whoosh, supports fuzzy search, returns ranked results with highlights

---

### Phase 4: Additional Tools

**Goal:** `get_doc_page` and `list_doc_pages` implemented

- [x] Create Pydantic models in `models.py`:
  - [x] `GetDocPageInput` with `path` (required) and `sections` (optional list)
  - [x] `ListDocPagesInput` with `category` (optional)
- [x] Implement `get_doc_page` in `tools.py`:
  - [x] `call_get_doc_page(arguments: dict) -> dict`
  - [x] Validate path using existing `get_file_path()` helper
  - [x] Load content from search index
  - [x] If `sections` provided: filter to matching h2 sections
  - [x] Return full markdown content or filtered sections
  - [x] Handle errors (file not found, invalid path)
- [x] Implement section filtering helper:
  - [x] `filter_sections(content: str, section_names: list[str]) -> str`
  - [x] Parse markdown to find matching ## headings
  - [x] Extract content between headings
  - [x] Return concatenated sections
- [x] Implement `list_doc_pages` in `tools.py`:
  - [x] `call_list_doc_pages(arguments: dict) -> dict`
  - [x] Get all pages from search index
  - [x] If `category` provided: parse sidebar.md and filter
  - [x] Format as markdown list with paths and titles
  - [x] Return formatted list
- [x] Update `tools/list` to include new tools:
  - [x] Add `get_doc_page` definition
  - [x] Add `list_doc_pages` definition
- [x] Update `handle_request()` to route new tools
- [x] Write tests:
  - [x] Test `get_doc_page` with full content
  - [x] Test `get_doc_page` with section filtering
  - [x] Test `list_doc_pages` with and without category
  - [x] Test error cases (invalid path, section not found)

**Deliverable:** All 3 tools working (search, get_page, list_pages)

---

### Phase 5: Rate Limiting

**Goal:** Rate limiting enforced on `/mcp` endpoint

- [x] Import `slowapi` in `main.py`:
  - [x] `from slowapi import Limiter, _rate_limit_exceeded_handler`
  - [x] `from slowapi.util import get_remote_address`
  - [x] `from slowapi.errors import RateLimitExceeded`
- [x] Create rate limiter instance:
  - [x] `limiter = Limiter(key_func=get_remote_address)`
  - [x] Add to app state: `app.state.limiter = limiter`
- [x] Apply rate limit to `/mcp` endpoint:
  - [x] Add decorator: `@limiter.limit(f"{settings.MCP_RATE_LIMIT_REQUESTS}/{settings.MCP_RATE_LIMIT_WINDOW}second")`
  - [x] Ensure request parameter is passed
- [x] Add rate limit exception handler:
  - [x] `@app.exception_handler(RateLimitExceeded)`
  - [x] Return JSON-RPC error response
  - [x] Use error code `-32603` (Internal error)
  - [x] Include `retryAfter` in error data
  - [x] Include `limit` info (e.g., "120/min")
- [x] Write tests:
  - [x] `tests/test_mcp_integration.py`
  - [x] Test rate limit enforcement
  - [x] Test rate limit error format (JSON-RPC structure)

**Deliverable:** Rate limiting active, returns proper JSON-RPC errors

---

### Phase 6: Error Handling

**Goal:** Comprehensive error handling with contextual messages

- [x] Create error formatter in `server.py`:
  - [x] `format_error(code: int, message: str, data: dict | None = None) -> dict`
  - [x] Standard JSON-RPC error structure
  - [x] Include contextual data (path, query, params)
  - [x] If `DEBUG=true`: add traceback to data
- [x] Implement error handling for all JSON-RPC codes:
  - [x] `-32700` Parse error - Invalid JSON
  - [x] `-32600` Invalid request - Missing required fields
  - [x] `-32601` Method not found - Unknown MCP method
  - [x] `-32602` Invalid params - Pydantic validation failures
  - [x] `-32603` Internal error - Server errors, rate limit, file not found
- [x] Add contextual error data:
  - [x] File not found: `{"path": "..."}`
  - [x] Rate limit: `{"retryAfter": 30, "limit": "120/min"}`
  - [x] Search error: `{"query": "..."}`
  - [x] Invalid params: `{"field": "...", "error": "..."}`
- [x] Add try/except blocks in all tool handlers:
  - [x] Catch `ValidationError` from Pydantic → `-32602`
  - [x] Catch `FileNotFoundError` → `-32602` with path
  - [x] Catch generic exceptions → `-32603`
  - [x] Log all errors with appropriate level
- [x] Write error handling tests:
  - [x] Test each error code
  - [x] Test error data format
  - [x] Test DEBUG mode includes traceback
  - [x] Test production mode hides internals

**Deliverable:** All error cases handled with proper JSON-RPC responses

---

### Phase 7: Testing & Documentation

**Goal:** Complete test suite and user documentation

- [x] Complete test suite:
  - [x] 208 tests passing (includes MCP tests)
  - [x] Add edge case tests:
    - [x] Empty search query
    - [x] Search with special characters
    - [x] Path traversal attempts in get_doc_page
    - [x] Very long queries (>500 chars)
    - [x] Invalid section names
  - [ ] Add performance tests:
    - [ ] Search with 100+ docs (<100ms)
    - [ ] Index build time (<500ms for 100 docs)
    - [ ] Cache load time (<10ms)
  - [ ] Run coverage: `uv run pytest tests/ --cov=src/docs_server/mcp`
- [x] Create user documentation:
  - [x] `docs/features/mcp.md` - MCP user guide
    - [x] What is MCP and why use it
    - [x] Available tools and usage examples
    - [x] Configuration options
    - [x] Rate limiting details
    - [x] Integration with Claude Desktop
  - [x] Usage examples with JSON-RPC requests
  - [x] Configuration reference table
- [x] Update existing documentation:
  - [x] Add MCP section to `docs/index.md`
  - [x] Add `/mcp` endpoint to `docs/sidebar.md`
  - [x] Update `docs/api/endpoints.md` with MCP endpoint
  - [x] Update `README.md` with MCP feature bullet
- [x] Run quality checks:
  - [x] `uv run pytest tests/ -v` (all tests pass)
  - [x] `uv run ruff check src/ tests/` (no linting errors)
  - [x] `uv run ruff format src/ tests/` (code formatted)
  - [ ] Manual testing with sample requests

**Deliverable:** Production-ready feature with complete documentation

---

### Phase 8: CLI Tools & Cache Management

**Goal:** Add CLI tools for index management

- [x] Create `src/docs_server/mcp/cli.py`:
  - [x] `build` command - Build search index
  - [x] `validate` command - Check if cache is valid
  - [x] `invalidate` command - Clear cached index
  - [x] `info` command - Show index statistics
  - [x] Use `click` library for CLI (if not heavy) or argparse
- [x] Add CLI entry point to `pyproject.toml`:
  - [x] `[project.scripts]`
  - [x] `servemd-mcp = "docs_server.mcp.cli:main"`
- [x] Test CLI commands:
  - [x] `uv run python -m docs_server.mcp.cli build`
  - [x] `uv run python -m docs_server.mcp.cli validate`
  - [x] `uv run python -m docs_server.mcp.cli info`
  - [x] `uv run python -m docs_server.mcp.cli invalidate`
- [x] Document CLI usage in `docs/features/mcp.md`

**Deliverable:** CLI tools for manual cache management ✅

---

### Phase 9: Polish & Deploy

**Goal:** Production deployment ready

- [ ] Performance optimization:
  - [ ] Profile search with large doc sets (100+ files)
  - [ ] If >100ms: optimize scoring algorithm
  - [ ] If >500ms index build: add progress logging
  - [ ] Monitor memory usage during index build
- [x] Add structured logging:
  - [x] Log MCP requests: `[MCP] method=tools/call tool=search_docs`
  - [x] Log search queries: `[MCP] search query="..." results=5`
  - [x] Log index operations: `[MCP] index built: 42 docs (350ms)`
  - [x] Log rate limit hits: `[MCP] rate limit exceeded ip=...`
- [x] Update Docker configuration:
  - [x] Verify `slowapi` in dependencies (already present)
  - [ ] Test Docker build: `docker build -t servemd .`
  - [ ] Test container startup time with cache
  - [ ] Verify cache persistence with volume mount
- [x] Update deployment documentation:
  - [x] Add MCP ENV vars to `docs/configuration.md`
  - [x] Add k8s/k3s considerations for cache volume
  - [x] Add horizontal scaling notes (each pod has own cache)
  - [ ] Update `examples/k8s-simple.yaml` if needed (not critical)
- [x] Manual testing:
  - [x] Test with curl: send JSON-RPC requests (tested and documented)
  - [x] Created comprehensive manual testing guide: `examples/mcp-manual-testing.md`
  - [ ] Test with Claude Desktop (requires user setup)
  - [ ] Test with n8n/make.com webhook (requires user setup)
  - [x] Verify rate limiting in production-like environment (test scripts provided)
  - [x] Test cache persistence across restarts (verified in testing)
- [x] Create deployment checklist:
  - [x] Created `examples/deployment-checklist.md` with comprehensive steps:
    - [x] Pre-deployment testing
    - [x] Docker build verification
    - [x] API testing scripts
    - [x] Rate limiting tests
    - [x] Kubernetes deployment steps
    - [x] Post-deployment verification
    - [x] Log monitoring
    - [x] Performance monitoring
    - [x] Cache persistence testing
    - [x] Rollback procedures
    - [x] Troubleshooting guide

**Deliverable:** Deployed to production, monitored (Partially complete - logging and docs done)

---

## Success Criteria

- [ ] **Functional Requirements**
  - [ ] `/mcp` endpoint responds to JSON-RPC 2.0 requests
  - [ ] `initialize` method returns correct capabilities
  - [ ] `tools/list` returns 3 tool definitions with schemas
  - [ ] `search_docs` returns ranked results with snippets
  - [ ] `get_doc_page` returns full or filtered content
  - [ ] `list_doc_pages` returns all available pages
  - [ ] Rate limiting enforced at 120 req/min per IP
  - [ ] All errors return proper JSON-RPC error format

- [ ] **Performance Requirements**
  - [ ] Index build: <500ms for 100 documents
  - [ ] Index load from cache: <10ms
  - [ ] Search query: <100ms for 100 documents
  - [ ] Get page: <10ms
  - [ ] Memory footprint: <10MB for 100 documents

- [ ] **Quality Requirements**
  - [ ] Test coverage: ~80% for MCP module
  - [ ] All tests pass: `uv run pytest tests/ -v`
  - [ ] No linting errors: `uv run ruff check src/ tests/`
  - [ ] Code formatted: `uv run ruff format src/ tests/`

- [ ] **Documentation Requirements**
  - [ ] User guide in `docs/features/mcp.md`
  - [ ] API reference in `docs/api/endpoints.md`
  - [ ] Configuration in `docs/configuration.md`
  - [ ] Updated README.md with MCP feature

- [ ] **Deployment Requirements**
  - [ ] Docker build succeeds
  - [ ] Container starts with cached index (<1 second)
  - [ ] Existing endpoints still work
  - [ ] MCP works in production environment

---

## Key Files to Modify

### New Files to Create

```
src/docs_server/mcp/
├── __init__.py               # Package initialization
├── server.py                 # JSON-RPC 2.0 handler (200 lines)
├── models.py                 # Pydantic models (50 lines)
├── indexer.py                # Index builder/loader (250 lines)
├── search.py                 # Search implementation (150 lines)
└── tools.py                  # Tool implementations (200 lines)

tests/
├── test_mcp_indexer.py       # Index tests (~100 lines)
├── test_mcp_search.py        # Search tests (~100 lines)
├── test_mcp_tools.py         # Tool tests (~150 lines)
├── test_mcp_server.py        # JSON-RPC tests (~100 lines)
└── test_mcp_integration.py   # Integration tests (~150 lines)

docs/features/
└── mcp.md                    # User documentation (~300 lines)
```

**Estimated New Code:** ~1,850 lines (including tests and docs)

### Existing Files to Modify

```
src/docs_server/
├── main.py                   # Add /mcp endpoint, startup event (~30 lines)
└── config.py                 # Add MCP settings (~10 lines)

docs/
├── index.md                  # Add MCP section (~5 lines)
├── sidebar.md                # Add MCP link (~2 lines)
└── api/endpoints.md          # Document /mcp endpoint (~50 lines)

pyproject.toml                # Add slowapi dependency (~1 line)
README.md                     # Add MCP feature (~5 lines)
```

**Estimated Modified Code:** ~100 lines

---

## Impact Analysis

### Positive Impacts

1. **New Capability**
   - LLMs can query documentation interactively
   - Reduced context window usage (250x savings)
   - Better UX for AI assistants

2. **Complementary to Existing**
   - Works alongside `llms.txt` and `llms-full.txt`
   - No changes to existing endpoints
   - Optional feature (can be disabled via `MCP_ENABLED=false`)

3. **Performance**
   - Fast bootup with cached index (<10ms)
   - Efficient search (50-100ms per query)
   - Low memory overhead (~5MB per 100 docs)

### Potential Risks

1. **Rate Limiting Bypass**
   - **Risk:** Users could bypass rate limits with multiple IPs
   - **Mitigation:** Acceptable for public docs, can add reverse proxy limits
   - **Impact:** Low (documentation is public anyway)

2. **Index Build Delay**
   - **Risk:** First startup without cache takes ~500ms
   - **Mitigation:** Cache persists across restarts
   - **Impact:** Low (one-time delay per deployment)

3. **Search Quality**
   - **Risk:** Simple text search might miss relevant results
   - **Mitigation:** Title-heavy scoring prioritizes well-structured docs
   - **Impact:** Medium (can enhance with fuzzy search later)

4. **Additional Complexity**
   - **Risk:** More code to maintain
   - **Mitigation:** Well-tested, follows existing patterns
   - **Impact:** Medium (~1,850 new lines)

### Dependencies

**New External Dependencies:**
- `whoosh>=2.7.4` - Full-text search engine (pure Python, production-ready)
- `slowapi>=0.1.9` - Rate limiting (well-maintained, FastAPI-compatible)

**Total:** 2 new dependencies (both pure Python, no C extensions)

**Internal Dependencies:**
- Reuses existing `get_file_path()` helper
- Reuses existing cache infrastructure pattern
- Reuses existing markdown parsing for content extraction

---

## Rollback Strategy

### If Issues Arise During Deployment

1. **Disable MCP Feature**
   ```bash
   # Set environment variable
   MCP_ENABLED=false
   
   # Or comment out in config
   # MCP_ENABLED: bool = True  # Disabled temporarily
   ```
   - Existing endpoints continue working
   - No restart needed (just reload config)

2. **Remove /mcp Endpoint**
   - Comment out endpoint in `main.py`
   - Restart application
   - MCP code stays but isn't accessible

3. **Full Rollback**
   ```bash
   # Revert to previous commit
   git revert <commit-hash>
   
   # Remove MCP package
   rm -rf src/docs_server/mcp/
   
   # Remove slowapi dependency
   # Edit pyproject.toml, run uv sync
   
   # Remove tests
   rm tests/test_mcp_*.py
   ```

### Testing Rollback

- [ ] Verify `MCP_ENABLED=false` disables endpoint
- [ ] Verify existing endpoints still work with MCP disabled
- [ ] Test full rollback in development environment

---

## Validation Checklist

### Pre-Deployment

- [ ] All tests pass locally: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/ tests/`
- [ ] Code formatted: `uv run ruff format src/ tests/`
- [ ] Test coverage ≥80% for MCP module
- [ ] Manual testing completed:
  - [ ] `initialize` request/response
  - [ ] `tools/list` returns 3 tools
  - [ ] `search_docs` with various queries
  - [ ] `get_doc_page` with and without sections
  - [ ] `list_doc_pages` with and without category
  - [ ] Rate limiting enforces 120/min
  - [ ] Error handling (invalid JSON, unknown method, etc.)
- [ ] Documentation reviewed:
  - [ ] User guide is clear
  - [ ] API reference is accurate
  - [ ] Configuration documented
- [ ] Docker build succeeds: `docker build -t servemd .`
- [ ] Container starts successfully

### Post-Deployment

- [ ] Health check passes: `curl http://host:8080/health`
- [ ] Existing endpoints work:
  - [ ] `GET /` redirects to `/index.html`
  - [ ] `GET /index.html` returns rendered HTML
  - [ ] `GET /llms.txt` returns text
  - [ ] `GET /llms-full.txt` returns text
- [ ] MCP endpoint responds: `POST /mcp` with `initialize`
- [ ] Rate limiting works (verify 429 after 120 requests)
- [ ] Index builds/loads successfully (check logs)
- [ ] Search returns results (test with known query)
- [ ] No errors in logs (check application logs)
- [ ] Performance acceptable:
  - [ ] Response time <100ms for search
  - [ ] No memory leaks (monitor over time)
  - [ ] CPU usage normal

### Monitoring (First 24 Hours)

- [ ] Track MCP endpoint usage (request count)
- [ ] Track rate limit hits (how many IPs hit limit)
- [ ] Monitor error rates (should be <1%)
- [ ] Monitor response times (should be <100ms)
- [ ] Monitor memory usage (should stay stable)
- [ ] Check logs for unexpected errors

---

## Appendix: Code Examples

### A. JSON-RPC 2.0 Request/Response Examples

**Request: Initialize**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "claude-desktop",
      "version": "1.0.0"
    }
  }
}
```

**Response: Initialize**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "servemd-mcp",
      "version": "1.0.0"
    }
  }
}
```

**Request: Search**
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {
      "query": "rate limiting",
      "limit": 5
    }
  }
}
```

**Response: Search**
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 3 results:\n\n1. api/endpoints.md (score: 15)\n   '...No rate limiting by default. For production, use...'\n\n2. configuration.md (score: 8)\n   '...MCP_RATE_LIMIT_REQUESTS=120...'"
      }
    ]
  }
}
```

**Error: Rate Limit Exceeded**
```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "error": {
    "code": -32603,
    "message": "Rate limit exceeded",
    "data": {
      "retryAfter": 30,
      "limit": "120/min"
    }
  }
}
```

### B. Pydantic Model Examples

```python
from pydantic import BaseModel, Field

class SearchDocsInput(BaseModel):
    """Input model for search_docs tool"""
    query: str = Field(
        min_length=1,
        max_length=500,
        description="Search query to find relevant documentation"
    )
    limit: int = Field(
        ge=1,
        le=50,
        default=10,
        description="Maximum number of results to return"
    )

class GetDocPageInput(BaseModel):
    """Input model for get_doc_page tool"""
    path: str = Field(
        min_length=1,
        description="Relative path to documentation file (e.g., 'api/endpoints.md')"
    )
    sections: list[str] | None = Field(
        default=None,
        description="Optional list of h2 section titles to filter"
    )

class ListDocPagesInput(BaseModel):
    """Input model for list_doc_pages tool"""
    category: str | None = Field(
        default=None,
        description="Optional category filter from sidebar structure"
    )
```

### C. Search Index Structure Example

```python
# Example search index structure
search_index = {
    "version": "1.0",
    "built_at": "2026-01-31T10:30:00Z",
    "docs_root": "/app/docs",
    "docs_count": 3,
    "index": {
        "api/endpoints.md": {
            "path": "api/endpoints.md",
            "title": "API Endpoints Reference",
            "content": "# API Endpoints Reference\n\n## GET /llms.txt\n\nServe llms.txt...",
            "sections": [
                {
                    "heading": "GET /llms.txt",
                    "level": 2,
                    "content": "Serve llms.txt with fallback strategy...",
                    "line_start": 73,
                    "line_end": 84
                },
                {
                    "heading": "Rate Limiting",
                    "level": 2,
                    "content": "No rate limiting by default...",
                    "line_start": 265,
                    "line_end": 280
                }
            ],
            "mtime": 1706745600.0,
            "size": 15234,
            "word_count": 2341
        }
    }
}
```

### D. Similar Implementation References

**Existing Cache Pattern** (from `caching.py`):
```python
# Similar pattern we'll use for MCP index cache
async def get_cached_llms(cache_file: str) -> Optional[str]:
    """Get cached llms content if exists."""
    cache_path = settings.CACHE_ROOT / "llms" / cache_file
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    return None

async def save_cached_llms(cache_file: str, content: str) -> None:
    """Save llms content to cache."""
    cache_dir = settings.CACHE_ROOT / "llms"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / cache_file
    cache_path.write_text(content, encoding="utf-8")
```

**Existing Path Validation** (from `helpers.py`):
```python
# We'll reuse this for get_doc_page path validation
def get_file_path(path: str) -> Path | None:
    """
    Resolve a file path safely within DOCS_ROOT.
    Returns None if path is invalid or outside DOCS_ROOT.
    """
    try:
        # Construct full path
        full_path = (settings.DOCS_ROOT / path).resolve()
        
        # Ensure path is within DOCS_ROOT (prevent traversal)
        if not str(full_path).startswith(str(settings.DOCS_ROOT.resolve())):
            logger.warning(f"Path traversal attempt: {path}")
            return None
        
        # Check if file exists
        if not full_path.exists():
            return None
        
        return full_path
    except Exception as e:
        logger.error(f"Error resolving path {path}: {e}")
        return None
```

**Existing Startup Event Pattern** (from `main.py`):
```python
# We'll add MCP index building to startup events
# Currently no startup events, so we'll create:
@app.on_event("startup")
async def startup_event():
    """Initialize MCP on startup"""
    if settings.MCP_ENABLED:
        from .mcp.indexer import build_or_load_index
        await build_or_load_index()
        logger.info("✅ MCP search index ready")
```

### E. Rate Limiting Implementation Example

```python
# Similar to existing pattern but using slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Add exception handler for JSON-RPC format
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded with JSON-RPC error"""
    # Extract request ID if present
    try:
        body = await request.json()
        request_id = body.get("id")
    except:
        request_id = None
    
    return JSONResponse(
        status_code=200,  # JSON-RPC uses 200 for errors
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": "Rate limit exceeded",
                "data": {
                    "retryAfter": 30,
                    "limit": f"{settings.MCP_RATE_LIMIT_REQUESTS}/{settings.MCP_RATE_LIMIT_WINDOW}s"
                }
            }
        }
    )

# Apply to endpoint
@app.post("/mcp")
@limiter.limit(f"{settings.MCP_RATE_LIMIT_REQUESTS}/{settings.MCP_RATE_LIMIT_WINDOW}second")
async def mcp_endpoint(request: Request):
    body = await request.json()
    result = await handle_mcp_request(body)
    return JSONResponse(content=result)
```

### F. Search Scoring Algorithm Example

```python
def calculate_score(doc: dict, query: str) -> int:
    """Calculate relevance score for a document"""
    score = 0
    query_lower = query.lower()
    query_terms = query_lower.split()
    
    # Title scoring (highest weight)
    title_lower = doc["title"].lower()
    if query_lower in title_lower:
        score += 100  # Exact phrase match
    for term in query_terms:
        if term in title_lower:
            score += 20  # Individual term match
    
    # Section heading scoring (medium weight)
    for section in doc["sections"]:
        heading_lower = section["heading"].lower()
        if query_lower in heading_lower:
            score += 50  # Exact phrase match
        for term in query_terms:
            if term in heading_lower:
                score += 10  # Individual term match
    
    # Content scoring (base weight)
    content_lower = doc["content"].lower()
    for term in query_terms:
        score += content_lower.count(term)  # 1 point per occurrence
    
    return score
```

---

## Notes

- Refer to `specs/mcp-specification.md` for complete technical specification
- All design decisions documented in specification (7 questions resolved)
- Estimated timeline: 3-4 weeks part-time or 1.5-2 weeks full-time
- Feature can be disabled via `MCP_ENABLED=false` if issues arise
- Compatible with existing llms.txt endpoints (complementary, not replacement)
