# MCP Integration Specification

**Version:** 1.0  
**Date:** 2026-01-31  
**Status:** Design Phase

---

## Executive Summary

Add Model Context Protocol (MCP) support to ServeMD to enable LLMs to interactively query documentation. MCP complements existing `llms.txt`/`llms-full.txt` endpoints by providing on-demand search instead of static dumps.

**Key Benefit:** 250x less context usage (2KB vs 500KB for typical query)

---

## Architecture

### Design Constraints

1. ✅ **Immutable doc root** - Docs baked into Docker image (read-only)
2. ✅ **Disk-based index cache** - Fast bootup for k8s/k3s horizontal scaling
3. ✅ **No external services** - Self-contained (no Redis, Postgres, etc.)
4. ✅ **HTTP/JSON-RPC transport** - FastAPI-native, simple

### System Overview

```
┌─────────────┐
│ LLM Client  │
│ (Claude)    │
└──────┬──────┘
       │ POST /mcp
       │ JSON-RPC 2.0
       ▼
┌──────────────────────┐
│  FastAPI App         │
│  ┌────────────────┐  │
│  │ Search Index   │  │ ← Loaded from CACHE_ROOT
│  │ (in memory)    │  │   or built on startup
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │ MCP Tools:     │  │
│  │ - search_docs  │  │
│  │ - get_doc_page │  │
│  │ - list_pages   │  │
│  └────────────────┘  │
└──────────────────────┘
```

---

## Index Cache Strategy

### Cache Location

```
CACHE_ROOT/
├── html/              # Existing: rendered HTML
├── llms/              # Existing: llms.txt files
└── mcp/               # NEW
    └── search-index.json
```

### Cache Lifecycle

**Startup:**
1. Check if `search-index.json` exists in cache
2. Validate cache (version, file count, DEBUG mode)
3. If valid: load from disk (10ms)
4. If invalid: rebuild and save (500ms for 100 docs)

**Runtime:**
- Index stays in memory
- No rebuilds (production mode)
- DEBUG mode: rebuild on each startup

**Benefits:**
- Fast bootup for new k8s pods (10ms vs 500ms)
- No external services needed
- Survives container restarts

### Index Format

```json
{
  "version": "1.0",
  "built_at": "2026-01-31T10:30:00Z",
  "docs_root": "/app/docs",
  "docs_count": 42,
  "index": {
    "api/endpoints.md": {
      "path": "api/endpoints.md",
      "title": "API Endpoints Reference",
      "content": "full markdown content...",
      "sections": [
        {
          "heading": "GET /llms.txt",
          "level": 2,
          "content": "section content...",
          "line_start": 73,
          "line_end": 84
        }
      ],
      "mtime": 1706745600.0,
      "size": 15234,
      "word_count": 2341
    }
  }
}
```

---

## Search Implementation

### Algorithm: Python In-Memory

**Why not grep/ripgrep:**
- Grep: Fast but no ranking, hard to extract snippets, external process
- Python: Full control, structured output, 50-100ms (fast enough)

**Search Process:**
1. Convert query to lowercase
2. Score each document:
   - Title match: high weight
   - Section heading match: medium weight
   - Content match: base weight
3. Extract snippet (~200 chars around match)
4. Sort by score, return top N

**Performance:**
- 10-100ms per query (up to 100 docs)
- Scales to ~500 docs before considering hybrid grep approach

---

## MCP Protocol

### Transport: HTTP/JSON-RPC 2.0

**Endpoint:** `POST /mcp`  
**Content-Type:** `application/json`

