"""
Tests for MCP JSON-RPC server functionality.
Tests JSON-RPC 2.0 parsing, initialize method, and error handling.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from docs_server.main import app
from docs_server.mcp.server import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    format_error,
    format_response,
    handle_request,
    parse_request,
)

# Test JSON-RPC request parsing


class TestParseRequest:
    """Tests for parse_request function."""

    def test_parse_valid_request(self):
        """Valid JSON-RPC request should parse successfully."""
        body = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
        request, error = parse_request(body)

        assert error is None
        assert request is not None
        assert request.method == "initialize"
        assert request.id == "1"
        assert request.params == {"protocolVersion": "2024-11-05"}

    def test_parse_request_without_params(self):
        """Request without params should be valid."""
        body = {
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/list",
        }
        request, error = parse_request(body)

        assert error is None
        assert request is not None
        assert request.method == "tools/list"
        assert request.params is None

    def test_parse_request_with_integer_id(self):
        """Request with integer ID should be valid."""
        body = {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "initialize",
        }
        request, error = parse_request(body)

        assert error is None
        assert request is not None
        assert request.id == 42

    def test_parse_request_missing_method(self):
        """Request without method should fail."""
        body = {
            "jsonrpc": "2.0",
            "id": "1",
        }
        request, error = parse_request(body)

        assert request is None
        assert error is not None
        assert error.code == INVALID_REQUEST

    def test_parse_request_invalid_jsonrpc_version(self):
        """Request with wrong jsonrpc version should fail."""
        body = {
            "jsonrpc": "1.0",
            "id": "1",
            "method": "initialize",
        }
        request, error = parse_request(body)

        assert request is None
        assert error is not None
        assert error.code == INVALID_REQUEST


# Test response formatting


class TestFormatResponse:
    """Tests for format_response function."""

    def test_format_success_response(self):
        """Success response should have correct structure."""
        result = {"capabilities": {"tools": {}}}
        response = format_response("1", result)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "1"
        assert response["result"] == result
        assert "error" not in response

    def test_format_response_with_integer_id(self):
        """Response should preserve integer ID."""
        response = format_response(42, {"data": "test"})

        assert response["id"] == 42


class TestFormatError:
    """Tests for format_error function."""

    def test_format_error_response(self):
        """Error response should have correct structure."""
        response = format_error("1", METHOD_NOT_FOUND, "Method not found")

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "1"
        assert response["error"]["code"] == METHOD_NOT_FOUND
        assert response["error"]["message"] == "Method not found"
        assert "result" not in response

    def test_format_error_with_data(self):
        """Error response should include data when provided."""
        response = format_error("1", INVALID_PARAMS, "Invalid params", {"field": "query"})

        assert response["error"]["data"] == {"field": "query"}

    def test_format_error_with_none_id(self):
        """Error response should handle None ID (for parse errors)."""
        response = format_error(None, PARSE_ERROR, "Parse error")

        assert response["id"] is None


# Test MCP method handling


class TestHandleRequest:
    """Tests for handle_request function."""

    @pytest.mark.asyncio
    async def test_initialize_method(self):
        """Initialize method should return server info and capabilities."""
        body = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }
        response = await handle_request(body)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "1"
        assert "result" in response
        assert response["result"]["serverInfo"]["name"] == "servemd-mcp"
        assert response["result"]["serverInfo"]["version"] == "1.0.0"
        assert "capabilities" in response["result"]
        assert "tools" in response["result"]["capabilities"]

    @pytest.mark.asyncio
    async def test_initialize_without_params(self):
        """Initialize should work without params."""
        body = {
            "jsonrpc": "2.0",
            "id": "2",
            "method": "initialize",
        }
        response = await handle_request(body)

        assert "result" in response
        assert response["result"]["serverInfo"]["name"] == "servemd-mcp"

    @pytest.mark.asyncio
    async def test_tools_list_method(self):
        """tools/list should return empty tools list in Phase 1."""
        body = {
            "jsonrpc": "2.0",
            "id": "3",
            "method": "tools/list",
        }
        response = await handle_request(body)

        assert "result" in response
        assert "tools" in response["result"]
        assert isinstance(response["result"]["tools"], list)

    @pytest.mark.asyncio
    async def test_notifications_initialized(self):
        """notifications/initialized should return success."""
        body = {
            "jsonrpc": "2.0",
            "id": "4",
            "method": "notifications/initialized",
        }
        response = await handle_request(body)

        assert "result" in response
        assert response["result"] == {}

    @pytest.mark.asyncio
    async def test_unknown_method(self):
        """Unknown method should return METHOD_NOT_FOUND error."""
        body = {
            "jsonrpc": "2.0",
            "id": "5",
            "method": "unknown/method",
        }
        response = await handle_request(body)

        assert "error" in response
        assert response["error"]["code"] == METHOD_NOT_FOUND
        assert "unknown/method" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_invalid_request(self):
        """Invalid request should return INVALID_REQUEST error."""
        body = {
            "jsonrpc": "2.0",
            "id": "6",
            # Missing method
        }
        response = await handle_request(body)

        assert "error" in response
        assert response["error"]["code"] == INVALID_REQUEST


# Test HTTP endpoint integration


class TestMCPEndpoint:
    """Integration tests for /mcp HTTP endpoint."""

    @pytest.mark.asyncio
    async def test_mcp_endpoint_initialize(self):
        """POST /mcp should handle initialize request."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                    },
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "1"
        assert "result" in data
        assert data["result"]["serverInfo"]["name"] == "servemd-mcp"

    @pytest.mark.asyncio
    async def test_mcp_endpoint_invalid_json(self):
        """POST /mcp with invalid JSON should return parse error."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp",
                content="not json",
                headers={"Content-Type": "application/json"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["error"]["code"] == PARSE_ERROR

    @pytest.mark.asyncio
    async def test_mcp_endpoint_tools_list(self):
        """POST /mcp should handle tools/list request."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": "2",
                    "method": "tools/list",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]


# Test error codes


class TestErrorCodes:
    """Tests for JSON-RPC error code constants."""

    def test_parse_error_code(self):
        """Parse error should be -32700."""
        assert PARSE_ERROR == -32700

    def test_invalid_request_code(self):
        """Invalid request error should be -32600."""
        assert INVALID_REQUEST == -32600

    def test_method_not_found_code(self):
        """Method not found error should be -32601."""
        assert METHOD_NOT_FOUND == -32601

    def test_invalid_params_code(self):
        """Invalid params error should be -32602."""
        assert INVALID_PARAMS == -32602

    def test_internal_error_code(self):
        """Internal error should be -32603."""
        assert INTERNAL_ERROR == -32603
