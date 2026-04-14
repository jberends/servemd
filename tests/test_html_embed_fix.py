"""Tests for raw HTML file serving in iframe embeds."""

from fastapi.testclient import TestClient


def test_raw_html_served_with_correct_content_type(tmp_path, monkeypatch):
    """Raw HTML files are served with text/html; charset=utf-8."""
    import docs_server.config as cfg

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    monkeypatch.setattr(cfg.settings, "DOCS_ROOT", docs_root)

    html_content = "<!DOCTYPE html><html><head><title>T</title></head><body><h1>Test</h1></body></html>"
    (docs_root / "test_page.html").write_text(html_content, encoding="utf-8")

    # Import app AFTER monkeypatching
    from docs_server.main import app

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/raw/test_page.html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Test" in response.text


def test_raw_html_iframe_accessible(tmp_path, monkeypatch):
    """An HTML file in DOCS_ROOT renders as a page with an iframe pointing to /raw/."""
    import docs_server.config as cfg

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "sidebar.md").write_text("# Nav\n", encoding="utf-8")
    (docs_root / "topbar.md").write_text("# Top\n", encoding="utf-8")
    monkeypatch.setattr(cfg.settings, "DOCS_ROOT", docs_root)

    html_content = "<!DOCTYPE html><html><body><h1>Embedded</h1></body></html>"
    (docs_root / "embed_test.html").write_text(html_content, encoding="utf-8")

    from docs_server.main import app

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/embed_test.html")

    assert response.status_code == 200
    assert 'src="/raw/embed_test.html"' in response.text
    assert 'class="html-embed-frame"' in response.text


def test_raw_html_nested_directory(tmp_path, monkeypatch):
    """HTML files in subdirectories are served correctly from /raw/."""
    import docs_server.config as cfg

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    subdir = docs_root / "specs"
    subdir.mkdir()
    monkeypatch.setattr(cfg.settings, "DOCS_ROOT", docs_root)

    html_content = "<!DOCTYPE html><html><body><h1>Nested</h1></body></html>"
    (subdir / "nested.html").write_text(html_content, encoding="utf-8")

    from docs_server.main import app

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/raw/specs/nested.html")

    assert response.status_code == 200
    assert "Nested" in response.text
