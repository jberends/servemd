"""
FastAPI Documentation Server - KLO-519
A lightweight documentation server for serving markdown files as HTML.
Inspired by Nuxt UI design system and documentation patterns.
"""

import html
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import __version__
from .caching import get_cached_html, get_cached_llms, save_cached_html, save_cached_llms
from .config import settings
from .helpers import (
    build_chatgpt_url,
    build_claude_url,
    build_mistral_url,
    extract_table_of_contents,
    format_search_results_human,
    get_custom_css_path,
    get_file_path,
    parse_sidebar_navigation,
    parse_topbar_links,
    path_to_doc_url,
)
from .llms_service import generate_llms_txt_content
from .markdown_service import render_markdown_to_html
from .templates import create_html_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter for MCP endpoint
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Handles MCP search index initialization and cleanup.
    """
    # Startup
    if settings.MCP_ENABLED:
        try:
            from .mcp import get_index_manager

            manager = get_index_manager()
            success = await manager.initialize()

            if success:
                logger.info(f"🔍 MCP search index ready ({manager.get_backend().get_doc_count()} docs)")
            else:
                logger.warning("⚠️ MCP search index initialization failed - search may be unavailable")

        except Exception as e:
            logger.error(f"Failed to initialize MCP index: {e}", exc_info=True)
            # Don't fail startup - MCP is optional feature
    else:
        logger.info("MCP disabled, skipping index initialization")

    yield  # Application runs here

    # Shutdown
    if settings.MCP_ENABLED:
        try:
            from .mcp import get_index_manager

            manager = get_index_manager()
            manager.shutdown()
            logger.debug("MCP search index shutdown complete")
        except Exception as e:
            logger.warning(f"Error during MCP shutdown: {e}")


# FastAPI app initialization
app = FastAPI(
    title="ServeMD Documentation Server",
    description="Lightweight documentation server with Nuxt UI-inspired design",
    version=__version__,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded errors with JSON-RPC error format.
    Returns a proper JSON-RPC error response for MCP clients.
    """
    # Try to extract request ID from body for JSON-RPC compliance
    request_id = None
    try:
        body = await request.json()
        request_id = body.get("id")
    except Exception:
        pass  # Body might not be JSON or already consumed

    # Calculate retry after (extract from exc or use default)
    retry_after = settings.MCP_RATE_LIMIT_WINDOW

    # Structured logging for rate limit hits
    ip = get_remote_address(request)
    logger.warning(
        f"[MCP] rate limit exceeded ip={ip} limit={settings.MCP_RATE_LIMIT_REQUESTS}/{settings.MCP_RATE_LIMIT_WINDOW}s"
    )

    return JSONResponse(
        status_code=429,
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": "Rate limit exceeded",
                "data": {
                    "retryAfter": retry_after,
                    "limit": f"{settings.MCP_RATE_LIMIT_REQUESTS}/{settings.MCP_RATE_LIMIT_WINDOW}s",
                },
            },
        },
    )


# Mount static files for assets (images, logos, etc.)
assets_path = settings.DOCS_ROOT / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    logger.info(f"Mounted assets directory: {assets_path}")
else:
    logger.warning(f"Assets directory not found: {assets_path}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "docs_root": str(settings.DOCS_ROOT.absolute()),
        "cache_root": str(settings.CACHE_ROOT.absolute()),
        "debug": settings.DEBUG,
        "mcp_enabled": settings.MCP_ENABLED,
    }


