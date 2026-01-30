"""
FastAPI Documentation Server - KLO-519
A lightweight documentation server for serving markdown files as HTML.
Inspired by Nuxt UI design system and documentation patterns.
"""

import logging
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .caching import get_cached_html, get_cached_llms, save_cached_html, save_cached_llms
from .config import settings
from .helpers import extract_table_of_contents, get_file_path, parse_sidebar_navigation, parse_topbar_links
from .llms_service import generate_llms_txt_content
from .markdown_service import render_markdown_to_html
from .templates import create_html_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="ServeMD Documentation Server",
    description="Lightweight documentation server with Nuxt UI-inspired design",
    version="1.0.0",
    debug=settings.DEBUG,
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
    }


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
            current_path = path  # The current .html path for active state
            full_html = create_html_template(html_content, title, current_path, navigation, topbar_sections, toc_items)

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
    import uvicorn

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
