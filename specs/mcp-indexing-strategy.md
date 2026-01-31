# MCP Indexing Strategy - Deep Dive

**Date:** 2026-01-31  
**Status:** Design Discussion

---

## Current Health Endpoint

The app already has a `/health` endpoint:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "docs_root": str(settings.DOCS_ROOT.absolute()),
        "cache_root": str(settings.CACHE_ROOT.absolute()),
        "debug": settings.DEBUG,
    }
```

**For k8s/k3s:** We need to extend this to include MCP readiness.

---

## The Scalability Question

**Problem:** How do we index 1000s of files efficiently?

**Current approach:**
- Scan all `.md` files on startup
- Parse each file (title, content, sections)
- Build in-memory index
- **Estimated time:** 500ms for 100 files = **5 seconds for 1000 files**

**Is 5 seconds acceptable?**
- ❌ Slows down k8s pod startup
- ❌ Delays readiness probe
- ❌ Poor developer experience (restart = 5s wait)

---

## Indexing Strategy Options

### Option 1: Build-Time Indexing (Docker) ⭐ **RECOMMENDED**

**Concept:** Build the index during Docker image build, bake it into the image

**Process:**
1. During `docker build`:
   ```dockerfile
   # Copy docs
   COPY docs/ /app/docs/
   
   # Build search index (at build time)
   RUN python -m docs_server.mcp.indexer build --output /app/cache/mcp/search-index.json
   ```

2. At runtime:
   - Index already exists in image
   - Load from disk (<10ms)
   - **Zero index build time on startup**

**Pros:**
- ✅ **Instant startup** (10ms vs 5 seconds)
- ✅ Perfect for k8s horizontal scaling
- ✅ Consistent index across all pods
- ✅ No CPU spike on pod creation
- ✅ Immutable docs = index never stale

**Cons:**
- ❌ Requires CLI tool for index building
- ❌ Slightly larger Docker image (~5-10MB for index)

**Implementation:**
```python
# src/docs_server/mcp/indexer.py