@app.post("/mcp")
@limiter.limit(f"{settings.MCP_RATE_LIMIT_REQUESTS}/{settings.MCP_RATE_LIMIT_WINDOW}second")
async def mcp_endpoint(request: Request):
    """
    MCP (Model Context Protocol) endpoint.
    Handles JSON-RPC 2.0 requests from LLM clients.

    Rate limited to MCP_RATE_LIMIT_REQUESTS per MCP_RATE_LIMIT_WINDOW seconds.
    Default: 120 requests per 60 seconds per IP.

    Supports:
    - initialize: Handshake and capability negotiation
    - tools/list: List available tools
    - tools/call: Execute a tool (search_docs, get_doc_page, list_doc_pages)
    """
    if not settings.MCP_ENABLED:
        return JSONResponse(
            status_code=404,
            content={"error": "MCP endpoint is disabled"},
        )

    try:
        body = await request.json()
    except Exception as e:
        logger.warning(f"MCP: Invalid JSON in request: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error: Invalid JSON",
                },
            }
        )

    # Import here to avoid circular imports
    from .mcp import handle_request

    # Structured logging for MCP requests
    method = body.get("method", "unknown")
    request_id = body.get("id", "none")
    logger.info(f"[MCP] method={method} id={request_id}")
    result = await handle_request(body)
    return JSONResponse(content=result)


@app.get("/llms.txt")
async def serve_llms_txt(request: Request):
    """
    Serve llms.txt with fallback strategy:
    1. PRIMARY: Serve curated llms.txt from DOCS_ROOT if exists
    2. FALLBACK: Generate from sidebar.md + index.md
    Implements caching similar to HTML files.
    """
    # Check cache first
    cache_file = "llms.txt"
    cached = await get_cached_llms(cache_file)
    if cached:
        logger.debug("Serving cached llms.txt")
        return PlainTextResponse(content=cached, media_type="text/plain; charset=utf-8")

    try:
        # Get base URL from environment or request
        base_url = settings.BASE_URL if settings.BASE_URL else str(request.base_url).rstrip("/")

        # Generate content using helper function
        result = await generate_llms_txt_content(base_url)

        # Cache the result
        await save_cached_llms(cache_file, result)

        logger.info(f"Generated and cached llms.txt (base_url: {base_url})")
        return PlainTextResponse(content=result, media_type="text/plain; charset=utf-8")

    except Exception as e:
        logger.error(f"Error generating llms.txt: {e}")
        raise HTTPException(status_code=500, detail="Error generating llms.txt") from e


@app.get("/llms-full.txt")
async def serve_llms_full_txt(request: Request):
    """
    Serve llms-full.txt: expanded version with all linked content.
    Uses XML-style structure for LLM consumption (Claude format).
    """
    # Check cache first
    cache_file = "llms-full.txt"
    cached = await get_cached_llms(cache_file)
    if cached:
        logger.debug("Serving cached llms-full.txt")
        return PlainTextResponse(content=cached, media_type="text/plain; charset=utf-8")

    try:
        # Get base URL from environment or request
        base_url = settings.BASE_URL if settings.BASE_URL else str(request.base_url).rstrip("/")

        # Generate llms.txt content using helper function
        llms_content = await generate_llms_txt_content(base_url)

        # Parse all .md links (both absolute and relative)
        # Pattern matches absolute URLs with .md extension
        pattern = r"\[([^\]]+)\]\((https?://[^)]+\.md(?:#[^)]*)?)\)"
        links = re.findall(pattern, llms_content)

        # Start with the index content
        result = llms_content + "\n\n"

        # Fetch and append each linked page
        seen_urls = set()
        for _title, url in links:
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Extract relative path from absolute URL
            # Remove the base_url prefix and any anchor
            rel_path = url.replace(base_url + "/", "").replace(base_url, "").lstrip("/")
            rel_path = rel_path.split("#")[0]  # Remove anchor

            file_path = settings.DOCS_ROOT / rel_path

            if file_path.exists():
                try:
                    page_content = file_path.read_text(encoding="utf-8")
                    result += f"\n<url>{url}</url>\n<content>\n{page_content}\n</content>\n"
                    logger.debug(f"Added to llms-full.txt: {rel_path}")
                except (OSError, UnicodeDecodeError) as e:
                    logger.warning(f"Error reading {rel_path}: {e}")
                    continue
            else:
                logger.debug(f"File not found for llms-full.txt: {rel_path}")

        # Cache the result
        await save_cached_llms(cache_file, result)

        logger.info(f"Generated and cached llms-full.txt with {len(seen_urls)} pages")
        return PlainTextResponse(content=result, media_type="text/plain; charset=utf-8")

    except Exception as e:
        logger.error(f"Error generating llms-full.txt: {e}")
        raise HTTPException(status_code=500, detail="Error generating llms-full.txt") from e


