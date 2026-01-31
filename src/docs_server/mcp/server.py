"""
JSON-RPC 2.0 handler for MCP protocol.
Handles incoming MCP requests and routes to appropriate method handlers.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any

from pydantic import ValidationError

from ..config import settings
from .models import InitializeParams, InitializeResult, JsonRpcError, JsonRpcRequest, JsonRpcResponse

logger = logging.getLogger(__name__)

# JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def parse_request(body: dict[str, Any]) -> tuple[JsonRpcRequest | None, JsonRpcError | None]:
    """
    Parse and validate a JSON-RPC 2.0 request.

    Args:
        body: Raw request body dictionary

    Returns:
        Tuple of (parsed_request, error). If error is not None, parsing failed.
    """
    try:
        request = JsonRpcRequest.model_validate(body)
        return request, None
    except ValidationError as e:
        logger.warning(f"Invalid JSON-RPC request: {e}")
        return None, JsonRpcError(
            code=INVALID_REQUEST,
            message="Invalid JSON-RPC request",
            data={"errors": e.errors()},
        )


def format_response(request_id: str | int | None, result: dict[str, Any]) -> dict[str, Any]:
    """
    Format a successful JSON-RPC 2.0 response.

    Args:
        request_id: The request ID to echo back
        result: The result payload

    Returns:
        Formatted JSON-RPC response dictionary
    """
    response = JsonRpcResponse(id=request_id, result=result)
    # Exclude None from nested objects but keep id (required by JSON-RPC spec)
    data = response.model_dump()
    # Remove None error (we have a result, not an error)
    if data.get("error") is None:
        del data["error"]
    return data


def format_error(
    request_id: str | int | None,
    code: int,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Format a JSON-RPC 2.0 error response.

    Args:
        request_id: The request ID to echo back (can be None for parse errors)
        code: JSON-RPC error code
        message: Human-readable error message
        data: Optional additional error data

    Returns:
        Formatted JSON-RPC error response dictionary
    """
    error = JsonRpcError(code=code, message=message, data=data)
    response = JsonRpcResponse(id=request_id, error=error)
    # Keep id (required by JSON-RPC spec), remove result (we have an error)
    data_dict = response.model_dump()
    if data_dict.get("result") is None:
        del data_dict["result"]
    # Remove None data from error object
    if data_dict["error"].get("data") is None:
        del data_dict["error"]["data"]
    return data_dict


async def handle_initialize(params: dict[str, Any] | None) -> dict[str, Any]:
    """
    Handle the MCP initialize method.

    Args:
        params: Initialize parameters from client

    Returns:
        Initialize result with server info and capabilities
    """
    # Parse and validate parameters if provided
    if params:
        try:
            init_params = InitializeParams.model_validate(params)
            logger.info(f"MCP client initialized: {init_params.clientInfo}")
        except ValidationError as e:
            logger.warning(f"Invalid initialize params: {e}")
            # Continue anyway - params are optional per spec

    # Return server capabilities
    result = InitializeResult()
    return result.model_dump()


async def handle_tools_list() -> dict[str, Any]:
    """
    Handle the tools/list method.
    Returns the list of available MCP tools with their schemas.

    Returns:
        Dictionary with tools list containing:
        - search_docs: Full-text search across documentation
        - get_doc_page: Retrieve a specific documentation page
        - list_doc_pages: List all available documentation pages
    """
    from .tools import get_tool_definitions

    return {"tools": get_tool_definitions()}


