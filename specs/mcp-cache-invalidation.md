# MCP Cache Invalidation Strategy

**Date:** 2026-01-31  
**Status:** Critical Design Decision

---

## The Cache Invalidation Problem

> "There are only two hard things in Computer Science: cache invalidation and naming things."
> — Phil Karlton

**The Question:** When does the cached search index become stale?

---

## Cache Structure

```
CACHE_ROOT/
├── html/                    # Existing: rendered HTML cache
│   └── index.html.cache
├── llms/                    # Existing: llms.txt cache
│   └── llms.txt.cache
└── mcp/                     # NEW: MCP search index
    ├── index.db             # Whoosh index files
    ├── schema.pickle
    └── _MAIN_*.toc
```

---

## Invalidation Scenarios

### Scenario 1: Files Added/Removed/Modified

**Triggers:**
- User adds new markdown file
- User modifies existing file
- User deletes file
- User renames file

**Current behavior (other caches):**
- HTML cache: Per-file, checks mtime
- llms.txt cache: No invalidation (cleared on restart)

**Problem:** How do we know files changed?

---

### Scenario 2: Configuration Changed

**Triggers:**
- `DOCS_ROOT` changed (pointing to different directory)
- `MCP_ENABLED` toggled off/on
- App version updated (index format may change)

**Problem:** Old cache may be incompatible

---

### Scenario 3: Rolling Deployment (k8s)

**Scenario:**
- Pod 1 has cached index (version A of docs)
- Deploy new code with docs version B
- Pod 2 starts, builds new index
- Both pods serving different content!

**Problem:** Inconsistent search results across pods

---

## Invalidation Strategies

### Strategy 1: Hash-Based Validation ⭐ **RECOMMENDED**

**Concept:** Generate hash of all file paths + mtimes, store in cache metadata

**How it works:**
```python
def calculate_docs_hash() -> str:
    """Generate hash of all markdown files (paths + mtimes)"""
    md_files = sorted(settings.DOCS_ROOT.rglob("*.md"))
    
    hash_input = []
    for f in md_files:
        rel_path = str(f.relative_to(settings.DOCS_ROOT))
        mtime = f.stat().st_mtime
        hash_input.append(f"{rel_path}:{mtime}")
    
    # Hash the concatenated string
    content = "\n".join(hash_input).encode('utf-8')
    return hashlib.sha256(content).hexdigest()

async def is_cache_valid() -> bool:
    """Check if cached index is still valid"""
    
    # Load cached metadata
    cache_metadata = load_cache_metadata()
    if not cache_metadata:
        return False
    
    # Calculate current hash
    current_hash = calculate_docs_hash()
    cached_hash = cache_metadata.get("docs_hash")
    
    # Compare
    if current_hash != cached_hash:
        logger.info(f"Cache invalid: hash mismatch")
        return False
    
    # Check other criteria
    if cache_metadata.get("docs_root") != str(settings.DOCS_ROOT):
        logger.info(f"Cache invalid: DOCS_ROOT changed")
        return False
    
    if cache_metadata.get("index_version") != CURRENT_INDEX_VERSION:
        logger.info(f"Cache invalid: index version changed")
        return False
    
    return True
```

**Cache metadata file:**
```json
{
  "index_version": "1.0",
  "docs_root": "/app/docs",
  "docs_hash": "a3f5c8d...",
  "docs_count": 237,
  "built_at": "2026-01-31T10:30:00Z",
  "build_duration_ms": 1847
}
```

**Startup flow:**
```python
@app.on_event("startup")
async def startup_mcp():
    if not settings.MCP_ENABLED:
        return
    
    logger.info("Initializing MCP search index...")
    
    # Check if cache is valid
    if await is_cache_valid():
        # Load from cache (fast: 10-50ms)
        logger.info("Loading MCP index from cache...")
        await load_index_from_cache()
        logger.info("✅ MCP index loaded from cache")
    else:
        # Rebuild index (1-2 seconds)
        logger.info("Cache invalid or missing, rebuilding index...")
        await build_search_index()
        await save_index_to_cache()
        logger.info("✅ MCP index built and cached")
```

**Performance:**
- **Hash calculation:** <100ms for 500 files (just stat calls)
- **Cache hit:** 10-50ms (load index)
- **Cache miss:** 1-2 seconds (rebuild)

**Pros:**
- ✅ Accurate detection (any file change invalidates)
- ✅ Fast validation (<100ms)
- ✅ Simple to implement
- ✅ Works across deployments

**Cons:**
- ❌ Rebuilds entire index even for single file change
- ❌ No incremental updates

---

### Strategy 2: Per-File Tracking with Incremental Updates

