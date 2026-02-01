# MCP (Model Context Protocol) Support

ServeMD includes built-in support for the [Model Context Protocol (MCP)](https://spec.modelcontextprotocol.io/), enabling LLMs like Claude to interactively query your documentation instead of loading everything into context.

## Why MCP?

Traditional approaches like `llms.txt` and `llms-full.txt` dump entire documentation into context, which:

- **Wastes tokens** - A 500KB documentation site uses ~125K tokens
- **Hits context limits** - Large documentation may exceed context windows
- **Lacks precision** - LLMs must search through all content for relevant info

MCP provides **on-demand search and retrieval**:

- **250x less context** - Typical queries use ~2KB instead of 500KB
- **Precise results** - Full-text search with relevance scoring
- **Scales infinitely** - Works with 10 or 10,000 documentation pages

## Quick Start

### 1. Enable MCP (Default: Enabled)

```bash
# MCP is enabled by default
# To disable:
MCP_ENABLED=false
```

### 2. Test the Endpoint

```bash
# Initialize handshake
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "curl", "version": "1.0"}
    }
  }'

# List available tools
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/list"
  }'
```

## Available Tools

ServeMD exposes three MCP tools:

### search_docs

Search documentation with full-text search powered by Whoosh.

**Features:**
- Fuzzy search (typo tolerance): `configration~` finds "configuration"
- Boolean operators: `auth AND login`, `rate OR limit`, `config NOT debug`
- Field-specific: `title:API`, `content:authentication`
- Phrase search: `"rate limiting"`

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
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

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 3 result(s):\n\n1. **API Endpoints** (`api/endpoints.md`)\n   Category: api\n   Score: 15.50\n   Rate limiting is enforced at 120 requests...\n\n..."
      }
    ]
  }
}
```

### get_doc_page

Retrieve the full content of a specific documentation page, optionally filtered to specific sections.

**Request (full page):**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "get_doc_page",
    "arguments": {
      "path": "api/endpoints.md"
    }
  }
}
```

**Request (specific sections):**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "get_doc_page",
    "arguments": {
      "path": "api/endpoints.md",
      "sections": ["GET /health", "Rate Limiting"]
    }
  }
}
```

### list_doc_pages

List all available documentation pages, optionally filtered by category.

**Request (all pages):**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "list_doc_pages",
    "arguments": {}
  }
}
```

**Request (filtered by category):**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "list_doc_pages",
    "arguments": {
      "category": "api"
    }
  }
}
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_ENABLED` | `true` | Enable/disable MCP endpoint |
| `MCP_RATE_LIMIT_REQUESTS` | `120` | Max requests per window per IP |
| `MCP_RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |
| `MCP_MAX_SEARCH_RESULTS` | `10` | Default max search results |
| `MCP_SNIPPET_LENGTH` | `200` | Max characters for snippets |

## Rate Limiting

The MCP endpoint is rate-limited to prevent abuse:

- **Default:** 120 requests per 60 seconds per IP address
- **Response on limit:** JSON-RPC error with retry information

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "error": {
    "code": -32603,
    "message": "Rate limit exceeded",
    "data": {
      "retryAfter": 60,
      "limit": "120/60s"
    }
  }
}
```

## Search Index

ServeMD builds a Whoosh search index on startup:

- **First start:** ~500ms to index (100 docs)
- **Subsequent starts:** ~10ms to load from cache
- **Cache location:** `CACHE_ROOT/mcp/whoosh/`
- **Automatic rebuild:** When docs change (hash-based validation)

The index includes:
- Document paths (unique identifier)
- Titles (2x boost for relevance)
- Full content (for search and snippets)
- Section headings (1.5x boost)
- Categories (from directory structure)

## Integration Examples

### Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "my-docs": {
      "type": "http",
      "url": "https://docs.example.com/mcp"
    }
  }
}
```

### n8n / Make.com

Use HTTP Request nodes to call the MCP endpoint:

1. Set URL: `https://docs.example.com/mcp`
2. Method: POST
3. Headers: `Content-Type: application/json`
4. Body: JSON-RPC request

### Custom LLM Applications

```python
import httpx

async def search_docs(query: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://docs.example.com/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "search_docs",
                    "arguments": {"query": query}
                }
            }
        )
        return response.json()["result"]["content"][0]["text"]
```

## Error Codes

MCP uses standard JSON-RPC 2.0 error codes:

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `-32700` | Parse error | Invalid JSON in request |
| `-32600` | Invalid request | Missing `method` or `jsonrpc` |
| `-32601` | Method not found | Unknown MCP method |
| `-32602` | Invalid params | Validation error, file not found |
| `-32603` | Internal error | Rate limit, index not ready |