**Request Format:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {
      "query": "rate limiting"
    }
  }
}
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 3 results:\n1. api/endpoints.md..."
      }
    ]
  }
}
```

### MCP Methods

| Method | Purpose | Status |
|--------|---------|--------|
| `initialize` | Handshake/capability negotiation | Required |
| `tools/list` | List available tools | Required |
| `tools/call` | Execute a tool | Required |

---

## MCP Tools

### 1. search_docs

**Purpose:** Full-text search across documentation

**Input:**
```json
{
  "query": "string (required)",
  "limit": "integer (optional, default: 10)"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "Found 3 results:\n\n1. api/endpoints.md (score: 15)\n   'No rate limiting by default...'\n\n2. config.md (score: 8)\n   'Configure MCP_RATE_LIMIT_REQUESTS...'"
  }]
}
```

### 2. get_doc_page

**Purpose:** Retrieve specific documentation page

**Input:**
```json
{
  "path": "string (required)",
  "sections": "array<string> (optional)"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "# API Endpoints\n\n## GET /llms.txt\n..."
  }]
}
```

### 3. list_doc_pages

**Purpose:** List all available documentation pages

**Input:**
```json
{
  "category": "string (optional)"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "Documentation Pages:\n\n- index.md\n- api/endpoints.md\n- configuration.md\n..."
  }]
}
```

---

## Rate Limiting

**Strategy:** Token bucket per IP address

**Configuration:**
- `MCP_RATE_LIMIT_REQUESTS`: 120 requests per window (configurable via ENV)
- `MCP_RATE_LIMIT_WINDOW`: 60 seconds (configurable via ENV)

**Implementation:** `slowapi` library (FastAPI-compatible)

**Response when exceeded:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "error": {
    "code": -32000,
    "message": "Rate limit exceeded",
    "data": {"retryAfter": 30}
  }
}
```

---

## Configuration

### Environment Variables

```bash
# MCP Feature
MCP_ENABLED=true                    # Enable/disable MCP endpoint (default: true)

# Rate Limiting
MCP_RATE_LIMIT_REQUESTS=120        # Requests per window (default: 120)
MCP_RATE_LIMIT_WINDOW=60           # Window in seconds (default: 60)

# Search
MCP_MAX_SEARCH_RESULTS=10          # Max results per search (default: 10)
MCP_SNIPPET_LENGTH=200             # Snippet length in chars (default: 200)
```

---

## File Structure

```
src/docs_server/
├── mcp/
│   ├── __init__.py
│   ├── server.py          # JSON-RPC handler
│   ├── indexer.py         # Index builder/loader
│   ├── search.py          # Search implementation
│   ├── tools.py           # Tool implementations (3 tools)
│   └── rate_limit.py      # Rate limiting middleware
├── main.py                # Add /mcp endpoint + startup event
└── config.py              # Add MCP config
```

---

## Dependencies

**New:**
- `slowapi>=0.1.9` - Rate limiting

**Existing (reused):**
- `fastapi` - Web framework
- `markdown` - Content parsing (via existing code)
- `pathlib` - File operations

---

## Performance

| Metric | Target |
|--------|--------|
| Index build (100 docs) | <500ms |
| Index load from cache | <10ms |
| Search query | <100ms |
| Get page | <10ms |
| Memory footprint | ~5MB per 100 docs |

---

## Security

1. **Path Traversal Prevention**
   - Reuse existing `get_file_path()` validation
   - No `..` or absolute paths allowed

2. **Rate Limiting**
   - Per-IP tracking
   - Configurable limits
   - Graceful 429 responses

3. **No Authentication**
   - Public endpoint by design
   - Rate limiting provides protection
   - Can add reverse proxy auth if needed

---

## Design Decisions Summary

All design questions resolved ✅

| # | Decision | Choice |
|---|----------|--------|
| 1 | Error Codes | Standard JSON-RPC 2.0 only |
| 2 | Input Validation | Pydantic models (schema-based) |
| 3 | Search Scoring | Title-heavy (100/50/1 weights) |
| 4 | Resources | No resources - tools only |
| 5 | Rate Limiting | 120/min, configurable via ENV |
| 6 | Testing | Pragmatic (unit + integration, ~80% coverage) |
| 7 | Error Messages | Contextual detail (production-safe) |

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Goal:** MCP endpoint responds to basic requests

**Tasks:**
1. Add dependency: `slowapi>=0.1.9` to `pyproject.toml`
2. Create MCP package structure:
   ```
   src/docs_server/mcp/__init__.py
   src/docs_server/mcp/server.py
   src/docs_server/mcp/models.py  (Pydantic models)
   ```