**Concept:** Track each file individually, only re-index changed files

**How it works:**
```python
# Store per-file metadata
cache_metadata = {
    "api/endpoints.md": {
        "mtime": 1706745600.0,
        "size": 15234,
        "indexed_at": "2026-01-31T10:30:00Z"
    },
    "configuration.md": {
        "mtime": 1706745500.0,
        "size": 8934,
        "indexed_at": "2026-01-31T10:30:00Z"
    }
}

async def incremental_index_update():
    """Update index incrementally"""
    
    # Load cache metadata
    cached_files = load_file_metadata()
    
    # Scan current files
    current_files = {}
    for f in settings.DOCS_ROOT.rglob("*.md"):
        rel_path = str(f.relative_to(settings.DOCS_ROOT))
        current_files[rel_path] = {
            "mtime": f.stat().st_mtime,
            "size": f.stat().st_size
        }
    
    # Find changes
    added = set(current_files) - set(cached_files)
    removed = set(cached_files) - set(current_files)
    modified = {
        path for path in current_files
        if path in cached_files and 
           current_files[path]["mtime"] != cached_files[path]["mtime"]
    }
    
    if not (added or removed or modified):
        logger.info("No changes detected")
        return
    
    # Open index for updates
    with index.writer() as writer:
        # Remove deleted/modified documents
        for path in (removed | modified):
            writer.delete_by_term("path", path)
        
        # Add new/modified documents
        for path in (added | modified):
            doc = parse_document(current_files[path])
            writer.add_document(**doc)
    
    logger.info(f"Index updated: +{len(added)} ~{len(modified)} -{len(removed)}")
```

**Performance:**
- **No changes:** <10ms (just file stat checks)
- **Few changes (1-10 files):** 100-200ms (incremental update)
- **Many changes:** 1-2 seconds (rebuild recommended)

**Pros:**
- ✅ Fast when few files change
- ✅ No unnecessary rebuilds
- ✅ Great for development with hot reload

**Cons:**
- ❌ More complex implementation
- ❌ Requires Whoosh support (it does have it!)
- ❌ More edge cases to handle

---

### Strategy 3: Time-Based Expiration

**Concept:** Cache expires after N minutes/hours

```python
async def is_cache_expired() -> bool:
    metadata = load_cache_metadata()
    if not metadata:
        return True
    
    built_at = datetime.fromisoformat(metadata["built_at"])
    age = datetime.utcnow() - built_at
    
    # Expire after 1 hour (configurable)
    max_age = timedelta(hours=settings.MCP_CACHE_MAX_AGE_HOURS)
    
    return age > max_age
```

**Pros:**
- ✅ Simple to implement
- ✅ Predictable behavior

**Cons:**
- ❌ May rebuild unnecessarily
- ❌ May serve stale data before expiration
- ❌ Not suitable for immutable docs

---

### Strategy 4: Manual Invalidation API

**Concept:** Provide endpoint to clear cache

```python
@app.post("/admin/mcp/invalidate-cache")
async def invalidate_mcp_cache(
    api_key: str = Header(None, alias="X-API-Key")
):
    """Manually invalidate MCP cache (admin only)"""
    
    # Check API key
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401)
    
    # Clear cache
    cache_dir = settings.CACHE_ROOT / "mcp"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    
    # Rebuild index
    await build_search_index()
    await save_index_to_cache()
    
    return {"status": "cache_invalidated", "rebuilt": True}
```

**Pros:**
- ✅ Full control
- ✅ Useful for debugging
- ✅ Can trigger from CI/CD

**Cons:**
- ❌ Requires manual action
- ❌ Needs authentication
- ❌ Not automatic

---

## Recommended Strategy: Hybrid Approach

**Combine multiple strategies for best results:**

### Production Mode (DEBUG=false):

1. **Hash-based validation** (Strategy 1)
   - Check hash on startup
   - Rebuild if hash mismatch
   - Fast and reliable

2. **Version checking**
   - Store index format version in metadata
   - Invalidate if version changes
   - Handles app upgrades

3. **Manual invalidation API** (Strategy 4)
   - Admin endpoint for emergency cache clear
   - Useful for CI/CD integration

### Development Mode (DEBUG=true):

1. **Incremental updates** (Strategy 2)
   - Watch for file changes
   - Update index incrementally
   - Fast iteration

2. **Auto-rebuild on restart**
   - Always rebuild in DEBUG mode
   - Ensure fresh data for development

---

## Implementation

### Cache Metadata Structure

