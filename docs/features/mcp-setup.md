# Connecting Your AI Client to MCP

This guide walks through connecting Claude Desktop, Cursor, and VS Code to the MCP endpoint of a ServeMD-powered documentation site.

> **Quick install:** Visit [/servemd](/servemd) on this site for one-click install buttons for Cursor and VS Code, plus a ready-to-copy config snippet for Claude Desktop — all pre-filled with the correct URL for this deployment.

## Claude Desktop

Claude Desktop supports remote HTTP MCP servers via manual configuration. There is no one-click URL scheme for remote servers.

### Steps

1. Open Claude Desktop.
2. Go to **Settings → Developer → Edit Config** to open `claude_desktop_config.json`.
3. Add your server under `mcpServers`:

```json
{
  "mcpServers": {
    "my-docs": {
      "type": "http",
      "url": "https://your-docs-site.com/mcp"
    }
  }
}
```

4. Save the file and **restart Claude Desktop**.
5. Verify the connection: click the **+** button in the chat input and select **Connectors**.

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## Cursor

Cursor v3.0.9+ has a known regression where native HTTP/SSE MCP transport is broken (affects Figma, Vercel, and all remote HTTP MCPs). The workaround is [`mcp-remote`](https://github.com/geelen/mcp-remote), which bridges the remote endpoint via stdio.

### Steps

1. Add the following to your Cursor MCP config:
   - **Global** (all projects): `~/.cursor/mcp.json`
   - **Project-level**: `.cursor/mcp.json` in your repo root

```json
{
  "mcpServers": {
    "my-docs": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://your-docs-site.com/mcp"]
    }
  }
}
```

2. Restart Cursor (or reload the MCP config from **Settings → Tools & MCP**).

Or use the **Add to Cursor** button on [/servemd](/servemd) which generates the correct deep link automatically.

## VS Code

VS Code supports MCP natively via its built-in HTTP transport.

### Steps

1. Open VS Code settings (`Cmd/Ctrl + ,`) and navigate to **MCP Servers**, or add to `.vscode/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "my-docs": {
        "type": "http",
        "url": "https://your-docs-site.com/mcp"
      }
    }
  }
}
```

Or use the **Add to VS Code** button on [/servemd](/servemd) which opens a pre-filled confirmation dialog.

## Manual JSON-RPC (fallback)

All MCP clients that support JSON-RPC 2.0 over HTTP can connect directly. See the [MCP Integration](mcp.html) page for the full protocol reference and example requests.