@app.get("/")
async def root():
    """Redirect root to index.html"""
    return RedirectResponse(url="/index.html", status_code=302)


@app.get("/search")
async def search_page(q: str = "", format: str = ""):
    """
    Search documentation. Displays results in main content area with sidebar and topbar.

    Supports two response formats:
    - HTML (default): Full page with searchbar + searchresults layout
    - JSON (format=json): HTML fragment of results for client-side live search

    Empty or whitespace-only query:
    - HTML: shows the search page with empty results prompt
    - JSON: returns empty results
    """
    query = q.strip() if q else ""
    is_json = format.lower() == "json"

    # JSON format: return structured response for client-side fetch
    if is_json:
        return await _search_json_response(query)

    # HTML format: full search page with searchbar + searchresults layout
    return await _search_html_response(query)


async def _search_json_response(query: str) -> JSONResponse:
    """Return search results as JSON with a pre-rendered HTML fragment."""
    if not query:
        return JSONResponse(content={"query": "", "count": 0, "results": [], "html": ""})

    # Check availability
    if not settings.MCP_ENABLED:
        return JSONResponse(
            content={
                "query": query,
                "count": 0,
                "results": [],
                "html": "<p class='search-no-results'>Search is not available.</p>",
            }
        )

    try:
        from .mcp import get_index_manager

        manager = get_index_manager()
        if not manager.is_initialized:
            return JSONResponse(
                content={
                    "query": query,
                    "count": 0,
                    "results": [],
                    "html": "<p class='search-no-results'>Search will be available once the index is built.</p>",
                }
            )
    except Exception as e:
        logger.warning(f"Search index check failed: {e}")
        return JSONResponse(
            content={
                "query": query,
                "count": 0,
                "results": [],
                "html": "<p class='search-no-results'>Search will be available once the index is built.</p>",
            }
        )

    try:
        from .mcp import search_docs

        results = search_docs(query=query)
    except RuntimeError as e:
        logger.warning(f"Search failed: {e}")
        return JSONResponse(
            content={
                "query": query,
                "count": 0,
                "results": [],
                "html": "<p class='search-no-results'>Search will be available once the index is built.</p>",
            }
        )

    # Build JSON payload with pre-rendered HTML fragment
    results_html = format_search_results_human(results, query)
    results_data = [
        {
            "title": r.title,
            "path": r.path,
            "url": path_to_doc_url(r.path),
            "snippet": r.snippet,
            "score": round(r.score, 2),
            "category": r.category,
        }
        for r in results
    ]
    return JSONResponse(
        content={
            "query": query,
            "count": len(results),
            "results": results_data,
            "html": results_html,
        }
    )


async def _search_html_response(query: str) -> HTMLResponse | RedirectResponse:
    """Return the full search page with searchbar + searchresults layout."""
    navigation = parse_sidebar_navigation()
    topbar_sections = parse_topbar_links()

    # Determine results HTML fragment
    results_html = ""
    unavailable_msg = "<p class='search-no-results'>Search will be available once the index is built.</p>"

    if not settings.MCP_ENABLED:
        results_html = unavailable_msg
    elif query:
        try:
            from .mcp import get_index_manager

            manager = get_index_manager()
            if not manager.is_initialized:
                results_html = unavailable_msg
            else:
                from .mcp import search_docs

                results = search_docs(query=query)
                results_html = format_search_results_human(results, query)
        except RuntimeError as e:
            logger.warning(f"Search failed: {e}")
            results_html = unavailable_msg
        except Exception as e:
            logger.warning(f"Search index check failed: {e}")
            results_html = unavailable_msg

    # Build the search page content: searchbar div + searchresults div
    import html as html_mod

    safe_query = html_mod.escape(query, quote=True) if query else ""
    content_html = f"""<div class="search-page">
    <form action="/search" method="GET" class="search-page-form" id="search-page-form">
        <span class="search-input-wrap">
            <input type="text" name="q" placeholder="Search documentation..." value="{safe_query}"
                   class="search-input" id="search-page-input" autocomplete="off" autofocus>
        </span>
        <button type="submit" class="search-page-btn">Search</button>
    </form>
    <div class="search-page-results" id="search-page-results">
        {results_html}
    </div>
</div>"""

    title = f"Search: {query} - Documentation" if query else "Search - Documentation"
    full_html = create_html_template(
        content_html,
        title=title,
        current_path="/search",
        navigation=navigation,
        topbar_sections=topbar_sections,
        toc_items=[],
        show_search=settings.MCP_ENABLED,
        search_query=query,
        is_search_page=True,
        show_branding=settings.SERVEMD_BRANDING_ENABLED,
        custom_css_url="/custom.css" if get_custom_css_path() else None,
    )
    return HTMLResponse(content=full_html)


