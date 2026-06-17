# AI Call Analytics Chatbot

FastAPI backend for an AI-powered call analytics chatbot. The backend uses GPT-4o-mini for intent routing and final answer formatting, and uses MCP-style retrieval tools to fetch call analytics data from MySQL.

The project also supports hosted authenticated HTTP access to the existing MCP tools through `hosted_mcp_server.py`.

## Architecture

```text
Frontend Chatbot
FastAPI Backend
GPT-4o-mini Tool Router
MCP-style Retrieval Functions
MySQL call_analytics_db.calls
GPT-4o-mini Final Response
Frontend Chatbot
```

Claude Desktop MCP setup files are kept separately in `claude_mcp/` and do not change the FastAPI chatbot flow.

## Folder Structure

```text
C:\mcp-ai-tool-router
|-- ai_bot.py
|-- api.py
|-- ai_tool_router.py
|-- hosted_mcp_server.py
|-- mysql_mcp_server.py
|-- requirements.txt
|-- .env.example
|-- DEPLOYMENT_GUIDE.md
`-- claude_mcp/
```

## Environment Variables

Create a local `.env` file from `.env.example`.

```env
OPENAI_API_KEY=

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=call_analytics_db
MYSQL_PORT=3306

PORT=8001

FRONTEND_ORIGIN=http://localhost:5500

MCP_AUTH_TOKEN=change_this_secret_token
MCP_HOST=0.0.0.0
MCP_PORT=8000
ENVIRONMENT=local
```

`FRONTEND_ORIGIN` supports comma-separated values, for example:

```env
FRONTEND_ORIGIN=http://localhost:5500,http://127.0.0.1:5500
```

## Installation

```powershell
cd C:\mcp-ai-tool-router
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Database Setup

The backend expects:

```text
Database: call_analytics_db
Table: calls
```

Export the database from the source machine:

```powershell
mysqldump -u root -p call_analytics_db > call_analytics_db.sql
```

Restore on a target server:

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS call_analytics_db;"
mysql -u root -p call_analytics_db < call_analytics_db.sql
```

Update `.env` with the target server's MySQL host, user, password, database, and port.

## Backend Startup

Local fixed-port startup:

```powershell
uvicorn ai_bot:app --host 0.0.0.0 --port 8001
```

Server-provided port example:

```powershell
uvicorn ai_bot:app --host 0.0.0.0 --port $env:PORT
```

Linux/macOS shell equivalent:

```bash
uvicorn ai_bot:app --host 0.0.0.0 --port "$PORT"
```

## Hosted MCP HTTP Server

Hosted mode exposes the existing MySQL-backed MCP tools through authenticated HTTP endpoints. It does not replace local Claude Desktop MCP mode.

Architecture:

```text
AI Client / Claude / Chatbot
Authenticated HTTP Request
hosted_mcp_server.py
Whitelisted Tool Router
Existing MCP Tool Function
MySQL call_analytics_db.calls
JSON Tool Result
AI Response
```

Start hosted MCP server:

```powershell
uvicorn hosted_mcp_server:app --host 0.0.0.0 --port 8000
```

Windows environment port:

```powershell
uvicorn hosted_mcp_server:app --host 0.0.0.0 --port $env:MCP_PORT
```

Linux/macOS environment port:

```bash
uvicorn hosted_mcp_server:app --host 0.0.0.0 --port "$MCP_PORT"
```

### Render Startup

For Render Web Service deployment, use Render's provided `$PORT`:

```text
Build Command:
pip install -r requirements.txt

Start Command:
uvicorn hosted_mcp_server:app --host 0.0.0.0 --port $PORT

Health Check Path:
/health
```

The repository also includes `render.yaml` for Render Blueprint-style setup. Secrets still need to be configured in the Render dashboard.

Required Render environment variables:

```text
MYSQL_HOST
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE=call_analytics_db
MYSQL_PORT=3306
MCP_AUTH_TOKEN
ENVIRONMENT=production
```

Do not set real secrets in `render.yaml`.

Health check:

```http
GET /health
```

Expected response:

```json
{
  "status": "running",
  "service": "Hosted MCP Server",
  "database": "connected"
}
```

Authenticated tool endpoint:

```http
POST /tools/call
Authorization: Bearer <MCP_AUTH_TOKEN>
```

Request:

```json
{
  "tool_name": "search_mysql_any_value_optimized",
  "arguments": {
    "search_value": "iPhone",
    "limit": 5
  }
}
```

Windows curl:

```powershell
curl -X POST http://localhost:8000/tools/call ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"tool_name\":\"search_mysql_any_value_optimized\",\"arguments\":{\"search_value\":\"iPhone\",\"limit\":5}}"
```

Linux/macOS curl:

```bash
curl -X POST http://localhost:8000/tools/call \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"search_mysql_any_value_optimized","arguments":{"search_value":"iPhone","limit":5}}'
```

Supported hosted tools:

```text
get_mysql_dataset_summary
search_mysql_any_value_optimized
get_mysql_full_call_by_id
get_mysql_full_call_by_recording_id
get_all_issue_patterns
get_improvement_areas
get_language_distribution
get_top_products_discussed
get_repeated_issue_patterns
```

Security:

```text
Bearer token is required for /tools/call.
Only whitelisted tools can run.
Unknown tools return 400 Bad Request.
Missing or invalid token returns 401 Unauthorized.
Secrets are loaded from environment variables.
```

## Health Check

```http
GET /
```

Expected response:

```json
{
  "status": "running",
  "message": "AI Call Analytics Chatbot Backend is running"
}
```

## Chat Endpoint

```http
POST /chat
```

Request:

```json
{
  "message": "Show iPhone calls"
}
```

Response includes:

```text
tool_decision
tool_result
final_answer
```

## Sample Queries

```text
Show dataset summary
Show iPhone calls
Show Tamil calls
Show full details for id 5
Show full details for recording id rec-example
Show language distribution
Top products discussed
Show improvement areas
Show issue patterns
Show repeated customer frustrations
```

## Frontend Startup

Serve the frontend from its project folder using the team's preferred static server. For local development, the backend CORS default supports:

```text
http://localhost:5500
http://127.0.0.1:5500
```

If the frontend is hosted elsewhere, update:

```env
FRONTEND_ORIGIN=https://your-frontend-domain.example
```

## Troubleshooting

If the backend does not start, verify dependencies:

```powershell
pip install -r requirements.txt
```

If OpenAI calls fail, verify:

```text
OPENAI_API_KEY
```

If MySQL queries fail, verify:

```text
MYSQL_HOST
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
MYSQL_PORT
```

If frontend requests are blocked, verify `FRONTEND_ORIGIN` matches the exact frontend URL.

If hosted MCP tool calls return 401, verify `MCP_AUTH_TOKEN` and the `Authorization: Bearer <token>` header.

## Deployment Checklist

```text
[ ] .env created from .env.example
[ ] OPENAI_API_KEY configured
[ ] MySQL database imported
[ ] MySQL env vars configured
[ ] Dependencies installed
[ ] Backend starts with uvicorn ai_bot:app
[ ] GET / returns running status
[ ] POST /chat returns chatbot response
[ ] Frontend origin configured in CORS
[ ] Sample queries return expected results
[ ] Hosted MCP /health works
[ ] Hosted MCP /tools/call rejects missing token
[ ] Hosted MCP /tools/call works with valid token
```