3. Implement JSON-RPC 2.0 handler in `server.py`:
   - Parse incoming requests
   - Validate JSON-RPC format
   - Route to method handlers
   - Format responses and errors
4. Add `/mcp` endpoint in `main.py`:
   ```python
   @app.post("/mcp")
   async def mcp_endpoint(request: Request):
       # Parse JSON body
       # Call mcp.server.handle_request()
       # Return JSON-RPC response
   ```
5. Implement `initialize` method:
   - Return server info and capabilities
   - Declare `tools` capability (no resources)
6. Add config in `config.py`:
   ```python
   MCP_ENABLED: bool = True
   MCP_RATE_LIMIT_REQUESTS: int = 120
   MCP_RATE_LIMIT_WINDOW: int = 60
   ```
7. Write basic tests:
   - `test_mcp_server.py` (JSON-RPC parsing)
   - Test `initialize` method

**Deliverable:** `/mcp` endpoint responds to `initialize` requests

**Estimated Time:** 2-3 days

---

### Phase 2: Search Index (Week 1-2)

**Goal:** Index builds/loads on startup and caches to disk

**Tasks:**
1. Create `mcp/indexer.py`:
   - `build_search_index()` - Scan docs, parse markdown
   - `save_index_to_cache()` - Write JSON to `CACHE_ROOT/mcp/`
   - `load_index_from_cache()` - Read from cache
   - `is_cache_valid()` - Validate cache
2. Implement markdown parsing helpers:
   - `extract_title()` - Get first # heading
   - `parse_sections()` - Extract ## sections
3. Add startup event in `main.py`:
   ```python
   @app.on_event("startup")
   async def startup_mcp():
       if settings.MCP_ENABLED:
           await build_or_load_index()
   ```
4. Store index in module-level variable:
   ```python
   _search_index: dict = {}
   
   def get_search_index() -> dict:
       return _search_index
   ```
5. Write tests:
   - `test_mcp_indexer.py` (build, save, load, validate)
   - Test with sample markdown files

**Deliverable:** Index builds on startup, loads from cache on restart

**Estimated Time:** 2-3 days

---

### Phase 3: Search Tool (Week 2)

**Goal:** `search_docs` tool works end-to-end

**Tasks:**
1. Create `mcp/search.py`:
   - `search_docs(query, limit)` - Main search function
   - Implement scoring algorithm (100/20/50/10/1 weights)
   - `extract_snippet()` - Context around matches
2. Create Pydantic model in `mcp/models.py`:
   ```python
   class SearchDocsInput(BaseModel):
       query: str = Field(min_length=1, max_length=500)
       limit: int = Field(ge=1, le=50, default=10)
   ```
3. Implement `tools/list` method in `server.py`:
   - Return tool definitions with JSON schemas
   - Auto-generate schemas from Pydantic models
4. Implement `tools/call` for `search_docs` in `mcp/tools.py`:
   - Validate input with Pydantic
   - Call `search.search_docs()`
   - Format results as MCP content
5. Write tests:
   - `test_mcp_search.py` (scoring, snippets)
   - `test_mcp_tools.py` (search_docs integration)

**Deliverable:** Search works via MCP protocol

**Estimated Time:** 2-3 days

---

### Phase 4: Additional Tools (Week 2-3)

**Goal:** `get_doc_page` and `list_doc_pages` implemented

**Tasks:**
1. Create Pydantic models:
   ```python
   class GetDocPageInput(BaseModel):
       path: str = Field(min_length=1)
       sections: list[str] | None = None
   
   class ListDocPagesInput(BaseModel):
       category: str | None = None
   ```
2. Implement `get_doc_page` in `tools.py`:
   - Validate path (reuse existing `get_file_path()`)
   - Load content from index
   - Filter by sections if requested
   - Return markdown content
3. Implement `list_doc_pages` in `tools.py`:
   - List all docs from index
   - Filter by category (parse from sidebar.md)
   - Return formatted list
4. Update `tools/list` to include new tools
5. Write tests for both tools

**Deliverable:** All 3 tools working

**Estimated Time:** 2 days

---

### Phase 5: Rate Limiting (Week 3)

**Goal:** Rate limiting enforced on `/mcp` endpoint