@app.get("/custom.css")
async def serve_custom_css():
    """
    Serve custom CSS file from DOCS_ROOT.
    Filename is from CUSTOM_CSS env var (default: custom.css).
    Returns 404 if file does not exist.
    """
    css_path = get_custom_css_path()
    if not css_path:
        raise HTTPException(status_code=404, detail="Custom CSS file not found")
    cache_control = "no-cache" if settings.DEBUG else "max-age=3600"
    return FileResponse(
        path=str(css_path),
        media_type="text/css",
        headers={"Cache-Control": cache_control},
    )


def _serve_html_in_iframe(path: str, file_path: Path) -> HTMLResponse:
    """Wrap a raw HTML file from DOCS_ROOT in the doc template via an iframe."""
    navigation = parse_sidebar_navigation()
    topbar_sections = parse_topbar_links()

    title = f"{file_path.stem.replace('_', ' ').title()} - Documentation"
    current_path = f"/{path}" if path and not path.startswith("/") else path

    if not re.fullmatch(r"[A-Za-z0-9._\-/]+", path):
        raise HTTPException(status_code=400, detail="Invalid path")

    safe_src = quote(path, safe="/")
    safe_title = html.escape(file_path.stem, quote=True)
    iframe_content = f'<iframe src="/raw/{safe_src}" class="html-embed-frame" title="{safe_title}"></iframe>'

    full_html = create_html_template(
        iframe_content,
        title,
        current_path,
        navigation,
        topbar_sections,
        toc_items=[],
        show_search=settings.MCP_ENABLED,
        show_branding=settings.SERVEMD_BRANDING_ENABLED,
        page_actions=None,
        custom_css_url="/custom.css" if get_custom_css_path() else None,
    )

    return HTMLResponse(content=full_html)


