# MCP Indexing - Advanced Data Structures

**Date:** 2026-01-31  
**Status:** Design Discussion - Smart Indexing

---

## Key Insight: Volume-Mounted Docs

**You're right!** If users run:
```bash
# CLI usage
servemd --docs-root /path/to/docs

# Docker with volume mount
docker run -v /path/to/docs:/app/docs servemd
```

Then docs are **NOT** in the Docker image, so build-time indexing won't work!

**This means:** We need efficient runtime indexing that builds in <5 seconds for 100-500 files.

---

## The Real Problem: Search Speed vs Build Speed

**Current approach:** Store full content, search linearly
- Build: Simple (just read files)
- Search: Slow O(n×m) where n=docs, m=content length

**What we need:**
- Build: <5 seconds for 500 files
- Search: <50ms even with 1000 files
- Memory: Reasonable (<100MB)

---

## Smart Indexing Options

### Option 1: Inverted Index (Industry Standard) ⭐

**Concept:** Like a book's index - map words → documents containing them

**Structure:**
```python
inverted_index = {
    "authentication": [
        {"doc": "api/endpoints.md", "positions": [45, 123, 567], "title": True},
        {"doc": "security.md", "positions": [12, 89], "heading": True}
    ],
    "rate": [
        {"doc": "api/endpoints.md", "positions": [265]},
        {"doc": "configuration.md", "positions": [89]}
    ],
    "limiting": [
        {"doc": "api/endpoints.md", "positions": [270]},
        {"doc": "configuration.md", "positions": [95]}
    ]
}
```

**Search algorithm:**
```python
def search_with_inverted_index(query: str) -> list:
    terms = query.lower().split()
    
    # Get docs for each term (O(1) hash lookup per term)
    docs_per_term = [inverted_index.get(term, []) for term in terms]
    
    # Find docs containing ALL terms (intersection)
    common_docs = set(docs_per_term[0]) & set(docs_per_term[1]) & ...
    
    # Score based on:
    # - Number of occurrences
    # - Position (title > heading > content)
    # - Proximity of terms
    
    return sorted_by_score(common_docs)
```

**Performance:**
- **Build:** 1-2 seconds for 500 files (parse + tokenize + build map)
- **Search:** 10-50ms (hash lookups + scoring, not linear scan!)
- **Memory:** ~20-30MB for 500 files (depends on vocabulary size)

**Pros:**
- ✅ **Lightning fast search** (O(log n) instead of O(n))
- ✅ Industry standard (proven approach)
- ✅ Supports phrase queries ("rate limiting")
- ✅ Can do proximity scoring (terms close together = higher score)
- ✅ Easy to extend (stopwords, stemming, etc.)

**Cons:**
- ❌ More complex build process
- ❌ Larger memory footprint

**Libraries to consider:**
- `Whoosh` - Pure Python search engine (lightweight, no C deps)
- `tantivy-py` - Python bindings to Rust's Tantivy (ultra fast)
- Roll our own (educational, full control)

---

### Option 2: Trie (Prefix Tree) for Fast Prefix Search

**Concept:** Tree structure for fast prefix matching

**Structure:**
```
         root
        /  |  \
       a   r   s
      /    |    \
     u     a     e
    /      |      \
   t       t       c
  /        |        \
 h         e         ...
(auth*)   (rate*)
```

**Use case:** 
- Fast autocomplete: "auth" → finds "authentication", "authorize", "auth"
- Good for prefix queries: "docker*" → "docker", "dockerfile", "docker-compose"

**Performance:**
- **Build:** 0.5-1 second for 500 files
- **Search:** <10ms for prefix queries
- **Memory:** ~5-10MB

**Pros:**
- ✅ Very fast prefix matching
- ✅ Low memory (shared prefixes)
- ✅ Good for autocomplete

**Cons:**
- ❌ Only works for prefix queries (not full-text)
- ❌ Doesn't handle "rate limiting" well (two words)

**Best for:** Autocomplete feature (future enhancement)

---

### Option 3: Suffix Array + BWT (Advanced String Matching)

**Concept:** Burrows-Wheeler Transform + Suffix Array for substring search

**What it does:**
- Can find ANY substring in O(log n) time
- Used in bioinformatics (DNA sequence matching)

**Performance:**
- **Build:** 2-3 seconds for 500 files
- **Search:** <5ms for exact substring
- **Memory:** ~50MB (stores all suffixes)

**Pros:**
- ✅ Ultra-fast substring search
- ✅ Handles typos well with BWT

**Cons:**
- ❌ Complex algorithm (hard to maintain)
- ❌ High memory usage
- ❌ Overkill for documentation search

**Best for:** Specialized use cases (not recommended here)

---

### Option 4: Hybrid: Inverted Index + N-grams for Fuzzy

**Concept:** Combine inverted index with character n-grams for fuzzy matching

