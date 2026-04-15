"""
Unit tests for config module.
Tests Settings initialization and environment variable handling.
"""

import os


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


def test_custom_css_default_and_env(monkeypatch):
    """Test CUSTOM_CSS default (custom.css) and env override with validation."""
    from docs_server.config import Settings

    monkeypatch.delenv("CUSTOM_CSS", raising=False)
    settings = Settings()
    assert settings.CUSTOM_CSS == "custom.css"

    monkeypatch.setenv("CUSTOM_CSS", "theme.css")
    settings = Settings()
    assert settings.CUSTOM_CSS == "theme.css"

    # Path traversal rejected - falls back to default
    monkeypatch.setenv("CUSTOM_CSS", "../etc/passwd")
    settings = Settings()
    assert settings.CUSTOM_CSS == "custom.css"

    # Missing .css extension - falls back to default
    monkeypatch.setenv("CUSTOM_CSS", "theme")
    settings = Settings()
    assert settings.CUSTOM_CSS == "custom.css"


def test_servemd_branding_enabled_default_and_env(monkeypatch):
    """Test SERVEMD_BRANDING_ENABLED default (true) and env override."""
    from docs_server.config import Settings

    monkeypatch.delenv("SERVEMD_BRANDING_ENABLED", raising=False)
    settings = Settings()
    assert settings.SERVEMD_BRANDING_ENABLED is True

    monkeypatch.setenv("SERVEMD_BRANDING_ENABLED", "false")
    settings = Settings()
    assert settings.SERVEMD_BRANDING_ENABLED is False

    monkeypatch.setenv("SERVEMD_BRANDING_ENABLED", "true")
    settings = Settings()
    assert settings.SERVEMD_BRANDING_ENABLED is True


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


def test_clear_cache_removes_contents(tmp_path, monkeypatch):
    """Test that clear_cache removes all cache contents and recreates the directory"""
    from docs_server.config import Settings

    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("CACHE_ROOT", str(tmp_path / "cache"))
    (tmp_path / "docs").mkdir()
    (tmp_path / "cache").mkdir()
    (tmp_path / "cache" / "index.html").write_text("cached")
    (tmp_path / "cache" / "subdir").mkdir()
    (tmp_path / "cache" / "subdir" / "file.txt").write_text("data")

    settings = Settings()
    settings.clear_cache()

    assert (tmp_path / "cache").exists()
    assert not (tmp_path / "cache" / "index.html").exists()
    assert not (tmp_path / "cache" / "subdir").exists()


def test_clear_cache_creates_directory_if_missing(tmp_path, monkeypatch):
    """Test that clear_cache creates the cache directory when it does not exist"""
    import shutil

    from docs_server.config import Settings

    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("CACHE_ROOT", str(tmp_path / "cache"))
    (tmp_path / "docs").mkdir()
    settings = Settings()
    shutil.rmtree(tmp_path / "cache")  # remove dir created by _init_directories

    settings.clear_cache()

    assert (tmp_path / "cache").exists()
    assert (tmp_path / "cache").is_dir()


def test_clear_cache_idempotent(tmp_path, monkeypatch):
    """Test that clear_cache can be called multiple times safely"""
    from docs_server.config import Settings

    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("CACHE_ROOT", str(tmp_path / "cache"))
    (tmp_path / "docs").mkdir()
    (tmp_path / "cache").mkdir()

    settings = Settings()
    settings.clear_cache()
    settings.clear_cache()

    assert (tmp_path / "cache").exists()


def test_forwarded_allow_ips_defaults_to_loopback(monkeypatch, tmp_path):
    monkeypatch.delenv("FORWARDED_ALLOW_IPS", raising=False)
    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("CACHE_ROOT", str(tmp_path / "cache"))
    (tmp_path / "docs").mkdir()
    from docs_server.config import Settings
    assert Settings().FORWARDED_ALLOW_IPS == "127.0.0.1"


def test_forwarded_allow_ips_reads_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "*")
    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("CACHE_ROOT", str(tmp_path / "cache"))
    (tmp_path / "docs").mkdir()
    from docs_server.config import Settings

    assert Settings().FORWARDED_ALLOW_IPS == "*"
