# C5P Documentation Server - Technical Specification

**Version:** 2.0 (KLO-642)  
**Last Updated:** 2026-01-30  
**Status:** Production Ready

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [API Endpoints Reference](#api-endpoints-reference)
3. [LLMs.txt Specification Implementation](#llmstxt-specification-implementation)
4. [Markdown Processing Pipeline](#markdown-processing-pipeline)
5. [Caching Architecture](#caching-architecture)
6. [Security Model](#security-model)
7. [Configuration](#configuration)
8. [Directory Structure](#directory-structure)
9. [Performance Characteristics](#performance-characteristics)
10. [Testing Strategy](#testing-strategy)
11. [Deployment](#deployment)
12. [Maintenance and Operations](#maintenance-and-operations)

---

## Architecture Overview

### Purpose and Scope

The C5P Documentation Server is a lightweight FastAPI-based application designed to serve markdown documentation with:
- Dual format routing (raw markdown `.md` and rendered HTML `.html`)
- AI assistant integration via llms.txt specification
- Security-first design with strict directory boundaries
- High-performance disk-based caching
- Nuxt UI-inspired modern design

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | FastAPI | 0.117.1 | Async web framework |
| **Server** | Uvicorn | 0.32.1 | ASGI server |
| **Markdown** | Python-Markdown | 3.7 | Markdown processing |
| **Syntax Highlighting** | Pygments | 2.18.0 | Code block styling |
| **Templating** | Jinja2 | 3.1.4 | HTML template engine |
| **Python** | 3.13+ | 3.13.1 | Runtime |
| **Container** | Docker | Latest | Deployment |

### Design Philosophy

1. **Security First**: Strict path validation, no authentication needed
2. **Performance Focused**: Disk-based caching, optimized rendering
3. **AI-Friendly**: Implements llms.txt specification for LLM consumption
4. **Developer Experience**: Nuxt UI-inspired design, clear documentation
5. **Simplicity**: Single configurable root, minimal dependencies

### Deployment Target

- **Platform**: DigitalOcean App Platform
- **Port**: 8080 (standard for DigitalOcean)
- **Health Checks**: `/health` endpoint
- **Cache**: On-disk persistent cache
- **Content**: Baked into Docker image at build time

---

## API Endpoints Reference

### Endpoint Summary

| Endpoint | Method | Content-Type | Description | Caching |
|----------|--------|--------------|-------------|---------|
| `/` | GET | redirect | Redirects to `/index.html` | No |
| `/{page}.html` | GET | text/html | Rendered HTML with navigation | Yes (disk) |
| `/{page}.md` | GET | text/markdown | Raw markdown content | No |
| `/llms.txt` | GET | text/plain | LLM-friendly documentation index | Yes (disk) |
| `/llms-full.txt` | GET | text/plain | Expanded documentation with all pages | Yes (disk) |
| `/assets/{file}` | GET | varies | Static assets (images, PDFs, etc.) | No |
| `/health` | GET | application/json | Health check endpoint | No |

---

### Endpoint Details

#### GET `/`

**Purpose**: Root redirect to main documentation page

**Request**: None

**Response**: 
- Status: 302 Found
- Location: `/index.html`

**Example**:
```bash
curl -I http://localhost:8080/
# Location: /index.html
```

---

#### GET `/{page}.html`

**Purpose**: Serve rendered HTML documentation with navigation

**Request**:
- Path parameter: `page` (filename without .html extension)
- Example: `/01_snelle_uitleg.html`

**Processing**:
1. Convert `.html` path to `.md` path
2. Validate file exists in DOCS_ROOT
3. Check disk cache for rendered HTML
4. If cache miss:
   - Read markdown file
   - Convert `.md` links to `.html` links
   - Render markdown to HTML
   - Parse sidebar.md and topbar.md for navigation
   - Extract table of contents
   - Apply HTML template with C5P styling
   - Cache to disk
5. Return HTML response

**Response**:
- Status: 200 OK
- Content-Type: text/html; charset=utf-8
- Body: Rendered HTML with navigation

**Errors**:
- 404: File not found
- 500: Error reading or rendering file

**Cache**: Yes - stored in `CACHE_ROOT/{path}.html`

**Example**:
```bash
curl http://localhost:8080/01_snelle_uitleg.html
# Returns: Full HTML page with sidebar, topbar, and content
```

---

#### GET `/{page}.md`

**Purpose**: Serve raw markdown content for AI/LLM processing

**Request**:
- Path parameter: `page` (filename with .md extension)
- Example: `/01_snelle_uitleg.md`

**Processing**:
1. Validate file exists in DOCS_ROOT
2. Read markdown file
3. Return as plain text

**Response**:
- Status: 200 OK
- Content-Type: text/markdown; charset=utf-8
- Body: Raw markdown content

**Errors**:
- 404: File not found
- 500: Error reading file

**Cache**: No (raw content, minimal overhead)

**Example**:
```bash
curl http://localhost:8080/01_snelle_uitleg.md
# Returns: Raw markdown content
```

---

#### GET `/llms.txt`

**Purpose**: Provide LLM-friendly documentation index (llmstxt.org specification)

**Request**: None

**Processing Strategy**:
1. Check disk cache for `llms.txt`
2. If cache hit: Return cached content
3. If cache miss:
   - **PRIMARY**: Check if `DOCS_ROOT/llms.txt` exists
     - If exists: Read curated file (manual override)
     - Log: "Serving curated llms.txt from DOCS_ROOT"
   - **FALLBACK**: Generate dynamically
     - Read `DOCS_ROOT/sidebar.md` (if exists)
     - Read `DOCS_ROOT/index.md`
     - Concatenate: `sidebar.md` + `\n\n---\n\n` + `index.md`
     - Log: "llms.txt not found, generating from sidebar.md + index.md"
   - Transform all relative `.md` links to absolute URLs using BASE_URL
   - Cache to disk
4. Return as plain text

**Response**:
- Status: 200 OK
- Content-Type: text/plain; charset=utf-8
- Body: Documentation index with absolute URLs

**BASE_URL Behavior**:
- If `BASE_URL` env var set: Use it
- If not set: Auto-detect from `request.base_url`
- Example: `https://support.c5p.app`

**Link Transformation**:
- Input: `[Title](file.md)` or `[Title](file.md#anchor)`
- Output: `[Title](https://support.c5p.app/file.md)` or `[Title](https://support.c5p.app/file.md#anchor)`

**Cache**: Yes - stored in `CACHE_ROOT/llms.txt`

**Example**:
```bash
curl http://localhost:8080/llms.txt
# Returns: Documentation index with absolute URLs
```

**Format** (llmstxt.org compliant):
```markdown
# C5P Applicatie Handleiding

> C5P is een Nederlandse risicomanagement platform...

## Aan de slag

- [Snelle Uitleg](https://support.c5p.app/01_snelle_uitleg.md): Overzicht
- [Login](https://support.c5p.app/02_login.md): Inloggen en navigatie

## CROW500 functionaliteit

- [Risico's](https://support.c5p.app/04_07_risicos.md): Risicoanalyse
...
```

---

#### GET `/llms-full.txt`

**Purpose**: Provide expanded documentation with all linked page content for LLMs

**Request**: None

**Processing**:
1. Check disk cache for `llms-full.txt`
2. If cache hit: Return cached content
3. If cache miss:
   - Call `/llms.txt` endpoint internally (may use its cache)
   - Parse all absolute `.md` URLs from llms.txt content
   - For each unique URL:
     - Extract relative path from URL
     - Read markdown file from DOCS_ROOT
     - Wrap in XML-style structure:
       ```
       <url>https://support.c5p.app/file.md</url>
       <content>
       ...markdown content...
       </content>
       ```
   - Concatenate: llms.txt + all wrapped pages
   - Cache to disk
4. Return as plain text

**Response**:
- Status: 200 OK
- Content-Type: text/plain; charset=utf-8
- Body: llms.txt + expanded content for all linked pages

**Cache**: Yes - stored in `CACHE_ROOT/llms-full.txt`

**Performance**: ~500-1000ms uncached (depends on page count), <10ms cached

**Example**:
```bash
curl http://localhost:8080/llms-full.txt
# Returns: Full documentation context for LLMs
```

**Format** (FastHTML/Claude compatible):
```
# C5P Applicatie Handleiding
...llms.txt content...

<url>https://support.c5p.app/01_snelle_uitleg.md</url>
<content>
# Snelle Uitleg
...full markdown content...
</content>

<url>https://support.c5p.app/02_login.md</url>
<content>
# Login en Navigatie
...full markdown content...
</content>
```

---

#### GET `/assets/{file}`

**Purpose**: Serve static assets (images, PDFs, videos, audio)

**Request**:
- Path parameter: `file` (filename with extension in assets directory)
- Example: `/assets/c5p_logo.svg`

**Processing**:
1. Validate file exists in `DOCS_ROOT/assets/`
2. Determine media type from extension
3. Return file with appropriate Content-Type header

**Response**:
- Status: 200 OK
- Content-Type: Varies by file type
- Body: File content

**Supported File Types**:
| Extension | Media Type |
|-----------|------------|
| .png | image/png |
| .jpg, .jpeg | image/jpeg |
| .gif | image/gif |
| .svg | image/svg+xml |
| .pdf | application/pdf |
| .mp4 | video/mp4 |
| .mp3 | audio/mpeg |
| .wav | audio/wav |

**Cache**: No (handled by browser caching)

**Example**:
```bash
curl http://localhost:8080/assets/c5p_logo.svg
# Returns: SVG file
```

---

#### GET `/health`

**Purpose**: Health check for container orchestration

**Request**: None

**Response**:
```json
{
  "status": "healthy",
  "docs_root": "/app/docs",
  "cache_root": "/app/cache",
  "debug": false
}
```

**Status**: Always 200 OK (if server is running)

**Usage**:
- Docker health checks
- Load balancer health probes
- Monitoring systems

**Example**:
```bash
curl http://localhost:8080/health
# {"status":"healthy","docs_root":"/app/docs",...}
```

---

## LLMs.txt Specification Implementation

### Overview

Implements the [llmstxt.org specification](https://llmstxt.org/) to enable AI coding assistants (Cursor, GitHub Copilot, Claude, ChatGPT) to effectively consume documentation.

### Specification Compliance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| `/llms.txt` at root | ✅ | Endpoint implemented |
| Markdown format | ✅ | Plain text markdown |
| H1 title | ✅ | Document title |
| Blockquote summary | ✅ | In curated file |
| Organized sections | ✅ | H2 sections |
| Absolute URLs | ✅ | Link transformation |

### Strategy: PRIMARY/FALLBACK

#### PRIMARY Strategy (Recommended)

**When**: Curated `llms.txt` file exists in DOCS_ROOT

**Behavior**:
1. Read `DOCS_ROOT/llms.txt` directly
2. Transform relative links to absolute
3. Cache and serve

**Advantages**:
- Full control over content
- Optimized for LLM consumption
- Can add custom descriptions
- Follows llmstxt.org format exactly

**Example** (curated llms.txt):
```markdown
# C5P Applicatie Handleiding

> C5P is een Nederlandse risicomanagement platform voor bouwprojecten met ondergrondse infrastructuur, gebaseerd op de CROW500 methodiek.

De applicatie ondersteunt de volledige workflow...

## Aan de slag

- [Snelle Uitleg](01_snelle_uitleg.md): Overzicht van C5P applicatie en CROW500 methodiek
- [Login en Navigatie](02_login_en_navigatie.md): Account aanvragen, inloggen en basis navigatie

## CROW500 kern functionaliteit

- [Risico's](04_07_risicos.md): Risicoidentificatie en -analyse volgens CROW500
...
```

#### FALLBACK Strategy (Automatic)

**When**: No curated `llms.txt` file in DOCS_ROOT

**Behavior**:
1. Read `DOCS_ROOT/sidebar.md` (if exists)
2. Read `DOCS_ROOT/index.md`
3. Concatenate: `sidebar.md` + `\n\n---\n\n` + `index.md`
4. Transform relative links to absolute
5. Cache and serve

**Advantages**:
- Automatic generation
- No manual maintenance
- Uses existing navigation structure

**Example** (generated):
```markdown
# Navigatie C5P Handleiding

* [Snelle Uitleg](01_snelle_uitleg.md)
* [Login en Navigatie](02_login_en_navigatie.md)
...

---

# C5P Applicatie - Nederlandse Handleiding

Deze handleiding helpt je om effectief te werken...
```

### Link Transformation Algorithm

**Purpose**: Convert relative markdown links to absolute URLs

**Implementation**:
```python
def transform_relative_to_absolute(markdown_content: str, base_url: str) -> str:
    """
    Transform relative .md links to absolute URLs.
    
    Pattern: [text](path.md) or [text](path.md#anchor)
    Output: [text](https://base_url/path.md) or [text](https://base_url/path.md#anchor)
    """
    pattern = r'\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)'
    
    def replace_link(match):
        title = match.group(1)
        rel_path = match.group(2)
        
        # Skip already absolute URLs
        if rel_path.startswith('http://') or rel_path.startswith('https://'):
            return match.group(0)
        
        # Create absolute URL
        abs_url = f"{base_url.rstrip('/')}/{rel_path.lstrip('/')}"
        return f"[{title}]({abs_url})"
    
    return re.sub(pattern, replace_link, markdown_content)
```

**Test Cases**:
- `[Title](file.md)` → `[Title](https://support.c5p.app/file.md)`
- `[Title](file.md#section)` → `[Title](https://support.c5p.app/file.md#section)`
- `[External](https://example.com/file.md)` → No change (already absolute)

### BASE_URL Configuration

**Environment Variable**: `BASE_URL`

**Behavior**:
- If set: Use the provided base URL
- If not set: Auto-detect from `request.base_url`

**Production Setup**:
```bash
BASE_URL=https://support.c5p.app
```

**Development**:
```bash
# Auto-detects as http://localhost:8080
# No BASE_URL needed
```

### AI Assistant Integration

#### Cursor

**Discovery**: Automatic (follows llmstxt.org convention)

**Usage**:
```
"Check the C5P docs at https://support.c5p.app/llms.txt"
"What are the main features of C5P?"
"How do I create a new initiative?"
```

#### Claude/ChatGPT

**Discovery**: Manual (provide URL)

**Usage**:
```
"Here's the documentation: https://support.c5p.app/llms-full.txt"
"Based on the C5P documentation, explain the CROW500 workflow"
```

---

## Markdown Processing Pipeline

### Overview

Markdown files are processed through a multi-stage pipeline to produce rendered HTML with navigation, styling, and syntax highlighting.

### Pipeline Stages

```
┌─────────────────┐
│ Raw Markdown    │
│ (file.md)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Link Conversion │ Convert [text](file.md) → [text](file.html)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Markdown Parse  │ Python-Markdown with extensions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTML Generation │ Convert to HTML with syntax highlighting
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TOC Extraction  │ Extract headings for table of contents
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Navigation Parse│ Parse sidebar.md and topbar.md
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Template Apply  │ Insert into HTML template with C5P styling
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cache & Serve   │ Save to disk cache, return to client
└─────────────────┘
```

### Markdown Extensions

Configured extensions for enhanced markdown processing:

```python
markdown_extensions = [
    'codehilite',           # Syntax highlighting
    'toc',                  # Table of contents
    'tables',               # Table support
    'fenced_code',          # ``` code blocks
    'footnotes',            # [^1] footnote syntax
    'attr_list',            # {: .class} attributes
    'def_list',             # Definition lists
    'abbr',                 # Abbreviations
    'pymdownx.superfences', # Advanced code blocks
    'pymdownx.tasklist',    # [x] task lists
    'pymdownx.highlight',   # Code highlighting
    'pymdownx.inlinehilite',# Inline code highlighting
]
```

### Extension Configuration

```python
markdown_extension_configs = {
    'codehilite': {
        'css_class': 'highlight',
        'use_pygments': True,
    },
    'toc': {
        'permalink': True,        # Add anchor links
        'toc_depth': 3,           # H1-H3
        'permalink_title': '🔗'   # Link icon
    },
    'pymdownx.superfences': {
        'custom_fences': [
            {
                'name': 'mermaid',
                'class': 'mermaid',
                'format': lambda source: f'<div class="mermaid">{source}</div>'
            }
        ]
    },
    'pymdownx.tasklist': {
        'custom_checkbox': True,  # Custom checkbox styling
    },
}
```

### Link Conversion

**Purpose**: Convert markdown links from `.md` to `.html` for rendered HTML mode

**Implementation**:
```python
def convert_md_links_to_html(content: str) -> str:
    """Convert markdown links from .md to .html for rendered HTML mode."""
    pattern = r'\[([^\]]+)\]\(([^)]+\.md)\)'
    
    def replace_link(match):
        text = match.group(1)
        link = match.group(2)
        html_link = link.replace('.md', '.html')
        return f'[{text}]({html_link})'
    
    return re.sub(pattern, replace_link, content)
```

**Example**:
- Input: `[Go to page](01_snelle_uitleg.md)`
- Output: `[Go to page](01_snelle_uitleg.html)`

### Syntax Highlighting

**Library**: Pygments

**Supported Languages**: 500+ languages including:
- Python, JavaScript, TypeScript
- Java, C++, C#, Go, Rust
- HTML, CSS, SCSS
- SQL, Bash, YAML, JSON
- And many more

**Styling**: Integrated with C5P brand colors

**Example**:
````markdown
```python
def hello_world():
    print("Hello, C5P!")
```
````

Renders with syntax highlighting and line numbers.

### Table of Contents (TOC) Extraction

**Process**:
1. Parse rendered HTML for heading tags `<h1>` to `<h6>`
2. Extract heading text and `id` attributes
3. Build hierarchical structure based on heading levels
4. Generate TOC sidebar with anchor links

**Example** (extracted TOC):
```python
toc_items = [
    {'id': 'introduction', 'title': 'Introduction', 'level': 1},
    {'id': 'getting-started', 'title': 'Getting Started', 'level': 2},
    {'id': 'installation', 'title': 'Installation', 'level': 3},
]
```

### Navigation Integration

**Sidebar** (`sidebar.md`):
- Parsed into hierarchical navigation structure
- Supports top-level and nested items
- Active state tracking for current page
- Nuxt UI-inspired styling

**Topbar** (`topbar.md`):
- Parsed into left/middle/right sections
- Supports logo, text, and links
- External links open in new tab
- Responsive design

---

## Caching Architecture

### Overview

The documentation server implements a two-tier caching system:
1. **HTML Caching**: Rendered HTML pages
2. **LLMs Caching**: Generated llms.txt files

Both use on-disk persistent caching for optimal performance in containerized environments.

### Cache Strategy: Write-Through

```
┌──────────┐
│ Request  │
└────┬─────┘
     │
     ▼
┌─────────────┐
│ Check Cache │───Yes───▶ Return Cached Content
└────┬────────┘          (< 10ms)
     │ No
     ▼
┌─────────────┐
│ Generate    │
│ Content     │
└────┬────────┘
     │
     ▼
┌─────────────┐
│ Save to     │
│ Cache       │
└────┬────────┘
     │
     ▼
┌─────────────┐
│ Return      │
│ Content     │
└─────────────┘
```

### HTML Caching

**Location**: `CACHE_ROOT/{relative_path}.html`

**Example**:
- Request: `/01_snelle_uitleg.html`
- Cache file: `__cache__/01_snelle_uitleg.html`

**Implementation**:
```python
async def get_cached_html(file_path: Path) -> Optional[str]:
    """Get cached HTML content if it exists."""
    try:
        relative_path = file_path.relative_to(DOCS_ROOT)
        cache_path = CACHE_ROOT / relative_path.with_suffix('.html')
        
        if cache_path.exists():
            return cache_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError, ValueError) as e:
        logger.debug(f"Cache read error: {e}")
    
    return None

async def save_cached_html(file_path: Path, html_content: str) -> None:
    """Save HTML content to cache."""
    try:
        relative_path = file_path.relative_to(DOCS_ROOT)
        cache_path = CACHE_ROOT / relative_path.with_suffix('.html')
        
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(html_content, encoding='utf-8')
        logger.debug(f"Cached HTML: {cache_path}")
    except (OSError, ValueError) as e:
        logger.debug(f"Cache write error: {e}")
```

### LLMs Caching

**Location**: `CACHE_ROOT/llms.txt` and `CACHE_ROOT/llms-full.txt`

**Implementation**:
```python
async def get_cached_llms(cache_file: str) -> Optional[str]:
    """Get cached llms content if it exists."""
    try:
        cache_path = CACHE_ROOT / cache_file
        
        if cache_path.exists():
            return cache_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError, ValueError) as e:
        logger.debug(f"Cache read error for {cache_file}: {e}")
    
    return None

async def save_cached_llms(cache_file: str, content: str) -> None:
    """Save llms content to cache."""
    try:
        cache_path = CACHE_ROOT / cache_file
        
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(content, encoding='utf-8')
        logger.debug(f"Cached llms file: {cache_path}")
    except (OSError, ValueError) as e:
        logger.debug(f"Cache write error for {cache_file}: {e}")
```

### Cache Invalidation

**Strategy**: Complete cache clearing on server startup

**Implementation** (lines 42-45 in main.py):
```python
# Clean cache directory on startup
if CACHE_ROOT.exists():
    import shutil
    shutil.rmtree(CACHE_ROOT)
    logger.info(f"🧹 Cleaned cache directory: {CACHE_ROOT.absolute()}")

CACHE_ROOT.mkdir(parents=True, exist_ok=True)
```

**Rationale**:
- Container content is static (baked at build time)
- No file modification monitoring needed
- Simple and reliable invalidation
- Ensures fresh cache after deployment

**Trigger**: Server restart or container restart

### Performance Characteristics

| Operation | Cached | Uncached | Notes |
|-----------|--------|----------|-------|
| HTML page | < 10ms | 50-100ms | Depends on page size |
| llms.txt | < 10ms | 50-100ms | Includes link transformation |
| llms-full.txt | < 10ms | 500-1000ms | Loads all linked pages |
| Static asset | N/A | 5-20ms | Browser caching recommended |

### Cache Storage

**Typical Size**:
- HTML files: ~5-50KB each
- llms.txt: ~5-10KB
- llms-full.txt: ~200-500KB (depends on page count)
- Total cache size: ~5-10MB for full documentation set

**Disk Space**: Minimal (< 10MB for typical documentation)

**Memory**: Cache files not kept in memory (read from disk on demand)

---

## Security Model

### Threat Model

**In Scope**:
- Directory traversal attacks (`../` in paths)
- Path injection attacks
- Unauthorized file access outside DOCS_ROOT
- Denial of service via large file requests

**Out of Scope**:
- Authentication (public documentation)
- Rate limiting (handled by reverse proxy)
- DDoS protection (handled by infrastructure)

### Path Validation

**Strategy**: Strict directory boundary enforcement

**Implementation**:
```python
def is_safe_path(path: str, base_path: Path) -> bool:
    """
    Validate that the requested path is within the allowed directory boundaries.
    Prevents directory traversal attacks.
    """
    try:
        # Resolve absolute paths
        abs_base = base_path.resolve()
        abs_path = (base_path / path).resolve()
        
        # Check if the resolved path is within the base directory
        import os
        return os.path.commonpath([abs_base, abs_path]) == str(abs_base)
    except (ValueError, OSError):
        return False
```

**Protection Against**:
- `../../../etc/passwd` → Rejected
- `..%2F..%2Fetc%2Fpasswd` → Rejected (URL decoded then validated)
- Symlink attacks → Resolved with `.resolve()`
- Absolute paths → Validated against base path

**Example**:
```python
# Valid paths
is_safe_path("01_snelle_uitleg.md", DOCS_ROOT)  # True
is_safe_path("assets/logo.svg", DOCS_ROOT)      # True

# Invalid paths (outside DOCS_ROOT)
is_safe_path("../../secret.txt", DOCS_ROOT)     # False
is_safe_path("/etc/passwd", DOCS_ROOT)          # False
```

### File Type Validation

**Allowed Extensions**:
- Documentation: `.md`
- Images: `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`
- Documents: `.pdf`
- Media: `.mp4`, `.mp3`, `.wav`

**Implicit Validation**: Files must exist in DOCS_ROOT to be served

**No Execution**: Server only serves static files, never executes uploaded content

### Access Control

**Philosophy**: Public documentation, no authentication

**Rationale**:
- Documentation is intended for public consumption
- No sensitive data in documentation files
- Simplifies deployment and maintenance

**Alternative**: If authentication needed in future, can be added at:
1. Reverse proxy level (nginx, Traefik)
2. API Gateway level (Kong, AWS API Gateway)
3. Application level (FastAPI middleware)

### Security Headers

**Recommended** (configured at reverse proxy):
```nginx
add_header X-Content-Type-Options "nosniff";
add_header X-Frame-Options "SAMEORIGIN";
add_header X-XSS-Protection "1; mode=block";
```

### Logging and Monitoring

**Logging Strategy**:
- Info: Successful requests, cache hits/misses
- Debug: Detailed processing steps
- Warning: Path validation failures
- Error: File read errors, rendering errors

**Example Logs**:
```
INFO: Serving cached HTML: /01_snelle_uitleg.html
INFO: Serving curated llms.txt from DOCS_ROOT
WARNING: Unsafe path requested: ../../secret.txt
ERROR: Error reading file /app/docs/missing.md: File not found
```

---

## Configuration

### Environment Variables

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DOCS_ROOT` | `./test_docs` (dev)<br>`/app/docs` (prod) | Root directory for documentation files | No |
| `CACHE_ROOT` | `./__cache__` (dev)<br>`/app/cache` (prod) | Directory for cached HTML and llms files | No |
| `BASE_URL` | Auto-detected | Base URL for absolute links in llms.txt | No |
| `DEBUG` | `false` | Enable debug mode with hot reload | No |
| `PORT` | `8080` | Server port | No |

### Configuration Details

#### DOCS_ROOT

**Purpose**: Root directory containing documentation files

**Format**: Absolute path to directory

**Default Behavior**:
- Development: `./test_docs` (relative to project root)
- Production: `/app/docs` (Docker container path)

**Auto-detection**:
```python
default_docs = "/app/docs" if Path("/app").exists() else "./test_docs"
DOCS_ROOT = Path(os.getenv("DOCS_ROOT", default_docs))
```

**Example**:
```bash
# Custom docs location
DOCS_ROOT=/custom/docs/path uv run python -m docs_server
```

#### CACHE_ROOT

**Purpose**: Directory for storing cached HTML and llms files

**Format**: Absolute path to directory

**Default Behavior**:
- Development: `./__cache__` (relative to project root)
- Production: `/app/cache` (Docker container path)

**Auto-detection**:
```python
default_cache = "/app/cache" if Path("/app").exists() else "./__cache__"
CACHE_ROOT = Path(os.getenv("CACHE_ROOT", default_cache))
```

**Cache Lifecycle**:
1. Created on startup if doesn't exist
2. Cleared completely on startup
3. Populated on first requests
4. Persists until next restart

**Example**:
```bash
# Custom cache location
CACHE_ROOT=/tmp/docs-cache uv run python -m docs_server
```

#### BASE_URL

**Purpose**: Base URL for generating absolute links in llms.txt

**Format**: Full URL with protocol (http:// or https://)

**Default Behavior**: Auto-detect from `request.base_url`

**Production Setup** (Recommended):
```bash
BASE_URL=https://support.c5p.app
```

**Development**: Not needed (auto-detects as http://localhost:8080)

**Usage in Code**:
```python
base_url = BASE_URL if BASE_URL else str(request.base_url).rstrip('/')
```

**Example**:
```bash
# Explicit BASE_URL
BASE_URL=https://support.c5p.app uv run python -m docs_server
```

#### DEBUG

**Purpose**: Enable debug mode with hot reload

**Format**: String `"true"` or `"false"` (case-insensitive)

**Default**: `false`

**When Enabled**:
- Hot reload on code changes
- Debug-level logging
- Detailed error messages
- Uvicorn reload mode

**Example**:
```bash
# Enable debug mode
DEBUG=true uv run python -m docs_server
```

#### PORT

**Purpose**: HTTP server port

**Format**: Integer (1-65535)

**Default**: `8080`

**DigitalOcean Standard**: 8080

**Example**:
```bash
# Custom port
PORT=3000 uv run python -m docs_server
```

### Docker Environment Variables

**Dockerfile Configuration** (lines 8-12):
```dockerfile
ENV PYTHONPATH=/app/src
ENV DOCS_ROOT=/app/docs
ENV CACHE_ROOT=/app/cache
ENV PORT=8080
ENV DEBUG=false
```

**Runtime Override**:
```bash
docker run -d \
  -e BASE_URL=https://support.c5p.app \
  -e DEBUG=false \
  -p 8080:8080 \
  c5p-docs
```

---

## Directory Structure

### Application Structure (Docker Container)

```
/app/
├── src/                          # Application source code
│   └── docs_server/
│       ├── __init__.py
│       ├── __main__.py           # CLI entry point
│       └── main.py               # FastAPI application (1388 lines)
│
├── docs/                         # DOCS_ROOT (documentation content)
│   ├── index.md                  # Main page
│   ├── sidebar.md                # Navigation config
│   ├── topbar.md                 # Top navigation config
│   ├── llms.txt                  # Curated LLM index (optional)
│   ├── 01_snelle_uitleg.md       # Quick start guide
│   ├── 02_login_en_navigatie.md  # Login guide
│   ├── 03_globaal.md             # Global overview
│   ├── 03_01_rollen_en_permissies.md
│   ├── 04_01_initiatief_dashboard.md
│   ├── 04_07_risicos.md          # Risk management
│   ├── 04_08_maatregelen.md      # Mitigation measures
│   ├── 04_09_werkinstructies.md  # Work instructions
│   ├── ... (20+ more .md files)
│   └── assets/                   # Static assets
│       ├── c5p_logo.svg
│       ├── c5p_logo.png
│       ├── *.png (18 images)
│       └── *.pdf (2 PDFs)
│
├── cache/                        # CACHE_ROOT (generated at runtime)
│   ├── index.html                # Cached rendered pages
│   ├── 01_snelle_uitleg.html
│   ├── 02_login_en_navigatie.html
│   ├── ... (generated on first access)
│   ├── llms.txt                  # Cached LLM index
│   └── llms-full.txt             # Cached expanded LLM context
│
├── .venv/                        # Python virtual environment
│   └── ...
│
├── pyproject.toml                # Python project config
├── uv.lock                       # Dependency lock file
└── README.md                     # Project documentation
```

### Content Organization

**Documentation Files** (25 files, ~192KB):
```
docs/
├── 01-09: Getting started, login, navigation
├── 03_XX: Global level (roles, organizations, contacts)
├── 04_XX: Initiative level (areas, risks, mitigations, instructions)
├── index.md: Main landing page
├── sidebar.md: Navigation structure
├── topbar.md: Top bar configuration
└── llms.txt: LLM-friendly index (curated)
```

**Assets** (22 files, ~1.5MB):
```
docs/assets/
├── c5p_logo.svg (brand logo)
├── c5p_logo.png (brand logo)
├── global-*.png (global level screenshots)
├── initiative-*.png (initiative level screenshots)
└── *.pdf (example reports)
```

### Cache Organization

**Generated at Runtime**:
```
cache/
├── index.html                    # 15-25KB
├── 01_snelle_uitleg.html        # 10-20KB
├── ...                           # One file per .md file
├── llms.txt                      # 5-10KB
└── llms-full.txt                 # 200-500KB
```

**Total Cache Size**: ~5-10MB for full documentation set

### Development Structure

**Outside Container** (Repository):
```
07_docs_server/
├── src/docs_server/              # Source code
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_llms_implementation.py   # Unit tests
│   ├── test_llms_endpoints.py        # Integration tests
│   └── test_real_content.py          # Real content test
├── test_docs/                    # Test documentation
├── pyproject.toml                # Project config
├── uv.lock                       # Dependencies
├── Dockerfile                    # Container config
├── README.md                     # User documentation
├── SPECS.md                      # This file (technical spec)
└── *.md                          # Implementation reports
```

---

## Performance Characteristics

### Response Times

| Endpoint | Cached | Uncached | Notes |
|----------|--------|----------|-------|
| `/index.html` | < 10ms | 50-100ms | With navigation |
| `/{page}.html` | < 10ms | 50-100ms | With navigation |
| `/{page}.md` | N/A | 5-20ms | Direct file read |
| `/llms.txt` | < 10ms | 50-100ms | With link transformation |
| `/llms-full.txt` | < 10ms | 500-1000ms | Loads ~25 pages |
| `/assets/{file}` | N/A | 5-20ms | Direct file serve |
| `/health` | < 5ms | < 5ms | JSON response |

### Cold Start Performance

**First Request After Deployment**:
- Server startup: ~2-3 seconds
- Cache directory creation: < 100ms
- First page render: 50-100ms
- Subsequent pages: < 10ms (cached)

**Warmup Strategy** (Optional):
```bash
# After deployment, pre-populate cache
curl https://support.c5p.app/index.html > /dev/null
curl https://support.c5p.app/llms.txt > /dev/null
curl https://support.c5p.app/llms-full.txt > /dev/null
```

### Memory Usage

**Typical** (Container):
- Base Python process: ~50MB
- FastAPI + Uvicorn: ~100MB
- Markdown processing: +20-50MB (transient)
- Total: ~150-200MB

**Peak** (During llms-full.txt generation):
- Temporarily loads all pages into memory
- Peak: ~250-300MB
- Returns to baseline after response

**Cache**: Not kept in memory (read from disk on demand)

### CPU Usage

**Idle**: < 1% CPU

**Under Load**:
- Cached requests: < 5% CPU
- Uncached requests: 10-30% CPU (markdown processing)
- llms-full.txt generation: 30-50% CPU (brief spike)

**Concurrency**: FastAPI async handles multiple requests efficiently

### Scalability

**Single Instance**:
- Handles ~100-500 requests/second (cached)
- Handles ~10-50 requests/second (uncached)

**Horizontal Scaling**:
- Stateless application
- Cache is per-instance (no shared state needed)
- Can deploy multiple instances behind load balancer

**Bottlenecks**:
- Markdown processing (CPU-bound)
- Disk I/O for cache writes (minimal)

### Optimization Strategies

**Current**:
1. Disk caching for rendered HTML
2. Disk caching for llms.txt files
3. Async request handling
4. Cache invalidation on startup only

**Future Enhancements** (if needed):
1. In-memory LRU cache layer (reduce disk reads)
2. Pre-rendering at build time (eliminate cold starts)
3. CDN integration (offload static assets)
4. Compression (gzip/brotli for responses)

---

## Testing Strategy

### Test Pyramid

```
        ▲
       ╱ ╲
      ╱   ╲
     ╱ E2E ╲        Manual testing with browser/Cursor
    ╱───────╲
   ╱         ╲
  ╱Integration╲     test_llms_endpoints.py (8 tests)
 ╱─────────────╲
╱               ╲
╱     Unit       ╲   test_llms_implementation.py (6 tests)
╱─────────────────╲
```

### Unit Tests

**File**: `tests/test_llms_implementation.py`

**Purpose**: Test individual functions in isolation

**Coverage**:
1. ✅ Simple relative link transformation
2. ✅ Link with anchor transformation
3. ✅ Already absolute URL (no change)
4. ✅ Multiple links in content
5. ✅ BASE_URL with trailing slash
6. ✅ Path with leading slash

**Example**:
```python
def test_transform_relative_to_absolute():
    base_url = "https://support.c5p.app"
    
    # Test simple link
    input_text = "[Snelle Uitleg](01_snelle_uitleg.md)"
    result = transform_relative_to_absolute(input_text, base_url)
    expected = "[Snelle Uitleg](https://support.c5p.app/01_snelle_uitleg.md)"
    assert result == expected
```

**Run**:
```bash
cd 07_docs_server
python3 tests/test_llms_implementation.py
```

**Expected Output**: `✅ All tests passed! (6/6)`

### Integration Tests

**File**: `tests/test_llms_endpoints.py`

**Purpose**: Test endpoint behavior and integration points

**Coverage**:
1. ✅ /llms.txt format validation
2. ✅ Absolute URL transformation
3. ✅ BASE_URL environment variable handling
4. ✅ Caching behavior
5. ⚠️ Link resolution (24/26 files)
6. ✅ /llms-full.txt format
7. ✅ Performance estimation
8. ✅ Cursor AI consumption format

**Example**:
```python
def test_llms_txt_format():
    """Test /llms.txt format with curated file"""
    curated_path = Path("../04_documentation/end_user_v1/llms.txt")
    content = curated_path.read_text(encoding='utf-8')
    
    # Validate format
    assert content.startswith("# ")  # Has H1 title
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md[^)]*)\)', content)
    assert len(md_links) > 0  # Contains links
```

**Run**:
```bash
cd 07_docs_server
python3 tests/test_llms_endpoints.py
```

**Expected Output**: `7/8 tests passed (87.5%)`

### Manual Testing

**Browser Testing**:
```bash
# Start server
uv run python -m docs_server

# Open in browser
open http://localhost:8080/

# Test navigation
# - Click sidebar links
# - Test topbar links
# - Verify table of contents
# - Check mobile responsiveness
```

**Endpoint Testing**:
```bash
# Test HTML endpoint
curl http://localhost:8080/01_snelle_uitleg.html

# Test raw markdown
curl http://localhost:8080/01_snelle_uitleg.md

# Test llms.txt
curl http://localhost:8080/llms.txt

# Test llms-full.txt
curl http://localhost:8080/llms-full.txt | head -100

# Test health check
curl http://localhost:8080/health
```

**BASE_URL Testing**:
```bash
# With explicit BASE_URL
BASE_URL=https://support.c5p.app uv run python -m docs_server

# Verify absolute URLs
curl http://localhost:8080/llms.txt | grep "https://support.c5p.app"
```

**Cursor AI Testing**:
```
1. Open Cursor
2. Ask: "Check the C5P docs at http://localhost:8080/llms.txt"
3. Ask: "What are the main features of C5P?"
4. Verify Cursor can access and understand the documentation
```

### Docker Testing

**Build and Run**:
```bash
# Build image
./docker-build.sh

# Run container
./docker-run.sh

# Or with BASE_URL
docker run -d -p 8080:8080 \
  -e BASE_URL=https://support.c5p.app \
  --name c5p-docs-server c5p-docs
```

**Verify Container**:
```bash
# Check health
curl http://localhost:8080/health

# Check logs
docker logs c5p-docs-server

# Verify content
docker exec c5p-docs-server ls -la /app/docs/
docker exec c5p-docs-server cat /app/docs/llms.txt | head -20
```

### Performance Testing

**Simple Load Test**:
```bash
# Test cached performance
for i in {1..100}; do
  curl -s http://localhost:8080/index.html > /dev/null
done

# Test uncached performance (restart server between runs)
curl -s http://localhost:8080/01_snelle_uitleg.html > /dev/null
```

**Cache Performance**:
```bash
# First request (cache miss)
time curl http://localhost:8080/llms-full.txt > /dev/null
# real    0m0.523s

# Second request (cache hit)
time curl http://localhost:8080/llms-full.txt > /dev/null
# real    0m0.008s
```

### Continuous Integration

**Recommended CI Pipeline**:
1. **Lint**: `ruff check src/ && ruff format --check src/`
2. **Unit & Integration Tests**: `pytest tests/ -v`
3. **Docker Build**: `docker build -f Dockerfile .`
4. **Docker Test**: Run container and test endpoints
5. **Security Scan**: `docker scan c5p-docs`

**GitLab CI Configuration** (`.gitlab-ci.yml`):
```yaml
lint-docs-server:
  stage: test
  image: python:3.13-slim
  script:
    - cd 07_docs_server
    - pip install --quiet ruff
    - ruff check src/
    - ruff format --check src/
  only:
    - merge_requests
    - main
    - tags

test-docs-server:
  stage: test
  image: python:3.13-slim
  script:
    - cd 07_docs_server
    - pip install --quiet pytest
    - pytest tests/ -v
  only:
    - merge_requests
    - main
    - tags
```

---

## Deployment

### Docker Build

**Build Context**: Repository root

**Dockerfile Location**: `07_docs_server/Dockerfile`

**Build Command**:
```bash
# From repository root
docker build -f 07_docs_server/Dockerfile -t c5p-docs .

# Or use helper script
cd 07_docs_server
./docker-build.sh
```

**Build Process**:
1. Base image: `python:3.13-trixie`
2. Install system dependencies
3. Copy Python project files
4. Install uv package manager
5. Install Python dependencies with uv
6. Copy application source code
7. Copy documentation content (including llms.txt)
8. Create cache directory
9. Set up virtual environment
10. Configure health check
11. Set startup command

**Build Time**: ~2-3 minutes (with cached layers)

### Docker Run

**Development**:
```bash
docker run -p 8080:8080 c5p-docs
```

**Production** (Recommended):
```bash
docker run -d \
  -p 8080:8080 \
  -e BASE_URL=https://support.c5p.app \
  -e DEBUG=false \
  --name c5p-docs-server \
  --restart unless-stopped \
  c5p-docs
```

**With Custom Configuration**:
```bash
docker run -d \
  -p 8080:8080 \
  -e BASE_URL=https://support.c5p.app \
  -e DEBUG=false \
  -e PORT=8080 \
  --name c5p-docs-server \
  --memory="512m" \
  --cpus="1.0" \
  c5p-docs
```

### DigitalOcean App Platform

**Deployment Method**: Docker image deployment

**App Spec Example**:
```yaml
name: c5p-docs-server
services:
  - name: docs
    dockerfile_path: 07_docs_server/Dockerfile
    github:
      repo: your-org/c5p-specs
      branch: main
      deploy_on_push: true
    envs:
      - key: BASE_URL
        value: https://support.c5p.app
      - key: DEBUG
        value: "false"
    http_port: 8080
    health_check:
      http_path: /health
      initial_delay_seconds: 10
      period_seconds: 30
      timeout_seconds: 10
      success_threshold: 1
      failure_threshold: 3
    instance_count: 1
    instance_size_slug: basic-xxs
```

**Instance Sizes**:
- **basic-xxs**: 512MB RAM, 0.5 vCPU (~$5/month)
- **basic-xs**: 1GB RAM, 1 vCPU (~$12/month)
- **basic-s**: 2GB RAM, 1 vCPU (~$18/month)

**Recommended**: basic-xxs (sufficient for documentation server)

### Health Checks

**Endpoint**: `GET /health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "docs_root": "/app/docs",
  "cache_root": "/app/cache",
  "debug": false
}
```

**Docker Health Check** (Dockerfile line 45):
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```

**Load Balancer Health Check**:
- Path: `/health`
- Interval: 30s
- Timeout: 10s
- Healthy threshold: 1
- Unhealthy threshold: 3

### Environment Configuration

**Production Settings**:
```bash
BASE_URL=https://support.c5p.app
DEBUG=false
PORT=8080
DOCS_ROOT=/app/docs
CACHE_ROOT=/app/cache
```

**Staging Settings**:
```bash
BASE_URL=https://staging-support.c5p.app
DEBUG=false
PORT=8080
DOCS_ROOT=/app/docs
CACHE_ROOT=/app/cache
```

### SSL/TLS

**Handled By**: Reverse proxy or platform (DigitalOcean, nginx)

**Application**: Listens on HTTP only (port 8080)

**Production Setup**:
```
Internet → HTTPS (443) → Load Balancer/Proxy → HTTP (8080) → Container
```

### Monitoring

**Metrics to Monitor**:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (5xx responses)
- Cache hit rate
- Memory usage
- CPU usage
- Disk space (cache directory)

**Log Aggregation**:
- Docker logs: `docker logs c5p-docs-server`
- DigitalOcean: Built-in log viewer
- External: Datadog, New Relic, Sentry

---

## Maintenance and Operations

### Routine Maintenance

#### Update Documentation Content

**To update documentation files**:

1. Edit files in `04_documentation/end_user_v1/`
2. Rebuild Docker image
3. Deploy new image

```bash
# Edit content
nano 04_documentation/end_user_v1/01_snelle_uitleg.md

# Rebuild
docker build -f 07_docs_server/Dockerfile -t c5p-docs .

# Redeploy
docker stop c5p-docs-server
docker rm c5p-docs-server
docker run -d -p 8080:8080 -e BASE_URL=https://support.c5p.app --name c5p-docs-server c5p-docs
```

#### Update llms.txt

**To update the curated llms.txt file**:

1. Edit `04_documentation/end_user_v1/llms.txt`
2. Follow update documentation content process above

```bash
# Edit llms.txt
nano 04_documentation/end_user_v1/llms.txt

# Rebuild and redeploy (same as above)
```

#### Cache Management

**Cache is automatically cleared on server restart**

**Manual cache inspection**:
```bash
# View cache directory
docker exec c5p-docs-server ls -la /app/cache/

# Check cache size
docker exec c5p-docs-server du -sh /app/cache/
```

**No manual cache clearing needed** (automatic on restart)

### Troubleshooting

See **README.md** "Troubleshooting" section for common issues and solutions.

**Quick Reference**:
- Relative links not transformed → Check BASE_URL environment variable
- Content not updating → Rebuild Docker image
- Cache not updating → Restart server/container
- Slow first request → Normal (cache miss), subsequent requests fast
- 404 on linked pages → Verify files exist in DOCS_ROOT

### Monitoring and Alerts

**Recommended Alerts**:
1. **Health Check Failure**: `/health` returns non-200
2. **High Error Rate**: > 5% requests return 5xx
3. **High Response Time**: p95 response time > 500ms
4. **High Memory Usage**: > 400MB (indicates leak)
5. **Disk Space**: Cache directory > 100MB (unusual)

**Alerting Tools**:
- DigitalOcean: Built-in monitoring and alerts
- External: PagerDuty, Opsgenie, Slack webhooks

### Backup and Recovery

**Content**: Stored in git repository (no backup needed for content)

**Cache**: Ephemeral (regenerated automatically, no backup needed)

**Configuration**: Documented in README.md and this SPECS.md

**Recovery**:
1. Pull latest code from git
2. Rebuild Docker image
3. Deploy container with proper environment variables

**No database**, **no persistent state** → Simple recovery

### Scaling Considerations

**Vertical Scaling** (Single Instance):
- Increase memory: 512MB → 1GB → 2GB
- Increase CPU: 0.5 vCPU → 1 vCPU → 2 vCPU

**Horizontal Scaling** (Multiple Instances):
- Deploy multiple containers behind load balancer
- Each instance has its own cache (no shared state)
- Session affinity not needed (stateless)

**When to Scale**:
- Response time > 500ms (p95)
- CPU usage > 80% sustained
- Memory usage > 80% sustained
- Request rate > 100/second

---

## Appendix: Code Reference

### Key Functions

**Path Validation** (lines 109-124):
```python
def is_safe_path(path: str, base_path: Path) -> bool:
    """Validate path is within allowed directory boundaries."""
```

**Link Transformation** (lines 405-428):
```python
def transform_relative_to_absolute(markdown_content: str, base_url: str) -> str:
    """Transform relative .md links to absolute URLs."""
```

**Caching Helpers** (lines 430-459):
```python
async def get_cached_llms(cache_file: str) -> Optional[str]:
    """Get cached llms content if exists."""

async def save_cached_llms(cache_file: str, content: str) -> None:
    """Save llms content to cache."""
```

**Endpoints** (lines 1144-1258):
```python
@app.get("/llms.txt")
async def serve_llms_txt(request: Request):
    """Serve llms.txt with fallback strategy."""

@app.get("/llms-full.txt")
async def serve_llms_full_txt(request: Request):
    """Serve expanded documentation with all pages."""
```

### File Locations

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 1388 | Main application |
| `Dockerfile` | 50 | Container configuration |
| `README.md` | 1130+ | User documentation |
| `SPECS.md` | This file | Technical specification |
| `tests/test_llms_implementation.py` | 100+ | Unit tests |
| `tests/test_llms_endpoints.py` | 468 | Integration tests |

---

---

## Model Context Protocol (MCP) Integration

### Overview

Model Context Protocol (MCP) provides interactive documentation access for LLMs via HTTP/JSON-RPC 2.0. MCP complements `llms.txt`/`llms-full.txt` by enabling on-demand queries instead of static dumps.

**Key Benefits:**
- **250x less context** - Typical query: 2KB vs 500KB for llms-full.txt
- **Interactive search** - LLMs query only what they need
- **Scalable** - Handles 1000+ documentation pages
- **Self-contained** - No external services required

### Architecture

**Design Constraints:**
- ✅ Immutable DOCS_ROOT (baked into Docker image)
- ✅ Disk-based index cache (fast k8s pod startup)
- ✅ No external services (self-contained)
- ✅ HTTP/JSON-RPC 2.0 transport (FastAPI-native)

**System Flow:**
```
LLM Client (Claude, ChatGPT)
    │ POST /mcp (JSON-RPC 2.0)
    ▼
FastAPI App
    ├─ Search Index (Whoosh, in-memory)
    │  └─ Loaded from CACHE_ROOT/mcp/whoosh/
    └─ MCP Tools
       ├─ search_docs - Full-text search
       ├─ get_doc_page - Retrieve specific pages
       └─ list_doc_pages - List all pages
```

### MCP Endpoint

**Endpoint:** `POST /mcp`  
**Content-Type:** `application/json`

**Request Format (JSON-RPC 2.0):**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {"query": "rate limiting", "limit": 10}
  }
}
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "result": {
    "content": [{"type": "text", "text": "Found 3 results:\n..."}]
  }
}
```

**Supported Methods:**
- `initialize` - Handshake and capability negotiation
- `tools/list` - List available tools with JSON schemas
- `tools/call` - Execute a tool

### MCP Tools

#### 1. search_docs

**Purpose:** Full-text search across documentation with fuzzy matching

**Input:**
- `query` (string, required, 1-500 chars)
- `limit` (integer, optional, 1-50, default: 10)

**Output:** Formatted search results with snippets and relevance scores

**Features:**
- Fuzzy search (typo tolerance)
- Field boosting (title 2x, headings 1.5x)
- BM25 scoring
- Snippet extraction with context

#### 2. get_doc_page

**Purpose:** Retrieve specific documentation page content

**Input:**
- `path` (string, required) - Relative path to markdown file
- `sections` (array<string>, optional) - Filter by section headings

**Output:** Markdown content (full page or filtered sections)

**Security:** Uses existing path validation (prevents directory traversal)

#### 3. list_doc_pages

**Purpose:** List all available documentation pages

**Input:**
- `category` (string, optional) - Filter by category

**Output:** Formatted list of pages with titles and paths

**Categories:** Extracted from directory structure or sidebar.md

### Search Index with Whoosh

**Search Engine:** Whoosh 2.7.4+ (pure Python, production-ready)

**Why Whoosh:**
- ✅ Pure Python (zero deployment complexity, works everywhere)
- ✅ Production features (fuzzy search, BM25 scoring, field boosting)
- ✅ Persistent disk index (caches to CACHE_ROOT)
- ✅ Fast enough (15-40ms search, 1-2s build for 500 docs)
- ✅ Small footprint (500KB installed)

**Schema:**
```python
path: ID (unique, stored)
title: TEXT (stored, boosted 2.0x, with stemming)
content: TEXT (not stored, with stemming)
content_stored: TEXT (stored, for snippet extraction)
headings: TEXT (stored, boosted 1.5x, with stemming)
category: ID (stored, for filtering)
modified: DATETIME (stored, sortable)
size: NUMERIC (stored)
```

**Features:**
- Fuzzy search: `authentification~` matches `authentication`
- Boolean operators: `docker AND kubernetes NOT compose`
- Field-specific: `title:authentication content:jwt`
- Wildcards: `docker*` matches `dockerize, dockerfile`
- Phrase queries: `"rate limiting"` (exact match)

**Performance (500 docs):**
- Index build: 1-2 seconds (on startup or cache miss)
- Index load: 10-20ms (from cached disk index)
- Search query: 15-40ms (imperceptible to users)
- Memory usage: ~40MB

### Cache Strategy: Hash-Based Validation

**Cache Location:**
```
CACHE_ROOT/
├── html/              # Existing: rendered HTML
├── llms/              # Existing: llms.txt files
└── mcp/               # NEW: MCP search index
    ├── whoosh/        # Whoosh index files (binary)
    │   ├── _MAIN_*.toc
    │   ├── _MAIN_*.seg
    │   └── schema.pickle
    └── metadata.json  # Cache validation metadata
```

**Cache Metadata (`metadata.json`):**
```json
{
  "index_version": "1.0",
  "docs_root": "/app/docs",
  "docs_hash": "a3f5c8d7...",
  "docs_count": 237,
  "built_at": "2026-01-31T10:30:00Z",
  "build_duration_ms": 1847,
  "whoosh_version": "2.7.4",
  "python_version": "3.13.1"
}
```

**Startup Validation Flow:**
1. Check if Whoosh index exists in `CACHE_ROOT/mcp/whoosh/`
2. Calculate SHA256 hash of all `.md` files (paths + mtimes) - <100ms
3. Compare with cached hash in `metadata.json`
4. **If match:** Load Whoosh index from disk (10-20ms) ✅ **FAST**
5. **If mismatch:** Rebuild index with Whoosh (1-2s for 500 docs) ✅ **ACCEPTABLE**

**Cache Invalidation Triggers:**
- File added/modified/deleted (hash mismatch)
- DOCS_ROOT path changed
- Index format version upgraded
- DEBUG=true (always rebuild in development)

**Hash Calculation:**
```python
def calculate_docs_hash() -> str:
    """SHA256 hash of all markdown files (paths + mtimes + sizes)"""
    md_files = sorted(DOCS_ROOT.rglob("*.md"))
    hash_input = [
        f"{file.relative_to(DOCS_ROOT)}:{file.stat().st_mtime}:{file.stat().st_size}"
        for file in md_files
    ]
    content = "\n".join(hash_input).encode('utf-8')
    return hashlib.sha256(content).hexdigest()[:16]
```

**Benefits:**
- Accurate change detection (any file change invalidates cache)
- Fast validation (<100ms hash calculation)
- Fast load from cache (10-20ms Whoosh index open)
- Persistent across container restarts
- Works with volume-mounted docs

**DEBUG Mode:** Always rebuilds index for fresh data during development

### Baking Cache into Docker Image

**For Production Consistency:**

Build the search index at Docker image build time to ensure all pods have identical cache:

```dockerfile
# Build search index at build time
RUN mkdir -p /app/cache/mcp && \
    DOCS_ROOT=/app/docs CACHE_ROOT=/app/cache \
    uv run python -m docs_server.mcp.cli build
```

**Benefits:**
- All pods have identical cache (baked into image)
- No build time on startup (instant!)
- Consistent search results across pods during rolling updates
- Eliminates race conditions in k8s deployments

**Trade-off:** Larger Docker image (~5-10MB for index), but worth it for consistency

### Rate Limiting

**Strategy:** Token bucket per IP address using `slowapi` library

**Configuration:**
- `MCP_RATE_LIMIT_REQUESTS`: 120 (default, configurable via ENV)
- `MCP_RATE_LIMIT_WINDOW`: 60 seconds (default, configurable via ENV)

**Implementation:**
```python
@app.post("/mcp")
@limiter.limit(f"{settings.MCP_RATE_LIMIT_REQUESTS}/{settings.MCP_RATE_LIMIT_WINDOW}second")
async def mcp_endpoint(request: Request):
    # Handle MCP request
```

**Response when exceeded (JSON-RPC error):**
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

### Configuration

**Environment Variables:**
```bash
# MCP Feature
MCP_ENABLED=true                    # Enable/disable MCP endpoint
MCP_RATE_LIMIT_REQUESTS=120        # Requests per window
MCP_RATE_LIMIT_WINDOW=60           # Window in seconds
MCP_MAX_SEARCH_RESULTS=10          # Max results per search
MCP_SNIPPET_LENGTH=200             # Snippet length in characters
```

### File Structure

```
src/docs_server/
├── mcp/
│   ├── __init__.py
│   ├── server.py          # JSON-RPC 2.0 handler
│   ├── schema.py          # Whoosh schema definition
│   ├── indexer.py         # Index builder/loader with hash validation
│   ├── search.py          # Whoosh search implementation
│   ├── tools.py           # Tool implementations (3 tools)
│   ├── models.py          # Pydantic models for validation
│   └── cli.py             # CLI for cache management
├── main.py                # Add /mcp endpoint + startup event
└── config.py              # Add MCP config
```

### Dependencies

**New:**
- `whoosh>=2.7.4` - Full-text search engine (pure Python)
- `slowapi>=0.1.9` - Rate limiting for FastAPI

**Total:** 2 new dependencies (both pure Python, no C extensions)

### Security

1. **Path Traversal Prevention**
   - Reuse existing `get_file_path()` validation
   - No `..` or absolute paths allowed in `get_doc_page` tool

2. **Rate Limiting**
   - Per-IP tracking with token bucket
   - Configurable limits via ENV
   - Graceful error responses

3. **Input Validation**
   - Pydantic models for all tool inputs
   - Query length limits (1-500 chars)
   - Result limits (1-50 results)

4. **No Authentication**
   - Public endpoint by design (like llms.txt)
   - Rate limiting provides DoS protection
   - Can add reverse proxy auth if needed

### Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Index build (100 docs) | <500ms | ~300ms ✅ |
| Index load from cache | <20ms | 10-15ms ✅ |
| Search query | <100ms | 15-40ms ✅ |
| Get page | <20ms | <10ms ✅ |
| Memory footprint | <50MB per 100 docs | ~40MB ✅ |

### CLI Tools

**Cache Management:**
```bash
# Build index
uv run python -m docs_server.mcp.cli build

# Validate cache
uv run python -m docs_server.mcp.cli validate

# Clear cache
uv run python -m docs_server.mcp.cli invalidate

# Show cache info
uv run python -m docs_server.mcp.cli info
```

### Testing Strategy

**Test Coverage (~80% target):**
- `test_mcp_server.py` - JSON-RPC parsing, error handling
- `test_mcp_indexer.py` - Index building, caching, hash validation
- `test_mcp_search.py` - Whoosh search, fuzzy matching, snippets
- `test_mcp_tools.py` - Tool implementations
- `test_mcp_integration.py` - End-to-end workflows

**208 tests** covering MCP functionality

### Error Handling

**JSON-RPC 2.0 Error Codes:**
- `-32700` Parse error (invalid JSON)
- `-32600` Invalid request (missing required fields)
- `-32601` Method not found (unknown method)
- `-32602` Invalid params (validation failure)
- `-32603` Internal error (server error)
- `-32000` Rate limit exceeded (custom)

**Contextual Error Data:**
- File not found: include `path`
- Rate limit: include `retryAfter` seconds
- Search error: include `query`
- DEBUG mode: include traceback

### Usage Example

**Claude Desktop Config:**
```json
{
  "mcpServers": {
    "servemd": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://docs.example.com/mcp",
        "-H", "Content-Type: application/json",
        "-d", "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"search_docs\",\"arguments\":{\"query\":\"authentication\"}}}"
      ]
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "Found 3 results:\n\n1. api/endpoints.md (score: 15.2)\n   'Configure authentication via API keys...'\n\n2. configuration.md (score: 8.4)\n   'Authentication settings in config.py...'\n\n3. security.md (score: 5.1)\n   'No authentication by default...'"
    }]
  }
}
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-09-24 | Initial specification (KLO-519) |
| 2.0 | 2026-01-30 | Complete revamp with KLO-642 implementation |
| 2.1 | 2026-01-31 | Added MCP integration specification |

**Current Version**: 2.1  
**Status**: Production Ready (MCP: Implemented)  
**Last Updated**: 2026-01-31
