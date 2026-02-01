"""
MCP CLI - Command-line tools for managing the MCP search index.

This module provides CLI commands for:
- Building the search index
- Validating cached index
- Invalidating (clearing) cached index
- Showing index statistics

Usage:
    uv run python -m docs_server.mcp.cli build
    uv run python -m docs_server.mcp.cli validate
    uv run python -m docs_server.mcp.cli info
    uv run python -m docs_server.mcp.cli invalidate
"""

import argparse
import asyncio
import json
import logging
import shutil
import sys
import warnings

# Suppress SyntaxWarnings from unmaintained whoosh library (Python 3.13 compatibility)
# These filters must be set before any whoosh imports
warnings.filterwarnings("ignore", category=SyntaxWarning, module="whoosh")
warnings.filterwarnings("ignore", message="invalid escape sequence", module="whoosh")
warnings.filterwarnings("ignore", message='"is" with .*int.*literal', module="whoosh")

from ..config import settings  # noqa: E402
from .indexer import get_index_manager  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def setup_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="servemd-mcp",
        description="MCP search index management tools for ServeMD",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build or rebuild the search index")
    build_parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild even if cache is valid",
    )

    # Validate command
    subparsers.add_parser("validate", help="Check if cached index is valid")

    # Info command
    subparsers.add_parser("info", help="Show index statistics and metadata")

    # Invalidate command
    invalidate_parser = subparsers.add_parser("invalidate", help="Clear cached index and metadata")
    invalidate_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )

    return parser


