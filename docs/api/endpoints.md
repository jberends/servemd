# HTTP Endpoints

Complete API reference for all HTTP endpoints provided by the documentation server.

## Health Check

### `GET /health`

Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "docs_root": "/app/docs",
  "cache_root": "/app/cache",
  "debug": false
}
```

**Status Codes:**
- `200 OK` - Server is healthy

**Example:**
```bash
curl http://localhost:8080/health
```

---

## MCP Endpoint

### `POST /mcp`

Model Context Protocol endpoint for interactive documentation queries via JSON-RPC 2.0.

**Features:**
- Full-text search with Whoosh
- Fuzzy search (typo tolerance)
- Page retrieval with section filtering
- Rate limited (120 req/min per IP)

**Available Methods:**
- `initialize` — Handshake and capability negotiation
- `tools/list` — List available tools
- `tools/call` — Execute a tool (search_docs, get_doc_page, list_doc_pages)

**Example - Initialize:**
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {}
    }
  }'
```

**Example - Search:**
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "search_docs",
      "arguments": {"query": "configuration", "limit": 5}
    }
  }'
```

**Status Codes:**
- `200 OK` — Response returned (check JSON-RPC result/error)
- `404 Not Found` — MCP disabled
- `429 Too Many Requests` — Rate limit exceeded

**Error Codes (JSON-RPC):**
- `-32700` — Parse error (invalid JSON)
- `-32600` — Invalid request (missing fields)
- `-32601` — Method not found
- `-32602` — Invalid params
- `-32603` — Internal error (rate limit, index not ready)

See [MCP Integration Guide](../features/mcp.md) for complete documentation.

---

## LLMs.txt Endpoints

### `GET /llms.txt`

Returns AI assistant index with absolute URLs.

**Features:**
- PRIMARY: Serves curated `llms.txt` if exists
- FALLBACK: Auto-generates from `sidebar.md` + `index.md`
- Transforms relative links to absolute
- Cached for performance

**Response:** Plain text (Markdown format)

**Status Codes:**
- `200 OK` - Content returned
- `500 Internal Server Error` - Generation failed

**Example:**
```bash
curl http://localhost:8080/llms.txt
```

### `GET /llms-full.txt`

Returns complete documentation in one file.

**Features:**
- Includes llms.txt index
- Appends full content of all linked pages
- XML-style `<url>` and `<content>` tags
- Cached for performance

**Response Format:**
```
# Index content

<url>https://example.com/page1.md</url>
<content>
Full content of page1.md
</content>

<url>https://example.com/page2.md</url>
<content>
Full content of page2.md
</content>
```

**Status Codes:**
- `200 OK` - Content returned
- `500 Internal Server Error` - Generation failed

**Example:**
```bash
curl http://localhost:8080/llms-full.txt > all-docs.txt
```

---

## Content Endpoints

### `GET /` (Root)

Redirects to homepage.

**Response:** `302 Found` redirect to `/index.html`

**Example:**
```bash
curl -L http://localhost:8080/
```

### `GET /{path}.html`

Serves rendered HTML for markdown file.

**Features:**
- Renders `.md` file to styled HTML
- Includes navigation (sidebar, topbar)
- Adds table of contents
- Syntax highlighting
- Responsive design
- Cached after first render

**Parameters:**
- `path` - Path to markdown file (without `.md` extension)

**Response:** HTML document

**Status Codes:**
- `200 OK` - Content rendered
- `404 Not Found` - File doesn't exist
- `500 Internal Server Error` - Rendering failed

**Examples:**
```bash
# Homepage
curl http://localhost:8080/index.html

# Nested page
curl http://localhost:8080/user-guide/installation.html

# API docs
curl http://localhost:8080/api/endpoints.html
```

### `GET /{path}.md`

Serves raw markdown content.

**Features:**
- Returns original markdown source
- No rendering or processing
- UTF-8 encoded
- No caching (always fresh)

**Parameters:**
- `path` - Path to markdown file

**Response:** Plain text (Markdown)

**Status Codes:**
- `200 OK` - Content returned
- `404 Not Found` - File doesn't exist
- `500 Internal Server Error` - Read failed

**Examples:**
```bash
# Get raw markdown
curl http://localhost:8080/index.md

# Download a page
curl http://localhost:8080/api/endpoints.md -o endpoints.md
```

### `GET /{path}`

Serves static assets.

**Supported types:**
- Images: PNG, JPG, GIF, SVG
- Documents: PDF
- Media: MP4, MP3, WAV

**Parameters:**
- `path` - Path to asset file

**Response:** Binary file with appropriate MIME type

**Status Codes:**
- `200 OK` - File served
- `404 Not Found` - File doesn't exist

**Examples:**
```bash
# Get image
curl http://localhost:8080/assets/logo.svg