def build_index_cli():
    """CLI tool to build index at Docker build time"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['build'])
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    # Build index
    index = build_search_index_sync()
    
    # Save to output path
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2))
    
    print(f"✅ Index built: {index['docs_count']} docs → {output_path}")

if __name__ == '__main__':
    build_index_cli()
```

**Docker integration:**
```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Copy source
COPY src/ /app/src/
COPY docs/ /app/docs/

# Build search index (at build time!) ← NEW
RUN mkdir -p /app/cache/mcp && \
    uv run python -m docs_server.mcp.indexer build --output /app/cache/mcp/search-index.json

# Runtime
ENV DOCS_ROOT=/app/docs
ENV CACHE_ROOT=/app/cache
CMD ["uv", "run", "python", "-m", "docs_server"]
```

**Startup behavior:**
```python
@app.on_event("startup")
async def startup_mcp():
    if settings.MCP_ENABLED:
        # Check if index exists in image (built at build time)
        index_path = settings.CACHE_ROOT / "mcp" / "search-index.json"
        
        if index_path.exists():
            # Load from pre-built index (10ms)
            logger.info("Loading pre-built MCP index...")
            await load_index_from_cache()
            logger.info("✅ MCP ready (loaded from cache)")
        else:
            # Fallback: build on startup (5 seconds)
            logger.warning("No pre-built index found, building now...")
            await build_search_index()
            await save_index_to_cache()
            logger.info("✅ MCP ready (built on startup)")
```

**Best for:** Production deployments, k8s/k3s horizontal scaling

---

### Option 2: Parallel Indexing (Multiprocessing)

**Concept:** Use Python multiprocessing to index files in parallel

**Process:**
1. Scan for all `.md` files
2. Split files into chunks (e.g., 100 files per worker)
3. Process each chunk in parallel using `multiprocessing.Pool`
4. Merge results

**Implementation sketch:**
```python
import multiprocessing as mp
from functools import partial

def index_file(file_path: Path, docs_root: Path) -> tuple[str, dict]:
    """Index a single file (worker function)"""
    rel_path = str(file_path.relative_to(docs_root))
    content = file_path.read_text(encoding='utf-8')
    
    return rel_path, {
        "path": rel_path,
        "title": extract_title(content),
        "content": content,
        "sections": parse_sections(content),
        "mtime": file_path.stat().st_mtime,
        "size": len(content),
        "word_count": len(content.split())
    }

async def build_search_index_parallel() -> dict:
    """Build index using parallel processing"""
    md_files = list(settings.DOCS_ROOT.rglob("*.md"))
    
    # Use all CPU cores
    num_workers = mp.cpu_count()
    
    # Index files in parallel
    with mp.Pool(num_workers) as pool:
        worker = partial(index_file, docs_root=settings.DOCS_ROOT)
        results = pool.map(worker, md_files)
    
    # Build index dict
    index = {
        "version": "1.0",
        "built_at": datetime.utcnow().isoformat(),
        "docs_count": len(results),
        "index": dict(results)
    }
    
    return index
```

**Performance:**
- **Sequential:** 5 seconds for 1000 files (1 core)
- **Parallel (4 cores):** ~1.5 seconds for 1000 files
- **Parallel (8 cores):** ~1 second for 1000 files

**Pros:**
- ✅ 3-5x faster than sequential
- ✅ No Docker changes needed
- ✅ Works in development

**Cons:**
- ❌ Still takes 1-1.5 seconds (not instant)
- ❌ CPU spike on startup
- ❌ More complex code

**Best for:** Development mode, when you can't pre-build index

---

### Option 3: Incremental Indexing (Smart Updates)

**Concept:** Only re-index files that changed since last index

**Process:**
1. Load cached index
2. Check file mtimes
3. Only re-index changed files
4. Merge with cached index

**Implementation sketch:**
```python
async def build_search_index_incremental() -> dict:
    """Build index incrementally (only changed files)"""
    
    # Load cached index
    cached = await load_index_from_cache()
    if not cached:
        # No cache, build from scratch
        return await build_search_index()
    
    # Scan for all files
    current_files = {
        str(f.relative_to(settings.DOCS_ROOT)): f
        for f in settings.DOCS_ROOT.rglob("*.md")
    }
    
    # Find changed files
    changed_files = []
    for rel_path, file_path in current_files.items():
        current_mtime = file_path.stat().st_mtime
        
        if rel_path not in cached["index"]:
            # New file
            changed_files.append(file_path)
        elif cached["index"][rel_path]["mtime"] != current_mtime:
            # Modified file
            changed_files.append(file_path)
    
    # Find deleted files
    deleted_files = [
        path for path in cached["index"].keys()
        if path not in current_files
    ]
    
    # If no changes, return cached
    if not changed_files and not deleted_files:
        logger.info("No changes detected, using cached index")
        return cached
    
    # Re-index changed files only
    logger.info(f"Re-indexing {len(changed_files)} changed files...")
    for file_path in changed_files:
        rel_path = str(file_path.relative_to(settings.DOCS_ROOT))
        content = file_path.read_text(encoding='utf-8')
        
        cached["index"][rel_path] = {
            "path": rel_path,
            "title": extract_title(content),
            "content": content,
            "sections": parse_sections(content),
            "mtime": file_path.stat().st_mtime,
            "size": len(content),
            "word_count": len(content.split())
        }
    
    # Remove deleted files
    for path in deleted_files:
        del cached["index"][path]
    
    # Update metadata
    cached["docs_count"] = len(cached["index"])
    cached["built_at"] = datetime.utcnow().isoformat()
    
    return cached
```

**Performance:**
- **No changes:** <10ms (load from cache)
- **Few changes (1-10 files):** 50-100ms
- **Many changes (100+ files):** 500ms+

**Pros:**
- ✅ Very fast if no/few changes
- ✅ Useful in development (hot reload)

**Cons:**
- ❌ Complex logic
- ❌ Still slow on first build
- ❌ Not useful for immutable docs (production)

**Best for:** Development mode with file watching

---

### Option 4: Lazy Indexing (On-Demand)

**Concept:** Don't build full index on startup, index files as they're searched

**Process:**
1. Startup: Load minimal metadata (just file list)
2. First search: Index files on-demand
3. Cache indexed files for future searches
4. Gradually build complete index

**Implementation sketch:**
```python
# Global partial index
_partial_index: dict[str, dict] = {}

async def search_docs_lazy(query: str, limit: int) -> list[dict]:
    """Search with lazy indexing"""
    
    # Get list of all files (fast)
    md_files = list(settings.DOCS_ROOT.rglob("*.md"))
    
    results = []
    
    for md_file in md_files:
        rel_path = str(md_file.relative_to(settings.DOCS_ROOT))
        
        # Check if already indexed
        if rel_path not in _partial_index:
            # Index this file now (lazy)
            content = md_file.read_text(encoding='utf-8')
            _partial_index[rel_path] = {
                "title": extract_title(content),
                "content": content,
                "sections": parse_sections(content),
                # ...
            }
        
        # Search in this file
        doc = _partial_index[rel_path]
        score = calculate_score(doc, query)
        
        if score > 0:
            results.append({
                "path": rel_path,
                "score": score,
                # ...
            })
    
    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
```

**Performance:**
- **Startup:** <10ms (just file list)
- **First search:** Slow (indexes all files during search)
- **Subsequent searches:** Fast (files already indexed)

**Pros:**
- ✅ Instant startup
- ✅ No upfront cost

**Cons:**
- ❌ First search is VERY slow (5+ seconds for 1000 files)
- ❌ Poor UX (unpredictable response times)
- ❌ Complex state management

**Best for:** Rarely used features, very large doc sets

---

## Recommended Strategy by Environment

### Production (k8s/k3s) → **Option 1: Build-Time Indexing**

```
Docker Build Time:
├─ Copy docs → /app/docs/
├─ Build index → /app/cache/mcp/search-index.json (5 seconds, one-time)
└─ Bake into image

Container Startup:
└─ Load index from disk (10ms) ✅ INSTANT
```

**Why:**
- Docs are immutable (baked into image)
- Fastest possible startup for k8s pods
- No CPU spike during scaling
- Consistent across all replicas

### Development (DEBUG=true) → **Option 2: Parallel + Option 3: Incremental**

```
First Startup:
└─ Build index in parallel (1-1.5 seconds for 1000 files)

File Change Detected:
└─ Re-index changed files only (50-100ms)
```

**Why:**
- Fast enough for development
- Supports hot reload
- No Docker changes needed

---

## Health Endpoint Enhancement

**For k8s/k3s readiness/liveness probes:**

```python
# src/docs_server/main.py

@app.get("/health")
async def health_check():
    """Health check with MCP readiness"""
    
    # Base health
    health = {
        "status": "healthy",
        "docs_root": str(settings.DOCS_ROOT.absolute()),
        "cache_root": str(settings.CACHE_ROOT.absolute()),
        "debug": settings.DEBUG,
    }
    
    # Check MCP readiness
    if settings.MCP_ENABLED:
        from .mcp.indexer import get_search_index
        
        try:
            index = get_search_index()
            health["mcp"] = {
                "status": "ready" if index else "not_ready",
                "docs_indexed": index.get("docs_count", 0) if index else 0,
                "index_built_at": index.get("built_at") if index else None
            }
        except Exception as e:
            health["mcp"] = {
                "status": "error",
                "error": str(e)
            }
    
    # Determine overall status
    if settings.MCP_ENABLED and health.get("mcp", {}).get("status") != "ready":
        health["status"] = "degraded"
    
    return health

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - is the app running?"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - is the app ready to serve traffic?"""
    
    # Check if MCP is ready (if enabled)
    if settings.MCP_ENABLED:
        from .mcp.indexer import get_search_index
        index = get_search_index()
        
        if not index:
            # MCP enabled but index not ready
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "MCP index not built"}
            )
    
    return {"status": "ready"}
