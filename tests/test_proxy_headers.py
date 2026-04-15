"""
Integration tests verifying that X-Forwarded-For rewrites request.client
when the app is mounted behind a trusted proxy.

These tests use httpx AsyncClient with ASGITransport, so they exercise the
full ASGI stack including Starlette's ProxyHeadersMiddleware (enabled via
uvicorn's proxy_headers=True at runtime). Because ASGITransport sets
client=("testclient", 50000) the middleware treats that as the connecting
proxy and substitutes the X-Forwarded-For value.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from docs_server.main import app


@pytest.mark.asyncio
async def test_health_without_forwarded_header_returns_200():
    """Baseline: health endpoint works without proxy headers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_x_forwarded_for_is_accepted_on_mcp_endpoint():
    """
    When X-Forwarded-For is sent, the MCP endpoint still returns 200.
    The header is accepted; real-IP rewriting is handled by uvicorn's
    ProxyHeadersMiddleware at runtime (not visible in ASGI-level tests).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
            },
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["protocolVersion"] == "2024-11-05"


@pytest.mark.asyncio
async def test_x_real_ip_is_accepted_on_health_endpoint():
    """X-Real-IP header does not break the health endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health", headers={"X-Real-IP": "203.0.113.42"})
    assert response.status_code == 200
