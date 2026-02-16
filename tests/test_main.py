"""
Unit tests for main module.
Tests CLI argument parsing and main() entry point behavior.
"""

import sys
from unittest.mock import patch


def test_main_calls_clear_cache_when_flag_passed():
    """Test that main() calls settings.clear_cache() when --clear-cache is passed"""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        with patch.object(sys, "argv", ["docs_server", "--clear-cache"]):
            from docs_server.main import main

            main()

        mock_settings.clear_cache.assert_called_once()
        mock_uvicorn.assert_called_once()


def test_main_does_not_call_clear_cache_without_flag():
    """Test that main() does not call settings.clear_cache() when flag is omitted"""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        with patch.object(sys, "argv", ["docs_server"]):
            from docs_server.main import main

            main()

        mock_settings.clear_cache.assert_not_called()
        mock_uvicorn.assert_called_once()


def test_main_parses_clear_cache_with_other_args():
    """Test that --clear-cache is parsed correctly alongside other args (parse_known_args)"""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        with patch.object(sys, "argv", ["docs_server", "--clear-cache", "extra"]):
            from docs_server.main import main

            main()

        mock_settings.clear_cache.assert_called_once()
        mock_uvicorn.assert_called_once()
