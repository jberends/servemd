# Search Library: Whoosh-Reloaded

## Current Status: Whoosh-Reloaded ✅

ServeM currently uses [Whoosh-Reloaded](https://pypi.org/project/Whoosh-Reloaded/) (v2.7.5) for full-text search in the MCP (Model Context Protocol) feature. Whoosh-Reloaded is a community-maintained fork of the original Whoosh library with Python 3.x compatibility fixes.

### Why Whoosh-Reloaded?

- **Clean Python 3.13+ support**: No SyntaxWarnings or compatibility issues
- **Drop-in replacement**: Compatible API with original Whoosh
- **Pure Python**: No compilation or binary dependencies needed
- **Battle-tested**: Based on mature, well-tested Whoosh codebase
- **Works well**: Stable and performant for ServeM's use case

### Migration from Original Whoosh

If migrating from original Whoosh (v2.7.4), simply update the dependency:

```toml
# Old
dependencies = ["whoosh>=2.7.4"]

# New
dependencies = ["whoosh-reloaded>=2.7.5"]
```

No code changes required - it's a drop-in replacement!

## Maintenance Status

**Note**: While Whoosh-Reloaded is marked as "no longer maintained" (as of 2024), the v2.7.5 release includes all necessary fixes for modern Python versions. The library is stable and works perfectly for ServeM's needs.

## Recommended Alternative: Tantivy

**Status**: ✅ Actively maintained (latest release Dec 2025)

[Tantivy](https://pypi.org/project/tantivy/) is a modern full-text search library with Python bindings for the Rust-based Tantivy search engine.

### Advantages

- **Actively maintained**: Regular releases throughout 2025
- **Modern Python support**: Requires Python ≥ 3.9, actively tested on latest versions
- **Fast performance**: Rust-based engine with significant performance improvements over pure-Python solutions
- **Feature-rich**: Supports fuzzy search, boolean queries, phrase queries, and more
- **Production-ready**: Used in production by many companies

### Migration Path

If you decide to migrate from Whoosh to Tantivy:

1. **Update dependencies** in `pyproject.toml`:
   ```toml
   dependencies = [
       # ... other deps
       "tantivy>=0.25.0",  # Replace whoosh>=2.7.4
   ]
   ```

2. **Update search backend** in `src/docs_server/mcp/`:
   - Rewrite `indexer.py` to use Tantivy's API
   - Update `search.py` query parsing for Tantivy
   - Adjust schema definitions in `schema.py`

3. **Test thoroughly**:
   - All MCP search functionality
   - Index building and updating
   - Query parsing and results

4. **Update documentation**:
   - Remove SyntaxWarning suppression code
   - Update MCP documentation with new search capabilities

### Tantivy Example

```python
import tantivy

# Create schema
schema_builder = tantivy.SchemaBuilder()
schema_builder.add_text_field("title", stored=True)
schema_builder.add_text_field("content", stored=True)
schema_builder.add_text_field("path", stored=True)
schema = schema_builder.build()

# Create index
index = tantivy.Index(schema, path="/path/to/index")

# Add documents
writer = index.writer()
writer.add_document(tantivy.Document(
    title=["Getting Started"],
    content=["This is the content..."],
    path=["/docs/quick-start.md"]
))
writer.commit()

# Search
searcher = index.searcher()
query = index.parse_query("getting started", ["title", "content"])
results = searcher.search(query, 10)
```

## Other Alternatives

### PyLucene / Lupyne

- **Pros**: Battle-tested, Java-based Lucene under the hood
- **Cons**: Requires JVM, more complex setup, heavier weight

### Elasticsearch / OpenSearch

- **Pros**: Enterprise-grade, distributed, feature-rich
- **Cons**: Requires separate service, overkill for ServeM's use case

## Recommendation

**Short term**: Continue using Whoosh with SyntaxWarning suppression. It works well for ServeM's use case.

**Long term**: Consider migrating to Tantivy when:
- You need better performance at scale
- You want active maintenance and Python 3.14+ support
- You have time for the migration effort (estimated 2-3 days of work)

The migration is **not urgent** but would future-proof the codebase and potentially improve search performance.
