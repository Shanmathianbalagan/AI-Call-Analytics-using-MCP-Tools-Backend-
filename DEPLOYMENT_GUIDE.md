# Deployment Handover Guide

This guide prepares another team or server administrator to deploy the AI Call Analytics Chatbot on their own infrastructure.

Do not commit real secrets. Use `.env.example` as the template and create a private `.env` on the target server.

## Required Files

```text
ai_bot.py
api.py
ai_tool_router.py
hosted_mcp_server.py
mysql_mcp_server.py
requirements.txt
.env.example
README.md
DEPLOYMENT_GUIDE.md
```

If using Claude Desktop MCP integration, also include:

```text
claude_mcp/
```

## Environment Variables

Create `.env`:

```env
OPENAI_API_KEY=

MYSQL_HOST=
MYSQL_USER=
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

For multiple local frontend origins:

```env
FRONTEND_ORIGIN=http://localhost:5500,http://127.0.0.1:5500
```

For production:

```env
FRONTEND_ORIGIN=https://your-production-frontend-domain.example
```

## Database Export

On the source machine:

```powershell
mysqldump -u root -p call_analytics_db > call_analytics_db.sql
```

This creates a portable SQL dump of the `call_analytics_db` database.

## Database Import

On the target server:

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS call_analytics_db;"
mysql -u root -p call_analytics_db < call_analytics_db.sql
```

If the server uses a different database name, update `MYSQL_DATABASE` in `.env`.

For cloud MySQL, use the cloud provider's host, port, user, and password in `.env`.

## Dependency Installation

```powershell
cd C:\mcp-ai-tool-router
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
cd /path/to/mcp-ai-tool-router
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Backend Start Command

Windows fixed port:

```powershell
uvicorn ai_bot:app --host 0.0.0.0 --port 8001
```

Windows environment port:

```powershell
uvicorn ai_bot:app --host 0.0.0.0 --port $env:PORT
```

Linux/macOS environment port:

```bash
uvicorn ai_bot:app --host 0.0.0.0 --port "$PORT"
```

## Hosted MCP Server Start Command

Hosted MCP mode exposes the existing MySQL-backed MCP tools through authenticated HTTP endpoints.

Windows fixed port:

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

## Render Deployment Settings

Create a Render Web Service from the GitHub repository.

Use these settings:

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn hosted_mcp_server:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

Render provides the `$PORT` value at runtime. Do not hardcode `8000` for the Render start command.

The project includes:

```text
render.yaml
```

This can be used as a Render Blueprint-style deployment template. Secret values are not stored in the file and must be configured in Render.

Set these Render environment variables:

```text
MYSQL_HOST=<cloud/company MySQL host>
MYSQL_USER=<mysql user>
MYSQL_PASSWORD=<mysql password>
MYSQL_DATABASE=call_analytics_db
MYSQL_PORT=3306
MCP_AUTH_TOKEN=<strong private token>
ENVIRONMENT=production
```

Important:

```text
Render cannot connect to MySQL running only on your laptop.
The MySQL server must be reachable from Render.
Use cloud MySQL, a company-hosted database, or a network setup approved by the infrastructure team.
```

Hosted architecture:

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

Local Claude Desktop MCP mode remains unchanged:

```text
Claude Desktop
local mysql_mcp_server.py
MySQL
```

Hosted tool calls require:

```text
Authorization: Bearer <MCP_AUTH_TOKEN>
```

Missing or invalid tokens return:

```text
401 Unauthorized
```

## Frontend Start Command

Start the frontend using the hosting method selected by the deployment team.

For local static testing, a common option is:

```powershell
python -m http.server 5500
```

Run that command from the frontend folder, not necessarily from the backend folder.

Ensure the backend `.env` has:

```env
FRONTEND_ORIGIN=http://localhost:5500
```

## Health Check Testing

After starting the backend:

```powershell
curl http://localhost:8001/
```

Expected:

```json
{
  "status": "running",
  "message": "AI Call Analytics Chatbot Backend is running"
}
```

## Chat API Testing

```powershell
curl -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d "{\"message\":\"Show dataset summary\"}"
```

Expected:

```text
The response should include tool_decision, tool_result, and final_answer.
```

## Hosted MCP Health Check Testing

```powershell
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "running",
  "service": "Hosted MCP Server",
  "database": "connected"
}
```

## Hosted MCP Authenticated Tool Test

Windows:

```powershell
curl -X POST http://localhost:8000/tools/call ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"tool_name\":\"search_mysql_any_value_optimized\",\"arguments\":{\"search_value\":\"iPhone\",\"limit\":5}}"
```

Linux/macOS:

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

## Verification Checklist

```text
[ ] Required project files copied to server
[ ] .env created and secrets added
[ ] OPENAI_API_KEY configured
[ ] MySQL server reachable
[ ] call_analytics_db imported
[ ] calls table exists
[ ] Python virtual environment created
[ ] requirements.txt installed
[ ] Backend starts with uvicorn ai_bot:app
[ ] GET / health check works
[ ] POST /chat works
[ ] GPT tool routing works
[ ] MCP-style retrieval works
[ ] Frontend can call backend
[ ] CORS allows configured frontend origin
[ ] Sample queries return expected answers
[ ] Hosted MCP server starts
[ ] Hosted MCP /health returns running status
[ ] Hosted MCP /tools/call rejects missing token
[ ] Hosted MCP /tools/call rejects invalid token
[ ] Hosted MCP /tools/call works with valid token
```

## Sample Queries For Final Validation

```text
Show dataset summary
Show iPhone calls
Show full details for id 5
Show language distribution
Top products discussed
Show improvement areas
Show issue patterns
Show repeated customer frustrations
```

## Troubleshooting

If `OPENAI_API_KEY` is missing or invalid, GPT routing or response formatting will fail.

If MySQL connection fails, check `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, and `MYSQL_PORT`.

If the frontend cannot call the backend, check that `FRONTEND_ORIGIN` exactly matches the browser origin.

If port `8001` is unavailable, set another `PORT` value and start uvicorn with that port.

If database import fails, confirm MySQL client tools are installed and the target user has permission to create/import databases.

If hosted MCP authentication fails, confirm `MCP_AUTH_TOKEN` is configured and the request header exactly matches `Authorization: Bearer <token>`.