**Structure:**
```python
# Inverted index (exact words)
word_index = {
    "authentication": [...],
    "rate": [...]
}

# N-gram index (character sequences for fuzzy)
ngram_index = {
    "aut": ["authentication", "authorize", "author"],
    "uth": ["authentication"],
    "the": ["authentication", "the", "other"],
    # 3-character sliding window
}
```

**Search algorithm:**
```python
def fuzzy_search(query: str, threshold: float = 0.8):
    # Try exact match first (inverted index)
    exact_results = search_inverted_index(query)
    
    if exact_results:
        return exact_results
    
    # Fallback: fuzzy search with n-grams
    query_ngrams = generate_ngrams(query, n=3)
    
    # Find words with similar n-grams
    similar_words = []
    for ngram in query_ngrams:
        similar_words.extend(ngram_index.get(ngram, []))
    
    # Score by n-gram overlap
    candidates = score_by_overlap(similar_words, query_ngrams)
    
    # Search using similar words
    return search_inverted_index(candidates)
```

**Performance:**
- **Build:** 2-3 seconds for 500 files
- **Search (exact):** 10-50ms
- **Search (fuzzy):** 50-100ms
- **Memory:** ~40MB

**Pros:**
- ✅ Fast exact search (inverted index)
- ✅ Handles typos (n-grams)
- ✅ Best of both worlds

**Cons:**
- ❌ More memory
- ❌ Complex implementation

**Best for:** Production search with typo tolerance

---

## Comparison: Data Structures

| Structure | Build Time | Search Time | Memory | Fuzzy? | Best For |
|-----------|-----------|-------------|---------|--------|----------|
| **Linear Scan** (current) | 0.5s | **500ms** ❌ | 10MB | No | <100 docs |
| **Inverted Index** ⭐ | 2s | **20ms** ✅ | 30MB | No | **Recommended** |
| **Inverted + N-grams** | 3s | 50ms | 40MB | Yes | Production++ |
| **Trie** | 1s | 10ms | 10MB | No | Autocomplete |
| **Suffix Array** | 3s | 5ms | 50MB | Yes | Overkill |

---

## Go/Rust Libraries to Consider

### Option A: Use Tantivy (Rust) via Python Bindings

**Tantivy:** Full-text search engine in Rust (like Lucene but faster)

```bash
pip install tantivy
```

```python
import tantivy

# Create schema
schema_builder = tantivy.SchemaBuilder()
schema_builder.add_text_field("title", stored=True)
schema_builder.add_text_field("content", stored=True)
schema_builder.add_text_field("path", stored=True)
schema = schema_builder.build()

# Create index
index = tantivy.Index(schema, path="/app/cache/mcp/tantivy/")

# Index documents
writer = index.writer()
for doc in docs:
    writer.add_document(tantivy.Document(
        title=doc["title"],
        content=doc["content"],
        path=doc["path"]
    ))
writer.commit()

# Search (FAST!)
searcher = index.searcher()
query = index.parse_query("rate limiting", ["title", "content"])
results = searcher.search(query, limit=10)
```

**Performance:**
- **Build:** 0.5-1 second for 500 files (Rust speed!)
- **Search:** <10ms (compiled Rust)
- **Memory:** ~20MB (efficient Rust allocations)

**Pros:**
- ✅ **Blazing fast** (Rust performance)
- ✅ Battle-tested (used in production)
- ✅ Full-text search features (phrases, fuzzy, filters)
- ✅ Persistent index (saves to disk)
- ✅ Easy Python API

**Cons:**
- ❌ External dependency (C extension)
- ❌ Larger binary size
- ❌ Platform-specific builds

**Verdict:** **Best option if you're okay with Rust dependency**

---

### Option B: Whoosh (Pure Python)

**Whoosh:** Pure Python search engine (slower than Tantivy but no C deps)

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

# Create schema
schema = Schema(
    path=ID(stored=True),
    title=TEXT(stored=True),
    content=TEXT
)

# Create index
ix = index.create_in("/app/cache/mcp/whoosh/", schema)

# Index documents
writer = ix.writer()
for doc in docs:
    writer.add_document(
        path=doc["path"],
        title=doc["title"],
        content=doc["content"]
    )
writer.commit()

# Search
with ix.searcher() as searcher:
    query = QueryParser("content", ix.schema).parse("rate limiting")
    results = searcher.search(query)
```

**Performance:**
- **Build:** 1-2 seconds for 500 files (pure Python)
- **Search:** 20-50ms (Python speed)
- **Memory:** ~30MB

**Pros:**
- ✅ Pure Python (no C deps)
- ✅ Easy to install
- ✅ Full-text search features
- ✅ Persistent index

**Cons:**
- ❌ Slower than Tantivy (but still fast enough!)
- ❌ Larger memory footprint

**Verdict:** **Good balance: no C deps but still fast**

---

### Option C: Roll Our Own Inverted Index

**Custom implementation:** Full control, educational

```python
from collections import defaultdict
import re