```

**k8s deployment configuration:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: servemd
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: servemd
        image: servemd:latest
        ports:
        - containerPort: 8080
        
        # Liveness probe - restart if unhealthy
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Readiness probe - don't send traffic until ready
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 2  # Fast because index is pre-built!
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        env:
        - name: MCP_ENABLED
          value: "true"
        - name: DOCS_ROOT
          value: "/app/docs"
        - name: CACHE_ROOT
          value: "/app/cache"
```

---

## Performance Comparison

| Strategy | Startup Time | First Search | Memory | Best For |
|----------|-------------|--------------|---------|----------|
| **Build-Time** (Option 1) | **10ms** ⭐ | 50-100ms | 10MB | **Production** |
| **Parallel** (Option 2) | 1-1.5s | 50-100ms | 10MB | Development |
| **Incremental** (Option 3) | 10ms (if cached) | 50-100ms | 10MB | Development |
| **Lazy** (Option 4) | 10ms | **5+ seconds** ❌ | 10MB | Not recommended |
| **Sequential** (Current) | 5s | 50-100ms | 10MB | Small doc sets |

---

## Decision Matrix

### For 1000s of Files

**Production:**
- ✅ Use **Build-Time Indexing** (Option 1)
- ✅ Add health endpoints (`/health/ready`, `/health/live`)
- ✅ Set k8s `initialDelaySeconds: 2` (fast startup)

**Development:**
- ✅ Use **Parallel Indexing** (Option 2)
- ✅ Optional: Add **Incremental** (Option 3) for hot reload
- ✅ Accept 1-1.5 second startup (reasonable for dev)

---

## Implementation Recommendations

### Phase 1: Start Simple (MVP)

- Implement sequential indexing (current plan)
- Works fine for <500 files
- Get feature working first

### Phase 2: Add Build-Time (Production)

- Add CLI tool for index building
- Update Dockerfile to build index
- Add health endpoints

### Phase 3: Optimize Development (Optional)

- Add parallel indexing for DEBUG mode
- Add incremental indexing for hot reload
- Improve DX

---

## Open Questions

1. **Should we support both strategies?**
   - Build-time for production (fast)
   - Parallel for development (flexible)

2. **What's acceptable startup time?**
   - k8s: <2 seconds (for readiness probe)
   - Development: <5 seconds (acceptable for restart)

3. **How large are your doc sets?**
   - <100 files: Sequential is fine
   - 100-500 files: Parallel recommended
   - 500+ files: Build-time required

4. **Do you need hot reload in development?**
   - Yes: Add incremental indexing
   - No: Parallel is sufficient

---

## My Recommendation

**Start with Option 1 (Build-Time) for production** because:
- ✅ Your docs are immutable (Docker image)
- ✅ Instant startup is critical for k8s horizontal scaling
- ✅ Simple to implement (just add CLI tool)
- ✅ Best performance characteristics
- ✅ No runtime complexity

**Use Option 2 (Parallel) for development fallback** when cache doesn't exist.

**Add health endpoints** for k8s readiness/liveness probes.

---

## What do you think?

Which strategy makes most sense for your use case?
- How large are your typical doc sets?
- What's acceptable startup time for k8s pods?
- Do you need hot reload in development?