**Tasks:**
1. Add `slowapi` to imports in `main.py`
2. Create rate limiter instance:
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   ```
3. Apply rate limit to `/mcp` endpoint:
   ```python
   @app.post("/mcp")
   @limiter.limit(f"{settings.MCP_RATE_LIMIT_REQUESTS}/{settings.MCP_RATE_LIMIT_WINDOW}second")
   async def mcp_endpoint(request: Request):
       ...
   ```
4. Add rate limit exception handler:
   - Catch `RateLimitExceeded`
   - Return JSON-RPC error (-32603) with retry info
5. Write tests:
   - `test_mcp_integration.py` (rate limit enforcement)
   - Verify 429 response after limit

**Deliverable:** Rate limiting active and tested

**Estimated Time:** 1 day

---

### Phase 6: Error Handling (Week 3)

**Goal:** Comprehensive error handling with contextual messages

**Tasks:**
1. Create error formatter in `server.py`:
   ```python
   def format_error(code: int, message: str, data: dict | None = None):
       error = {"code": code, "message": message}
       if data:
           error["data"] = data
       if settings.DEBUG and "exception" in data:
           error["data"]["traceback"] = ...
       return error
   ```
2. Add error handling for:
   - Invalid JSON (`-32700`)
   - Invalid request structure (`-32600`)
   - Unknown methods (`-32601`)
   - Invalid params (`-32602`)
   - Internal errors (`-32603`)
3. Add contextual data:
   - File not found: include path
   - Rate limit: include retryAfter
   - Search error: include query
4. Write error handling tests

**Deliverable:** All error cases handled properly

**Estimated Time:** 1-2 days

---

### Phase 7: Testing & Documentation (Week 4)

**Goal:** Complete test suite and user documentation

**Tasks:**
1. Complete test suite:
   - Ensure ~80% coverage
   - Add edge case tests
   - Performance tests (search with 100 docs)
2. Create user documentation:
   - `docs/features/mcp.md` - User guide
   - Usage examples with Claude Desktop
   - Configuration reference
3. Update main docs:
   - Add MCP to `docs/index.md`
   - Add to `docs/sidebar.md`
   - Update `docs/api/endpoints.md`
4. Update README.md with MCP section
5. Run full test suite: `uv run pytest tests/ -v`
6. Run linters: `uv run ruff check src/ tests/`
7. Format code: `uv run ruff format src/ tests/`

**Deliverable:** Production-ready feature with docs

**Estimated Time:** 2-3 days

---

### Phase 8: Polish & Deploy (Week 4)

**Goal:** Production deployment ready

**Tasks:**
1. Performance optimization:
   - Profile search with large doc sets
   - Optimize if needed (>500ms is too slow)
2. Add logging:
   - Log MCP requests (method, tool name)
   - Log search queries and results count
   - Log index build/load times
3. Update Docker image:
   - Ensure slowapi is installed
   - Test container build
4. Update deployment docs:
   - Environment variables
   - k8s/k3s considerations
5. Manual testing:
   - Test with Claude Desktop (if possible)
   - Test with n8n/make.com (if possible)
   - Verify rate limiting in production

**Deliverable:** Deployed to production

**Estimated Time:** 2 days

---

### Summary Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Foundation | 2-3 days | `/mcp` endpoint active |
| 2. Search Index | 2-3 days | Index builds/caches |
| 3. Search Tool | 2-3 days | `search_docs` working |
| 4. Additional Tools | 2 days | All 3 tools working |
| 5. Rate Limiting | 1 day | Rate limits enforced |
| 6. Error Handling | 1-2 days | Errors handled properly |
| 7. Testing & Docs | 2-3 days | Tests + documentation |
| 8. Polish & Deploy | 2 days | Production ready |

**Total Estimated Time:** 3-4 weeks (part-time) or 1.5-2 weeks (full-time)

---

## Success Metrics

- ✅ 10ms cold start (cached index load)
- ✅ <100ms search response time
- ✅ Works with 100+ documentation pages
- ✅ Zero external dependencies
- ✅ Compatible with Claude Desktop, ChatGPT, etc.