class SimpleInvertedIndex:
    def __init__(self):
        self.index = defaultdict(list)  # word -> list of (doc, positions)
        self.docs = {}  # doc_id -> full doc info
    
    def add_document(self, doc_id: str, title: str, content: str):
        """Add document to index"""
        self.docs[doc_id] = {"title": title, "content": content}
        
        # Tokenize and index
        words = self._tokenize(content)
        for position, word in enumerate(words):
            self.index[word].append({
                "doc_id": doc_id,
                "position": position,
                "in_title": word in self._tokenize(title)
            })
    
    def search(self, query: str, limit: int = 10) -> list:
        """Search for documents"""
        query_terms = self._tokenize(query)
        
        # Get postings for each term
        postings = [self.index.get(term, []) for term in query_terms]
        
        # Find docs containing all terms
        doc_scores = defaultdict(float)
        for term_postings in postings:
            for posting in term_postings:
                doc_id = posting["doc_id"]
                
                # Score: title match = 100, content = 1
                score = 100 if posting["in_title"] else 1
                doc_scores[doc_id] += score
        
        # Sort by score
        results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                "doc_id": doc_id,
                "score": score,
                "title": self.docs[doc_id]["title"]
            }
            for doc_id, score in results[:limit]
        ]
    
    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization"""
        return re.findall(r'\w+', text.lower())
```

**Performance:**
- **Build:** 1-2 seconds for 500 files
- **Search:** 30-50ms
- **Memory:** ~25MB

**Pros:**
- ✅ No dependencies
- ✅ Full control
- ✅ Easy to understand and maintain
- ✅ Can customize for our use case

**Cons:**
- ❌ Missing advanced features (stemming, fuzzy, etc.)
- ❌ Not as optimized as libraries

**Verdict:** **Good for MVP, upgrade to Whoosh/Tantivy later**

---

## My Recommendation

### Phase 1 (MVP): Roll Our Own Inverted Index

**Why:**
- ✅ No new dependencies
- ✅ Fast enough (<50ms search)
- ✅ Builds in <2 seconds
- ✅ Easy to understand/maintain
- ✅ Proves the concept

**Implementation:** ~200 lines of Python

### Phase 2 (Production): Upgrade to Whoosh

**Why:**
- ✅ Still pure Python (easy install)
- ✅ Production-tested
- ✅ Better search quality (stemming, stopwords)
- ✅ Persistent index (save to disk)
- ✅ Only 1 new dependency

**If you need extreme speed:** Use Tantivy (Rust) instead

---

## Proposed Architecture

```
Startup (5-10 seconds acceptable):
├─ Scan DOCS_ROOT for *.md files
├─ Build inverted index:
│  ├─ Tokenize each file (title, content, sections)
│  ├─ Build word → documents map
│  └─ Calculate document statistics
├─ Save index to CACHE_ROOT/mcp/index.db
└─ Log: "✅ Indexed 237 documents in 2.3s"

Search Request (10-50ms):
├─ Parse query into terms
├─ Lookup terms in inverted index (O(1) hash lookup)
├─ Score documents (term frequency, position, etc.)
├─ Return top N results
└─ Extract snippets from original content
```

---

## Health Endpoint Strategy

```python
@app.get("/health/ready")
async def readiness_check():
    """k8s readiness probe"""
    
    # Check if index exists
    if settings.MCP_ENABLED:
        index_ready = check_mcp_index_ready()
        
        if not index_ready:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "MCP index building",
                    "retry_after": 5
                }
            )
    
    return {"status": "ready"}
```

**k8s config:**
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
  initialDelaySeconds: 10  # Give time to build index
  periodSeconds: 5
  failureThreshold: 3      # Allow 15s total (3 × 5s)
```

---

## Decision Time

**My recommendation for your use case:**

1. **Start with custom inverted index** (Phase 1)
   - Builds in <2 seconds for 500 files
   - Searches in <50ms
   - No new dependencies
   - ~200 lines of clean Python

2. **Health endpoints** with index readiness check
   - `/health/ready` waits for index
   - k8s `initialDelaySeconds: 10`
   - Rolling updates work fine (5-10s is acceptable)

3. **Future upgrade to Whoosh** (Phase 2)
   - When you need better search quality
   - When you want persistent index
   - Easy migration path (same concepts)

4. **Consider Tantivy** (Phase 3)
   - If you need <10ms search
   - If you have 1000+ documents
   - If you're okay with Rust dependency

---

## What do you think?

- Start with custom inverted index (fast enough, no deps)?
- Or go straight to Whoosh (proven, still pure Python)?
- Or full Rust with Tantivy (ultra fast, but C extension)?

And: Should we add fuzzy search from day 1, or add it later?
