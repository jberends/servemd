"""
Pydantic models for MCP JSON-RPC requests and responses.
Implements JSON-RPC 2.0 specification with MCP protocol support.
"""

from typing import Any

from pydantic import BaseModel, Field

# JSON-RPC 2.0 Models


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request model."""

    jsonrpc: str = Field(default="2.0", pattern=r"^2\.0$")
    id: str | int | None = None
    method: str
    params: dict[str, Any] | None = None


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error object."""

    code: int
    message: str
    data: dict[str, Any] | None = None


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response model."""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    result: dict[str, Any] | None = None
    error: JsonRpcError | None = None


# MCP Protocol Models


class ClientInfo(BaseModel):
    """Information about the MCP client."""

    name: str
    version: str


class InitializeParams(BaseModel):
    """Parameters for the initialize request."""

    protocolVersion: str
    capabilities: dict[str, Any] = Field(default_factory=dict)
    clientInfo: ClientInfo | None = None


class ServerInfo(BaseModel):
    """Information about the MCP server."""

    name: str = "servemd-mcp"
    version: str = "1.0.0"


class ServerCapabilities(BaseModel):
    """Server capabilities advertised during initialization."""

    tools: dict[str, Any] = Field(default_factory=dict)


class InitializeResult(BaseModel):
    """Result of the initialize request."""

    protocolVersion: str = "2024-11-05"
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)
    serverInfo: ServerInfo = Field(default_factory=ServerInfo)


# MCP Tool Input Models (for future phases)


class SearchDocsInput(BaseModel):
    """Input model for search_docs tool."""

    query: str = Field(min_length=1, max_length=500, description="Search query to find relevant documentation")
    limit: int = Field(ge=1, le=50, default=10, description="Maximum number of results to return")


class GetDocPageInput(BaseModel):
    """Input model for get_doc_page tool."""

    path: str = Field(min_length=1, description="Relative path to documentation file (e.g., 'api/endpoints.md')")
    sections: list[str] | None = Field(default=None, description="Optional list of h2 section titles to filter")


class ListDocPagesInput(BaseModel):
    """Input model for list_doc_pages tool."""

    category: str | None = Field(default=None, description="Optional category filter from sidebar structure")
