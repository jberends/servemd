#!/usr/bin/env python3
"""
Simple test script to verify llms.txt implementation.
This doesn't require the full server to be running.
"""

import re


def transform_relative_to_absolute(markdown_content: str, base_url: str) -> str:
    """
    Transform relative .md links to absolute URLs.

    Examples:
        [Title](file.md) -> [Title](https://docs.example.com/file.md)
        [Title](file.md#section) -> [Title](https://docs.example.com/file.md#section)
    """
    # Pattern matches: [text](path.md) or [text](path.md#anchor)
    pattern = r"\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)"

    def replace_link(match):
        title = match.group(1)
        rel_path = match.group(2)

        # Skip if already absolute URL
        if rel_path.startswith("http://") or rel_path.startswith("https://"):
            return match.group(0)

        # Create absolute URL
        abs_url = f"{base_url.rstrip('/')}/{rel_path.lstrip('/')}"
        return f"[{title}]({abs_url})"

    return re.sub(pattern, replace_link, markdown_content)


def test_simple_relative_link():
    """Test transformation of simple relative link"""
    base_url = "https://docs.example.com"
    content = "[Snelle Uitleg](01_snelle_uitleg.md)"
    result = transform_relative_to_absolute(content, base_url)
    expected = "[Snelle Uitleg](https://docs.example.com/01_snelle_uitleg.md)"
    assert result == expected


def test_link_with_anchor():
    """Test transformation of link with anchor"""
    base_url = "https://docs.example.com"
    content = "[Section](file.md#section)"
    result = transform_relative_to_absolute(content, base_url)
    expected = "[Section](https://docs.example.com/file.md#section)"
    assert result == expected


def test_already_absolute_url():
    """Test that already absolute URLs remain unchanged"""
    base_url = "https://docs.example.com"
    content = "[External](https://example.com/file.md)"
    result = transform_relative_to_absolute(content, base_url)
    expected = "[External](https://example.com/file.md)"
    assert result == expected


def test_multiple_links():
    """Test transformation of multiple links in content"""
    base_url = "https://docs.example.com"
    content = """
[Login](02_login.md)
[Dashboard](04_01_dashboard.md)
[Risks](04_07_risicos.md#overview)
"""
    result = transform_relative_to_absolute(content, base_url)
    assert "https://docs.example.com/02_login.md" in result
    assert "https://docs.example.com/04_01_dashboard.md" in result
    assert "https://docs.example.com/04_07_risicos.md#overview" in result


def test_base_url_with_trailing_slash():
    """Test that trailing slash in base URL is handled correctly"""
    base_url = "https://docs.example.com/"
    content = "[Test](test.md)"
    result = transform_relative_to_absolute(content, base_url)
    expected = "[Test](https://docs.example.com/test.md)"
    assert result == expected


def test_path_with_leading_slash():
    """Test that leading slash in path is handled correctly"""
    base_url = "https://docs.example.com"
    content = "[Test](/test.md)"
    result = transform_relative_to_absolute(content, base_url)
    expected = "[Test](https://docs.example.com/test.md)"
    assert result == expected


if __name__ == "__main__":
    # For standalone execution
    print("Running tests...")
    test_simple_relative_link()
    print("✅ Test 1 passed: Simple relative link")
    test_link_with_anchor()
    print("✅ Test 2 passed: Link with anchor")
    test_already_absolute_url()
    print("✅ Test 3 passed: Already absolute URL")
    test_multiple_links()
    print("✅ Test 4 passed: Multiple links")
    test_base_url_with_trailing_slash()
    print("✅ Test 5 passed: Base URL with trailing slash")
    test_path_with_leading_slash()
    print("✅ Test 6 passed: Path with leading slash")
    print("\n✅ All tests passed! Link transformation works correctly.")
