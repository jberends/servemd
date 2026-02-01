# TODO: Future Enhancements

**Project:** ServeMD
**Status:** Active Development
**Last Updated:** 2026-01-31

---

## Active Tasks

### None

All planned features have been implemented ✅

---

## Completed Features

### ✅ Core Documentation Server
- [x] FastAPI-based web server
- [x] Markdown rendering with Pygments syntax highlighting
- [x] Three-column layout (sidebar, content, TOC)
- [x] Smart disk caching for HTML and llms.txt
- [x] Security: path validation and directory boundaries
- [x] Docker deployment with health checks

### ✅ AI Integration (llms.txt)
- [x] `/llms.txt` endpoint with auto-generation fallback
- [x] `/llms-full.txt` endpoint with complete context export
- [x] Absolute URL transformation for BASE_URL
- [x] Curated vs auto-generated strategy
- [x] 208 comprehensive tests

### ✅ Model Context Protocol (MCP)
- [x] `/mcp` endpoint with JSON-RPC 2.0 support
- [x] Whoosh full-text search engine integration
- [x] Hash-based cache validation strategy
- [x] Three MCP tools: search_docs, get_doc_page, list_doc_pages
- [x] Rate limiting with slowapi (120 req/min default)
- [x] Fuzzy search with typo tolerance
- [x] Field boosting (title 2x, headings 1.5x)
- [x] BM25 scoring algorithm
- [x] Snippet extraction with context
- [x] CLI tools for cache management
- [x] Comprehensive test coverage

### ✅ PyPI Publishing
- [x] Package metadata and classifiers
- [x] Dynamic versioning from `__init__.py`
- [x] GitHub Actions workflow for automated publishing
- [x] Trusted publishing (OIDC)
- [x] CHANGELOG.md
- [x] Version 0.1.0 released

### ✅ Docker Publishing
- [x] Multi-stage Dockerfile
- [x] Docker Hub publishing workflow
- [x] GHCR (GitHub Container Registry) support
- [x] Multi-platform builds (amd64, arm64)
- [x] Automated version tagging (semver + latest)
- [x] Docker Hub repository documentation

---

## Future Enhancements (Not Planned)

These are ideas for potential future improvements:

### Performance Optimizations
- [ ] In-memory LRU cache layer (reduce disk reads)
- [ ] Pre-rendering at build time (eliminate cold starts)
- [ ] CDN integration (offload static assets)
- [ ] Response compression (gzip/brotli)
- [ ] HTTP/2 server push

### Search Enhancements
- [ ] Upgrade to Tantivy (Rust) for 5000+ docs
- [ ] Semantic search with embeddings
- [ ] Search result ranking tuning
- [ ] Search suggestions/autocomplete
- [ ] Search analytics

### MCP Features
- [ ] MCP resources for documentation metadata
- [ ] Batch query support
- [ ] Search result pagination
- [ ] Advanced filters (date, size, type)
- [ ] Query performance metrics

### Documentation Features
- [ ] Dark mode toggle
- [ ] Print-friendly styles
- [ ] PDF export
- [ ] Version comparison
- [ ] Search within page
- [ ] Copy code button

### Developer Experience
- [ ] Hot reload for documentation changes
- [ ] Live preview mode
- [ ] Documentation linting
- [ ] Broken link checker
- [ ] Documentation coverage metrics

### Deployment
- [ ] Kubernetes Helm chart
- [ ] Terraform modules
- [ ] DigitalOcean 1-click app
- [ ] Railway/Render templates
- [ ] Metrics/observability integration

---

## Notes

- All current requirements have been met
- System is production-ready
- Future enhancements should be driven by user feedback
- Prefer simplicity over features

---

## References

- **SPECS.md** - Complete technical specification
- **README.md** - User documentation
- **CHANGELOG.md** - Version history
- **docs/** - Self-hosted documentation