async def cmd_build(force: bool = False) -> int:
    """
    Build the search index.

    Args:
        force: Force rebuild even if cache is valid

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Building MCP search index...")
        logger.info(f"DOCS_ROOT: {settings.DOCS_ROOT.absolute()}")
        logger.info(f"CACHE_ROOT: {settings.CACHE_ROOT.absolute()}")

        manager = get_index_manager()
        success = await manager.initialize(force_rebuild=force)

        if success:
            doc_count = manager.get_backend().get_doc_count()
            logger.info(f"✅ Index built successfully ({doc_count} documents)")
            return 0
        else:
            logger.error("❌ Index build failed")
            return 1

    except Exception as e:
        logger.error(f"❌ Error during build: {e}", exc_info=True)
        return 1


async def cmd_validate() -> int:
    """
    Validate the cached index.

    Returns:
        Exit code (0 for valid, 1 for invalid)
    """
    try:
        index_path = settings.CACHE_ROOT / "mcp" / "whoosh"
        metadata_path = settings.CACHE_ROOT / "mcp" / "metadata.json"

        logger.info("Validating MCP search index cache...")
        logger.info(f"Index path: {index_path}")
        logger.info(f"Metadata path: {metadata_path}")

        # Check if files exist
        if not index_path.exists():
            logger.warning("❌ Index directory does not exist")
            return 1

        if not metadata_path.exists():
            logger.warning("❌ Metadata file does not exist")
            return 1

        # Try to load and validate
        manager = get_index_manager()
        if manager._validate_cache():
            logger.info("✅ Cache is valid")

            # Show metadata
            metadata = manager._load_cache_metadata()
            if metadata:
                logger.info(f"   Index version: {metadata.index_version}")
                logger.info(f"   Schema version: {metadata.schema_version}")
                logger.info(f"   Documents: {metadata.docs_count}")
                logger.info(f"   Built at: {metadata.built_at}")
                logger.info(f"   Build duration: {metadata.build_duration_ms}ms")

            return 0
        else:
            logger.warning("❌ Cache validation failed")
            logger.info("Possible reasons:")
            logger.info("  - Documentation files have changed")
            logger.info("  - Index version mismatch")
            logger.info("  - DOCS_ROOT path changed")
            logger.info("  - DEBUG mode is enabled")
            return 1

    except Exception as e:
        logger.error(f"❌ Error during validation: {e}", exc_info=True)
        return 1


async def cmd_info() -> int:
    """
    Show index statistics and metadata.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        index_path = settings.CACHE_ROOT / "mcp" / "whoosh"
        metadata_path = settings.CACHE_ROOT / "mcp" / "metadata.json"

        logger.info("MCP Search Index Information")
        logger.info("=" * 60)

        # Configuration
        logger.info("\n📋 Configuration:")
        logger.info(f"  DOCS_ROOT:    {settings.DOCS_ROOT.absolute()}")
        logger.info(f"  CACHE_ROOT:   {settings.CACHE_ROOT.absolute()}")
        logger.info(f"  MCP_ENABLED:  {settings.MCP_ENABLED}")
        logger.info(f"  DEBUG:        {settings.DEBUG}")

        # Index path info
        logger.info("\n📁 Index Paths:")
        logger.info(f"  Index dir:    {index_path}")
        logger.info(f"  Metadata:     {metadata_path}")

        # Check existence
        index_exists = index_path.exists()
        metadata_exists = metadata_path.exists()

        logger.info(f"  Index exists: {index_exists}")
        logger.info(f"  Metadata exists: {metadata_exists}")

        if index_exists:
            # Calculate size
            total_size = sum(f.stat().st_size for f in index_path.rglob("*") if f.is_file())
            logger.info(f"  Index size:   {total_size:,} bytes ({total_size / 1024:.1f} KB)")

        # Metadata details
        if metadata_exists:
            try:
                with open(metadata_path, encoding="utf-8") as f:
                    metadata = json.load(f)

                logger.info("\n📊 Index Metadata:")
                logger.info(f"  Index version:   {metadata.get('index_version', 'N/A')}")
                logger.info(f"  Schema version:  {metadata.get('schema_version', 'N/A')}")
                logger.info(f"  Document count:  {metadata.get('docs_count', 0)}")
                logger.info(f"  Built at:        {metadata.get('built_at', 'N/A')}")
                logger.info(f"  Build duration:  {metadata.get('build_duration_ms', 0)}ms")
                logger.info(f"  Whoosh version:  {metadata.get('whoosh_version', 'N/A')}")
                logger.info(f"  Python version:  {metadata.get('python_version', 'N/A')}")
                logger.info(f"  Docs hash:       {metadata.get('docs_hash', 'N/A')[:16]}...")

            except Exception as e:
                logger.warning(f"  Could not read metadata: {e}")

        # Validation status
        logger.info("\n✅ Cache Status:")
        manager = get_index_manager()
        is_valid = manager._validate_cache()
        logger.info(f"  Valid:        {is_valid}")

        if is_valid:
            logger.info("  Cache is ready to use")
        else:
            logger.info("  Cache needs rebuild")

        # Document counts
        if index_exists and is_valid:
            logger.info("\n📚 Document Statistics:")
            docs_count = len(list(settings.DOCS_ROOT.rglob("*.md")))
            logger.info(f"  Total .md files: {docs_count}")

            # Try to get indexed count
            try:
                await manager.initialize()
                indexed_count = manager.get_backend().get_doc_count()
                logger.info(f"  Indexed docs:    {indexed_count}")
            except Exception:
                pass

        logger.info("\n" + "=" * 60)
        return 0

    except Exception as e:
        logger.error(f"❌ Error getting info: {e}", exc_info=True)
        return 1


async def cmd_invalidate(confirm: bool = False) -> int:
    """
    Clear the cached index and metadata.

    Args:
        confirm: Skip confirmation prompt

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        cache_dir = settings.CACHE_ROOT / "mcp"

        if not cache_dir.exists():
            logger.info("ℹ️  Cache directory does not exist, nothing to clear")
            return 0

        # Confirmation prompt
        if not confirm:
            logger.warning(f"This will delete: {cache_dir}")
            response = input("Are you sure? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                logger.info("Cancelled")
                return 0

        # Remove cache directory
        logger.info("Removing MCP cache directory...")
        shutil.rmtree(cache_dir)
        logger.info("✅ Cache cleared successfully")
        logger.info("Next server startup will rebuild the index")

        return 0

    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}", exc_info=True)
        return 1


async def main() -> int:
    """Main CLI entry point."""
    parser = setup_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatch to command handlers
    if args.command == "build":
        return await cmd_build(force=args.force)
    elif args.command == "validate":
        return await cmd_validate()
    elif args.command == "info":
        return await cmd_info()
    elif args.command == "invalidate":
        return await cmd_invalidate(confirm=args.confirm)
    else:
        parser.print_help()
        return 1


def cli_main():
    """Synchronous wrapper for CLI entry point."""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
