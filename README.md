# AI Call Analytics Chatbot

FastAPI backend for an AI-powered call analytics chatbot. The backend uses GPT-4o-mini for intent routing and final answer formatting, and uses MCP-style retrieval tools to fetch call analytics data from MySQL.

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
```
