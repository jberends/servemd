"""
Unit tests for config module.
Tests Settings initialization and environment variable handling.
"""

import os
from pathlib import Path

import pytest


def test_settings_initialization():
    """Test that Settings initializes with default values"""
    from docs_server.config import Settings

    settings = Settings()

    assert settings.DOCS_ROOT is not None
    assert settings.CACHE_ROOT is not None
    assert settings.DEBUG in [True, False]
    assert isinstance(settings.PORT, int)
    assert settings.PORT > 0


def test_settings_default_values():
    """Test default values when no environment variables are set"""
    from docs_server.config import Settings

    # Clear any existing env vars
    for key in ["DOCS_ROOT", "CACHE_ROOT", "BASE_URL", "DEBUG", "PORT"]:
        os.environ.pop(key, None)

    settings = Settings()

    # Should use smart defaults
    assert settings.DEBUG is False
    assert settings.PORT == 8080
    assert settings.BASE_URL is None


def test_settings_environment_overrides(tmp_path, monkeypatch):
    """Test that environment variables override defaults"""
    from docs_server.config import Settings

    # Set environment variables
    test_docs = tmp_path / "docs"
    test_cache = tmp_path / "cache"
    test_docs.mkdir()
    test_cache.mkdir()

    monkeypatch.setenv("DOCS_ROOT", str(test_docs))
    monkeypatch.setenv("CACHE_ROOT", str(test_cache))
    monkeypatch.setenv("BASE_URL", "https://test.example.com")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")

    settings = Settings()

    assert settings.DOCS_ROOT == test_docs
    assert settings.CACHE_ROOT == test_cache
    assert settings.BASE_URL == "https://test.example.com"
    assert settings.DEBUG is True
    assert settings.PORT == 9000


def test_markdown_extensions_configured():
    """Test that markdown extensions are properly configured"""
    from docs_server.config import Settings

    settings = Settings()

    # Check essential extensions are present
    assert "codehilite" in settings.markdown_extensions
    assert "toc" in settings.markdown_extensions
    assert "tables" in settings.markdown_extensions
    assert "fenced_code" in settings.markdown_extensions
    assert "pymdownx.superfences" in settings.markdown_extensions
    assert "pymdownx.tasklist" in settings.markdown_extensions

    # Check extension configs
    assert "codehilite" in settings.markdown_extension_configs
    assert "toc" in settings.markdown_extension_configs
    assert "pymdownx.superfences" in settings.markdown_extension_configs


def test_markdown_extension_configs():
    """Test specific markdown extension configurations"""
    from docs_server.config import Settings

    settings = Settings()

    # Check codehilite config
    assert settings.markdown_extension_configs["codehilite"]["css_class"] == "highlight"
    assert settings.markdown_extension_configs["codehilite"]["use_pygments"] is True

    # Check TOC config
    assert settings.markdown_extension_configs["toc"]["permalink"] is True
    assert settings.markdown_extension_configs["toc"]["toc_depth"] == 3

    # Check tasklist config
    assert settings.markdown_extension_configs["pymdownx.tasklist"]["custom_checkbox"] is True


def test_debug_string_parsing():
    """Test DEBUG environment variable string parsing"""
    from docs_server.config import Settings

    test_cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("", False),
        ("anything", False),
    ]

    for env_value, expected in test_cases:
        os.environ["DEBUG"] = env_value
        settings = Settings()
        assert settings.DEBUG == expected, f"Failed for DEBUG={env_value}"