```python
# CACHE_ROOT/mcp/metadata.json
{
  "index_version": "1.0",           # Format version
  "docs_root": "/app/docs",         # Source directory
  "docs_hash": "a3f5c8d...",        # SHA256 of files + mtimes
  "docs_count": 237,                # Number of indexed docs
  "built_at": "2026-01-31T10:30:00Z",  # When index was built
  "build_duration_ms": 1847,        # How long it took
  "whoosh_version": "2.7.4",        # Library version
  "python_version": "3.13.1"        # Python version
}
```

### Startup Logic

```python
CURRENT_INDEX_VERSION = "1.0"

@app.on_event("startup")
async def startup_mcp():
    """Initialize MCP with smart caching"""
    
    if not settings.MCP_ENABLED:
        return
    
    logger.info("🔍 Initializing MCP search...")
    
    # Check cache validity
    cache_valid = await validate_cache()
    
    if cache_valid:
        # Fast path: load from cache
        try:
            logger.info("Loading index from cache...")
            start = time.time()
            await load_index_from_cache()
            elapsed = (time.time() - start) * 1000
            logger.info(f"✅ MCP ready ({elapsed:.0f}ms, from cache)")
            return
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}, rebuilding...")
    
    # Slow path: rebuild index
    try:
        logger.info("Building search index...")
        start = time.time()
        await build_search_index()
        await save_index_to_cache()
        elapsed = (time.time() - start) * 1000
        logger.info(f"✅ MCP ready ({elapsed:.0f}ms, index built)")
    except Exception as e:
        logger.error(f"Failed to build index: {e}")
        # Don't fail startup, just disable MCP
        settings.MCP_ENABLED = False
        logger.warning("⚠️ MCP disabled due to indexing failure")

async def validate_cache() -> bool:
    """Validate cached index"""
    
    # Check if cache exists
    cache_dir = settings.CACHE_ROOT / "mcp"
    metadata_file = cache_dir / "metadata.json"
    
    if not metadata_file.exists():
        logger.info("No cache found")
        return False
    
    # Load metadata
    try:
        metadata = json.loads(metadata_file.read_text())
    except Exception as e:
        logger.warning(f"Invalid cache metadata: {e}")
        return False
    
    # Validate index version
    if metadata.get("index_version") != CURRENT_INDEX_VERSION:
        logger.info(f"Cache invalid: version mismatch "
                   f"({metadata.get('index_version')} != {CURRENT_INDEX_VERSION})")
        return False
    
    # Validate DOCS_ROOT
    if metadata.get("docs_root") != str(settings.DOCS_ROOT.absolute()):
        logger.info(f"Cache invalid: DOCS_ROOT changed")
        return False
    
    # In DEBUG mode, always rebuild
    if settings.DEBUG:
        logger.info("DEBUG mode: forcing rebuild")
        return False
    
    # Validate file hash
    current_hash = calculate_docs_hash()
    cached_hash = metadata.get("docs_hash")
    
    if current_hash != cached_hash:
        logger.info("Cache invalid: files changed")
        return False
    
    # Cache is valid!
    logger.info(f"Cache valid: {metadata['docs_count']} docs, "
               f"built {metadata['built_at']}")
    return True

def calculate_docs_hash() -> str:
    """Calculate hash of all markdown files"""
    md_files = sorted(settings.DOCS_ROOT.rglob("*.md"))
    
    if not md_files:
        return "empty"
    
    # Build hash input: path:mtime:size for each file
    hash_parts = []
    for f in md_files:
        try:
            stat = f.stat()
            rel_path = str(f.relative_to(settings.DOCS_ROOT))
            hash_parts.append(f"{rel_path}:{stat.st_mtime}:{stat.st_size}")
        except Exception as e:
            logger.warning(f"Error stat'ing {f}: {e}")
            continue
    
    # Calculate SHA256
    content = "\n".join(hash_parts).encode('utf-8')
    return hashlib.sha256(content).hexdigest()[:16]  # First 16 chars sufficient
```

---

## Cache Invalidation for Rolling Deployments (k8s)

### Problem: Inconsistent Cache Across Pods

**Scenario:**
```
Time 0: Deploy v1 (docs version A)
├─ Pod 1 builds cache for docs A
└─ Pod 2 builds cache for docs A

Time 1: Deploy v2 (docs version B)
├─ Pod 1 still running (cache for docs A) ← OLD
├─ Pod 2 still running (cache for docs A) ← OLD
├─ Pod 3 starts (builds cache for docs B) ← NEW
└─ Pod 4 starts (builds cache for docs B) ← NEW

Result: Inconsistent search results!
```

### Solution: Bake Cache Into Docker Image

**Dockerfile:**
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Copy source
COPY src/ /app/src/
COPY docs/ /app/docs/