# Get PDF
curl http://localhost:8080/assets/manual.pdf -o manual.pdf
```

---

## Response Headers

All responses include standard headers:

```
Content-Type: text/html; charset=utf-8          (HTML pages)
Content-Type: text/plain; charset=utf-8         (Markdown, llms.txt)
Content-Type: application/json                  (Health check)
Content-Type: image/png                         (Images)
Content-Type: application/pdf                   (PDFs)
...
```

---

## Error Responses

### 404 Not Found

File or page doesn't exist.

**Response:**
```json
{
  "detail": "File not found"
}
```

### 500 Internal Server Error

Server error during processing.

**Response:**
```json
{
  "detail": "Error reading file: [error message]"
}
```

---

## Caching Behavior

### Cached Endpoints

These endpoints use intelligent caching:

| Endpoint | Cache Duration | Cache Key |
|----------|----------------|-----------|
| `GET /{path}.html` | Until server restart | File path |
| `GET /llms.txt` | Until server restart | `llms.txt` |
| `GET /llms-full.txt` | Until server restart | `llms-full.txt` |

### Non-Cached Endpoints

These endpoints are always fresh:

- `GET /health` - Real-time status
- `GET /{path}.md` - Original source
- `GET /{path}` (assets) - Static files

### Cache Invalidation

Cache is cleared on:
- Server restart
- Manual cache directory deletion
- File modification (in development with DEBUG=true)

---

## Rate Limiting

No rate limiting by default.

For production, use a reverse proxy (nginx, caddy) with rate limiting:

```nginx
limit_req_zone $binary_remote_addr zone=docs:10m rate=10r/s;

server {
    location / {
        limit_req zone=docs burst=20;
        proxy_pass http://localhost:8080;
    }
}
```

---

## CORS

CORS is not configured by default.

To enable CORS for API consumption:

```python
# Add to main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

---

## Authentication

No authentication by default.

For private documentation, use:

1. **Reverse Proxy Auth** (nginx, caddy)
2. **VPN/Firewall** (network-level)
3. **Custom Middleware** (FastAPI)

Example nginx basic auth:

```nginx
server {
    location / {
        auth_basic "Documentation";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://localhost:8080;
    }
}
```

---

## URL Structure

The server follows these URL patterns:

```
/                              → Redirects to /index.html
/index.html                    → Rendered homepage
/index.md                      → Raw markdown
/page.html                     → Rendered page
/page.md                       → Raw markdown
/folder/page.html              → Nested rendered page
/folder/page.md                → Nested raw markdown
/assets/image.png              → Static asset
/llms.txt                      → AI index
/llms-full.txt                 → Full content
/health                        → Health check
```

---

## Content Negotiation

The server doesn't use `Accept` headers. Instead, the URL extension determines the response:

- `.html` → Rendered HTML
- `.md` → Raw markdown
- Other → File type based on extension

---

## Examples

### Get Homepage HTML

```bash
curl http://localhost:8080/index.html
```

### Get Raw Markdown

```bash
curl http://localhost:8080/api/endpoints.md
```

### Download All Docs for AI

```bash
curl http://localhost:8080/llms-full.txt -o all-docs.txt
```

### Check Server Health

```bash
curl http://localhost:8080/health | jq .
```

### Get Specific Asset

```bash
curl http://localhost:8080/assets/logo.svg -o logo.svg
```

---

## Integration Examples

### Python

```python
import requests

# Get rendered page
response = requests.get("http://localhost:8080/index.html")
html = response.text

# Get raw markdown
response = requests.get("http://localhost:8080/index.md")
markdown = response.text

# Get AI index
response = requests.get("http://localhost:8080/llms.txt")
llms_txt = response.text
```

### JavaScript/Node

```javascript
// Fetch rendered page
const response = await fetch('http://localhost:8080/index.html');
const html = await response.text();

// Fetch markdown
const mdResponse = await fetch('http://localhost:8080/index.md');
const markdown = await mdResponse.text();
```

### cURL

```bash
# Get page and save
curl http://localhost:8080/page.html -o page.html

# Get all docs
curl http://localhost:8080/llms-full.txt -o docs.txt

# Check if page exists
curl -I http://localhost:8080/page.html
```

---

## Performance

### Response Times

| Endpoint Type | First Request | Cached |
|---------------|---------------|--------|
| Rendered HTML | 50-100ms | <5ms |
| Raw Markdown | <10ms | <10ms |
| LLMs.txt | 100-200ms | <5ms |
| Assets | <5ms | <5ms |

### Optimization Tips

1. Use caching (enabled by default)
2. Serve static assets via CDN
3. Use reverse proxy caching
4. Enable gzip compression
5. Minimize markdown files

---

## Security

### Built-in Protection

✅ Path traversal prevention  
✅ File type validation  
✅ UTF-8 encoding enforcement  
✅ Safe path resolution  

### Additional Security

Consider adding:

- HTTPS (via reverse proxy)
- Rate limiting
- Authentication
- CSP headers
- CORS configuration

---

## Next Steps

- **[Configuration](../configuration.md)** - Environment variables
- **[Deployment](../deployment/docker.md)** - Production deployment
- **[Examples](../examples/advanced.md)** - Integration examples
