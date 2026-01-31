# MCP Manual Testing Guide

Quick reference for manually testing MCP functionality.

## Prerequisites

```bash
# Start the server
cd /Users/jochem/dev/servemd
DOCS_ROOT=./docs uv run python -m docs_server
```

Server will be available at: http://localhost:8080

## 1. Health Check

```bash
curl -s http://localhost:8080/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "docs_root": "/path/to/docs",
  "cache_root": "/path/to/cache",
  "debug": false,
  "mcp_enabled": true
}
```

## 2. Initialize (Handshake)

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "curl",
        "version": "1.0"
      }
    }
  }' | jq
```

Expected response:
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

## 3. List Tools

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/list"
  }' | jq
```

Expected: 3 tools (search_docs, get_doc_page, list_doc_pages)

## 4. Search Documents

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "3",
    "method": "tools/call",
    "params": {
      "name": "search_docs",
      "arguments": {
        "query": "configuration",
        "limit": 3
      }
    }
  }' | jq
```

Expected: Ranked results with snippets

## 5. Get Document Page

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "4",
    "method": "tools/call",
    "params": {
      "name": "get_doc_page",
      "arguments": {
        "path": "configuration.md"
      }
    }
  }' | jq
```

Expected: Full markdown content

## 6. Get Document Page with Section Filter

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "5",
    "method": "tools/call",
    "params": {
      "name": "get_doc_page",
      "arguments": {
        "path": "configuration.md",
        "sections": ["Core Settings", "MCP Settings"]
      }
    }
  }' | jq
```

Expected: Only specified sections

## 7. List All Pages

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "6",
    "method": "tools/call",
    "params": {
      "name": "list_doc_pages",
      "arguments": {}
    }
  }' | jq
```

Expected: List of all documentation pages

## 8. List Pages by Category

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "7",
    "method": "tools/call",
    "params": {
      "name": "list_doc_pages",
      "arguments": {
        "category": "deployment"
      }
    }
  }' | jq
```

Expected: Only deployment-related pages

## 9. Fuzzy Search

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "8",
    "method": "tools/call",
    "params": {
      "name": "search_docs",
      "arguments": {
        "query": "configuraton~",
        "limit": 3
      }
    }
  }' | jq
```

Expected: Finds "configuration" despite typo

## 10. Boolean Search

```bash
# AND operator
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "9",
    "method": "tools/call",
    "params": {
      "name": "search_docs",
      "arguments": {
        "query": "docker AND kubernetes",
        "limit": 5
      }
    }
  }' | jq

# OR operator
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "10",
    "method": "tools/call",
    "params": {
      "name": "search_docs",
      "arguments": {
        "query": "docker OR kubernetes",
        "limit": 5
      }
    }
  }' | jq
```

## 11. Rate Limiting Test

```bash
# Send 125 requests rapidly
for i in {1..125}; do
  curl -s -X POST http://localhost:8080/mcp \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":\"$i\",\"method\":\"tools/list\"}" \
    > /dev/null &
done
wait

# Try one more (should be rate limited)
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"126","method":"tools/list"}' | jq
```

Expected: 429 status with retry info after exceeding limit

## 12. Error Handling

```bash
# Invalid JSON
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{invalid json}' | jq

# Unknown method
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"unknown"}' | jq

# Invalid tool
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"invalid_tool"}}' | jq

# Missing required params
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"search_docs"}}' | jq
```

Expected: Proper JSON-RPC error responses

## CLI Testing

```bash
# Build index
uv run python -m docs_server.mcp.cli build

# Validate cache
uv run python -m docs_server.mcp.cli validate

# Show info
uv run python -m docs_server.mcp.cli info

# Invalidate cache
uv run python -m docs_server.mcp.cli invalidate --confirm
```

## Log Monitoring

Watch for structured log entries:

```bash
# Start server and watch logs
DOCS_ROOT=./docs uv run python -m docs_server 2>&1 | grep "\[MCP\]"
```

Expected log entries:
```
[MCP] index built: 14 docs (184.4ms)
[MCP] index loaded from cache: 14 docs (15.6ms)
[MCP] method=initialize id=1
[MCP] method=tools/call tool=search_docs
[MCP] search query="configuration" results=3
[MCP] rate limit exceeded ip=127.0.0.1 limit=120/60s
```

## Performance Benchmarks

```bash
# Index build time
time uv run python -m docs_server.mcp.cli build --force

# Search latency (warm cache)
time curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"search_docs","arguments":{"query":"test"}}}' \
  > /dev/null
```

Expected:
- Index build: <500ms for 100 docs
- Search query: <100ms
- Get page: <10ms

## Integration Testing

### Claude Desktop

1. Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "servemd": {
      "type": "http",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

2. Restart Claude Desktop
3. Test queries like "Search for configuration docs"

### n8n Workflow

1. Create HTTP Request node
2. Set URL: `http://localhost:8080/mcp`
3. Method: POST
4. Body: JSON-RPC request
5. Test workflow

## Success Criteria

- [ ] All manual tests pass
- [ ] Response times within spec (<100ms for search)
- [ ] Rate limiting enforced correctly
- [ ] Structured logging visible in output
- [ ] No errors in logs
- [ ] Cache persists across restarts
- [ ] CLI tools work correctly