## Comparison: MCP vs llms.txt

| Feature | llms.txt | llms-full.txt | MCP |
|---------|----------|---------------|-----|
| Context size | ~10KB | ~500KB | ~2KB |
| Precision | Low | Low | High |
| Interactive | No | No | Yes |
| Real-time | No | No | Yes |
| Scales to | 100 pages | 50 pages | Unlimited |

**Recommendation:** Use MCP for interactive queries, `llms.txt` for quick overviews, and `llms-full.txt` for offline/batch processing.

## CLI Tools

ServeMD includes command-line tools for managing the MCP search index.

### Available Commands

```bash
# Build or rebuild the search index
uv run python -m docs_server.mcp.cli build

# Force rebuild (ignore cache)
uv run python -m docs_server.mcp.cli build --force

# Validate cached index
uv run python -m docs_server.mcp.cli validate

# Show index statistics
uv run python -m docs_server.mcp.cli info

# Clear cached index
uv run python -m docs_server.mcp.cli invalidate

# Clear without confirmation
uv run python -m docs_server.mcp.cli invalidate --confirm
```

### Command Details

#### build

Builds the search index from documentation files. If a valid cache exists, it will be used unless `--force` is specified.

```bash
$ uv run python -m docs_server.mcp.cli build
2026-01-31 13:48:58 [INFO] Building MCP search index...
2026-01-31 13:48:58 [INFO] DOCS_ROOT: /app/docs
2026-01-31 13:48:58 [INFO] CACHE_ROOT: /app/cache
2026-01-31 13:48:58 [INFO] ✅ MCP index built (184.4ms, 14 docs)
```

#### validate

Checks if the cached index is valid and can be used.

```bash
$ uv run python -m docs_server.mcp.cli validate
2026-01-31 13:48:59 [INFO] Validating MCP search index cache...
2026-01-31 13:48:59 [INFO] ✅ Cache is valid
2026-01-31 13:48:59 [INFO]    Index version: 1.0
2026-01-31 13:48:59 [INFO]    Documents: 14
```

#### info

Shows detailed information about the index including configuration, statistics, and cache status.

```bash
$ uv run python -m docs_server.mcp.cli info
2026-01-31 13:49:02 [INFO] MCP Search Index Information
2026-01-31 13:49:02 [INFO] ============================================================
2026-01-31 13:49:02 [INFO]
📋 Configuration:
2026-01-31 13:49:02 [INFO]   DOCS_ROOT:    /app/docs
2026-01-31 13:49:02 [INFO]   MCP_ENABLED:  True
...
```

#### invalidate

Clears the cached index and metadata. The next server startup will rebuild the index.

```bash
$ uv run python -m docs_server.mcp.cli invalidate
This will delete: /app/cache/mcp
Are you sure? [y/N]: y
2026-01-31 13:49:02 [INFO] ✅ Cache cleared successfully
```

### Use Cases

**Pre-build index for production:**
```bash
# In Dockerfile or deployment script
uv run python -m docs_server.mcp.cli build
```

**Verify cache after deployment:**
```bash
uv run python -m docs_server.mcp.cli validate && echo "Ready"
```

**Debug index issues:**
```bash
uv run python -m docs_server.mcp.cli info
```

**Force rebuild after doc changes:**
```bash
uv run python -m docs_server.mcp.cli build --force
```

## Troubleshooting

### "Search index not initialized"

The search index hasn't finished building. This can happen if:
- Server just started (wait a few seconds)
- Index build failed (check logs)
- `MCP_ENABLED=false` is set

**Solution:** Check index status with `uv run python -m docs_server.mcp.cli info`

### "Rate limit exceeded"

You've exceeded 120 requests/minute. Wait for the `retryAfter` period or adjust:

```bash
MCP_RATE_LIMIT_REQUESTS=300 MCP_RATE_LIMIT_WINDOW=60
```

### No search results

- Check that your docs are in `DOCS_ROOT`
- Verify files have `.md` extension
- Try broader search terms
- Check for typos (or use fuzzy search: `term~`)

**Debug:** Run `uv run python -m docs_server.mcp.cli info` to check indexed document count

### Cache validation fails

If the cache keeps rebuilding on every startup:
- Check that `DOCS_ROOT` path is consistent
- Verify file permissions on `CACHE_ROOT/mcp/`
- Look for file modification time issues (e.g., volume mounts)

**Solution:** Force rebuild with `uv run python -m docs_server.mcp.cli build --force`