async def handle_tools_call(params: dict[str, Any] | None) -> dict[str, Any]:
    """
    Handle the tools/call method.
    Dispatches to the appropriate tool handler based on the tool name.

    Args:
        params: Tool call parameters containing 'name' and 'arguments'

    Returns:
        Tool result content

    Raises:
        ValueError: If tool name is missing or unknown
        ValidationError: If arguments are invalid
    """
    from .tools import call_tool

    if not params:
        raise ValueError("Missing tool call parameters")

    tool_name = params.get("name")
    if not tool_name:
        raise ValueError("Missing tool name in params")

    arguments = params.get("arguments", {})

    # Structured logging for tool calls
    logger.info(f"[MCP] method=tools/call tool={tool_name}")

    # Call the tool
    result = call_tool(tool_name, arguments)

    # Log result metadata
    if tool_name == "search_docs" and isinstance(result, dict):
        content = result.get("content", [])
        if content and isinstance(content[0], dict):
            text = content[0].get("text", "")
            # Extract result count from text (e.g., "Found 3 result(s):")
            import re
            match = re.search(r"Found (\d+) result\(s\)", text)
            if match:
                count = match.group(1)
                query = arguments.get("query", "")
                logger.info(f"[MCP] search query=\"{query}\" results={count}")

    return result


async def handle_request(body: dict[str, Any]) -> dict[str, Any]:
    """
    Main entry point for handling MCP JSON-RPC requests.

    Implements comprehensive error handling with contextual messages:
    - -32700: Parse error (invalid JSON)
    - -32600: Invalid request (missing required fields)
    - -32601: Method not found (unknown MCP method)
    - -32602: Invalid params (validation failures, file not found)
    - -32603: Internal error (server errors, runtime failures)

    Args:
        body: Raw JSON request body

    Returns:
        JSON-RPC response dictionary
    """
    # Parse the request
    request, error = parse_request(body)

    if error:
        return format_error(body.get("id"), error.code, error.message, error.data)

    assert request is not None  # Type narrowing

    logger.debug(f"MCP request: method={request.method}")

    # Route to appropriate handler based on method
    try:
        if request.method == "initialize":
            result = await handle_initialize(request.params)
            return format_response(request.id, result)

        elif request.method == "notifications/initialized":
            # Client notification that initialization is complete
            # Per MCP spec, this is a notification (no response expected)
            # But we return success for consistency
            return format_response(request.id, {})

        elif request.method == "tools/list":
            result = await handle_tools_list()
            return format_response(request.id, result)

        elif request.method == "tools/call":
            result = await handle_tools_call(request.params)
            return format_response(request.id, result)

        else:
            logger.warning(f"Unknown MCP method: {request.method}")
            return format_error(
                request.id,
                METHOD_NOT_FOUND,
                f"Method not found: {request.method}",
                {"available_methods": ["initialize", "tools/list", "tools/call"]},
            )

    except ValueError as e:
        # Invalid params - missing or invalid tool name
        logger.warning(f"Invalid params for MCP request: {e}")
        error_data: dict[str, Any] = {"error": str(e)}
        if request.params:
            error_data["params"] = request.params
        return format_error(
            request.id,
            INVALID_PARAMS,
            str(e),
            error_data,
        )

    except ValidationError as e:
        # Pydantic validation error
        logger.warning(f"Validation error for MCP request: {e}")
        return format_error(
            request.id,
            INVALID_PARAMS,
            "Invalid parameters",
            {"errors": e.errors()},
        )

    except FileNotFoundError as e:
        # File not found error from get_doc_page
        logger.warning(f"File not found: {e}")
        error_data = {"error": str(e)}
        if request.params and "path" in (request.params.get("arguments") or {}):
            error_data["path"] = request.params["arguments"]["path"]
        return format_error(
            request.id,
            INVALID_PARAMS,
            str(e),
            error_data,
        )

    except RuntimeError as e:
        # Runtime errors (index not ready, search failures)
        logger.error(f"Runtime error handling MCP request: {e}")
        error_data = {"error": str(e)}
        if request.params:
            # Include query in error data for search errors
            if "arguments" in request.params and "query" in request.params["arguments"]:
                error_data["query"] = request.params["arguments"]["query"]
        return format_error(
            request.id,
            INTERNAL_ERROR,
            str(e),
            error_data,
        )

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Error handling MCP request: {e}", exc_info=True)
        error_data = {"error": str(e)}

        # Include traceback in DEBUG mode
        if settings.DEBUG:
            error_data["traceback"] = traceback.format_exc()

        return format_error(
            request.id,
            INTERNAL_ERROR,
            "Internal server error",
            error_data,
        )