# Build search index at build time! ← KEY SOLUTION
RUN mkdir -p /app/cache/mcp && \
    DOCS_ROOT=/app/docs CACHE_ROOT=/app/cache \
    uv run python -c "
import asyncio
from docs_server.mcp.indexer import build_search_index, save_index_to_cache
asyncio.run(build_search_index())
asyncio.run(save_index_to_cache())
"

# Set environment
ENV DOCS_ROOT=/app/docs
ENV CACHE_ROOT=/app/cache

CMD ["uv", "run", "python", "-m", "docs_server"]
```

**Benefits:**
- ✅ All pods have identical cache (baked into image)
- ✅ No build time on startup (instant!)
- ✅ Consistent search results across all pods
- ✅ Rolling updates are safe (new image = new cache)

**Trade-off:**
- Larger Docker image (~5-10MB for index)
- But worth it for consistency!

---

## Configuration Options

```python
# config.py

class Settings(BaseSettings):
    # Existing
    DOCS_ROOT: Path = Path("./docs")
    CACHE_ROOT: Path = Path("./__cache__")
    DEBUG: bool = False
    
    # MCP Cache Settings
    MCP_CACHE_ENABLED: bool = True                    # Enable disk caching
    MCP_CACHE_VALIDATE_ON_STARTUP: bool = True        # Check hash on startup
    MCP_FORCE_REBUILD: bool = False                   # Always rebuild (debug)
    MCP_CACHE_MAX_AGE_HOURS: int = 0                  # 0 = no time-based expiry
```

---

## Cache Management Commands

### CLI Tool for Cache Management

```python
# src/docs_server/mcp/cli.py

import click

@click.group()
def cli():
    """MCP index management CLI"""
    pass

@cli.command()
def build():
    """Build search index"""
    import asyncio
    asyncio.run(build_search_index())
    asyncio.run(save_index_to_cache())
    click.echo("✅ Index built")

@cli.command()
def validate():
    """Validate cached index"""
    import asyncio
    is_valid = asyncio.run(validate_cache())
    if is_valid:
        click.echo("✅ Cache is valid")
    else:
        click.echo("❌ Cache is invalid")
        raise SystemExit(1)

@cli.command()
def invalidate():
    """Clear cached index"""
    cache_dir = settings.CACHE_ROOT / "mcp"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        click.echo("✅ Cache cleared")
    else:
        click.echo("No cache to clear")

@cli.command()
def info():
    """Show cache info"""
    metadata_file = settings.CACHE_ROOT / "mcp" / "metadata.json"
    if not metadata_file.exists():
        click.echo("No cache found")
        return
    
    metadata = json.loads(metadata_file.read_text())
    click.echo(f"Index Version: {metadata['index_version']}")
    click.echo(f"Docs Count: {metadata['docs_count']}")
    click.echo(f"Built At: {metadata['built_at']}")
    click.echo(f"Build Duration: {metadata['build_duration_ms']}ms")
    click.echo(f"Docs Hash: {metadata['docs_hash']}")

if __name__ == '__main__':
    cli()
```

**Usage:**
```bash
# Build index
uv run python -m docs_server.mcp.cli build

# Validate cache
uv run python -m docs_server.mcp.cli validate

# Clear cache
uv run python -m docs_server.mcp.cli invalidate

# Show info
uv run python -m docs_server.mcp.cli info
```

---

## Summary

### Recommended Approach

1. **Hash-based validation** on startup (fast: <100ms)
2. **Rebuild on mismatch** (1-2 seconds acceptable)
3. **Cache metadata** with version, hash, timestamp
4. **Bake into Docker image** for production consistency
5. **CLI tools** for manual management
6. **Always rebuild** in DEBUG mode

### Cache Validity Checks

- ✅ Index version matches current version
- ✅ DOCS_ROOT path matches
- ✅ File hash matches (all files + mtimes)
- ✅ Not in DEBUG mode

### Performance

- **Cache hit:** 10-50ms load time
- **Cache miss:** 1-2 seconds rebuild time
- **Hash calculation:** <100ms validation time

---

## Decision: Final Strategy

**For your use case (volume-mounted docs, k8s, 5-10s startup budget):**

1. ✅ Use **Whoosh** for search index (pure Python, production-ready)
2. ✅ **Hash-based validation** on startup (<100ms)
3. ✅ **Rebuild if invalid** (1-2 seconds, within budget)
4. ✅ **Cache to CACHE_ROOT** (persistent across restarts)
5. ✅ **Bake into Docker image** when docs are static
6. ✅ Add **health endpoints** with index readiness check
7. ✅ Include **fuzzy search** from day 1 (Whoosh supports it!)

**Next:** Update TODO and specification with these decisions?
