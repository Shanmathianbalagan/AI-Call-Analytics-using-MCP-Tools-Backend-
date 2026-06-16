# Claude Desktop MCP Setup

This guide connects Claude Desktop to the existing MySQL MCP server.

## Existing MCP Server

The existing MCP server is:

```text
C:\mcp-ai-tool-router\mysql_mcp_server.py
```

Do not modify this server for Claude integration.

## Architecture

```text
User
Claude Desktop
MCP Tool Selection
mysql_mcp_server.py
MySQL call_analytics_db.calls
MCP Result
Claude Response
```

## Claude Desktop Config Location

On Windows, Claude Desktop config is usually located at:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Full path example:

```text
C:\Users\<your-username>\AppData\Roaming\Claude\claude_desktop_config.json
```

## MCP Server Registration

Add this config to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mysql-call-analytics": {
      "command": "C:\\mcp-ai-tool-router\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\mcp-ai-tool-router\\mysql_mcp_server.py"
      ]
    }
  }
}
```

## Setup Steps

1. Close Claude Desktop completely.
2. Open or create `%APPDATA%\Claude\claude_desktop_config.json`.
3. Paste the MCP server config.
4. Save the file.
5. Restart Claude Desktop.
6. Open a new Claude chat.
7. Ask: `Show dataset summary`

## Expected Behavior

Claude should discover the MCP tools exposed by `mysql_mcp_server.py`.

Claude should call tools such as:

```text
get_mysql_dataset_summary
search_mysql_any_value_optimized
get_mysql_full_call_by_id
get_mysql_full_call_by_recording_id
```

Claude should not directly query MySQL.

MySQL access must happen only through the MCP tools.

## Notes

The MCP server communicates through stdio.

When started manually, it may appear silent because it is waiting for an MCP client such as Claude Desktop.