@app.get("/raw/{path:path}")
async def serve_raw_file(path: str):
    """
    Serve a file from DOCS_ROOT as-is, without template wrapping.
    Used by the iframe embed for HTML files to avoid recursive template rendering.
    """
    file_path = get_file_path(path)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    suffix = file_path.suffix.lower()
    media_types = {
        ".html": "text/html",
        ".htm": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    safe_log_path = path.replace("\r", "").replace("\n", "")
    logger.debug(f"Serving raw file: {safe_log_path} ({media_type})")
    return FileResponse(path=str(file_path), media_type=media_type)


@app.get("/{path:path}")
async def serve_content(path: str, request: Request):
    """
    Main content serving endpoint with dual routing:
    - .md files: serve raw markdown
    - .html files: serve rendered HTML with template
    - other files: serve as static assets
    """
    if not path:
        return RedirectResponse(url="/index.html", status_code=302)

    # Handle .html requests (rendered markdown)
    if path.endswith(".html"):
        md_path = path[:-5] + ".md"  # Convert .html to .md
        file_path = get_file_path(md_path)

        if not file_path:
            # Fallback: check if a raw .html file exists in DOCS_ROOT
            html_file_path = get_file_path(path)
            if html_file_path:
                return _serve_html_in_iframe(path, html_file_path)
            raise HTTPException(status_code=404, detail="File not found")

        # Check cache first
        cached_html = await get_cached_html(file_path)
        if cached_html:
            logger.debug(f"Serving cached HTML: {path}")
            return HTMLResponse(content=cached_html)

        # Read and render markdown
        try:
            markdown_content = file_path.read_text(encoding="utf-8")
            html_content = await render_markdown_to_html(markdown_content, file_path)

            # Parse navigation
            navigation = parse_sidebar_navigation()
            topbar_sections = parse_topbar_links()

            # Extract table of contents from the rendered HTML
            toc_items = extract_table_of_contents(html_content)

            # Create full HTML document with styling and navigation
            title = f"{file_path.stem.replace('_', ' ').title()} - Documentation"
            page_title = file_path.stem.replace("_", " ").title()
            # Root-relative path for active state (matches sidebar/topbar link format)
            current_path = f"/{path}" if path and not path.startswith("/") else path
            current_doc_path = path[:-5] if path.endswith(".html") else path  # e.g. features/mcp

            # Build page actions (Copy page dropdown with AI links)
            if settings.BASE_URL:
                base_url = settings.BASE_URL
            else:
                base_url = str(request.base_url).rstrip("/")
                # Respect X-Forwarded-Proto from reverse proxies that terminate SSL
                forwarded_proto = request.headers.get("x-forwarded-proto", "")
                if forwarded_proto == "https" and base_url.startswith("http://"):
                    base_url = "https://" + base_url[7:]
            raw_md_url = f"{base_url}/{current_doc_path}.md"
            page_url = f"{base_url}{current_path}" if current_path.startswith("/") else f"{base_url}/{current_path}"
            page_actions = {
                "raw_md_url": raw_md_url,
                "page_url": page_url,
                "page_title": page_title,
                "chatgpt_url": build_chatgpt_url(raw_md_url),
                "claude_url": build_claude_url(raw_md_url),
                "mistral_url": build_mistral_url(raw_md_url),
            }

            full_html = create_html_template(
                html_content,
                title,
                current_path,
                navigation,
                topbar_sections,
                toc_items,
                show_search=settings.MCP_ENABLED,
                show_branding=settings.SERVEMD_BRANDING_ENABLED,
                page_actions=page_actions,
                custom_css_url="/custom.css" if get_custom_css_path() else None,
            )

            # Cache the rendered HTML
            await save_cached_html(file_path, full_html)

            logger.info(f"Rendered and cached: {path}")
            return HTMLResponse(content=full_html)

        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}") from e

    # Handle .md requests (raw markdown)
    elif path.endswith(".md"):
        file_path = get_file_path(path)

        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")

        try:
            content = file_path.read_text(encoding="utf-8")
            logger.debug(f"Serving raw markdown: {path}")
            return PlainTextResponse(content=content, media_type="text/markdown")
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}") from e

    # Handle static assets (images, PDFs, etc.)
    else:
        file_path = get_file_path(path)

        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")

        # Determine media type based on extension
        suffix = file_path.suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
            ".mp4": "video/mp4",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
        }

        media_type = media_types.get(suffix, "application/octet-stream")

        logger.debug(f"Serving asset: {path} ({media_type})")
        return FileResponse(path=str(file_path), media_type=media_type, filename=file_path.name)


def main():
    """Main entry point for the application"""
    import argparse
    import sys

    import uvicorn

    parser = argparse.ArgumentParser(description="ServeMD Documentation Server")
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the cache directory on startup before serving",
    )
    args, _ = parser.parse_known_args(sys.argv[1:])

    if args.clear_cache:
        settings.clear_cache()

    logger.info("🚀 Starting ServeMD Documentation Server...")
    logger.info(f"🌐 Server will be available at: http://localhost:{settings.PORT}")
    logger.info("📖 Try these URLs:")
    logger.info(f"   - http://localhost:{settings.PORT}/ (redirects to index.html)")
    logger.info(f"   - http://localhost:{settings.PORT}/index.html (rendered HTML)")
    logger.info(f"   - http://localhost:{settings.PORT}/index.md (raw markdown)")
    logger.info(f"   - http://localhost:{settings.PORT}/health")

    uvicorn.run(
        "docs_server.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )


if __name__ == "__main__":
    main()
