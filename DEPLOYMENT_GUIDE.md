# Deployment Handover Guide

This guide prepares another team or server administrator to deploy the AI Call Analytics Chatbot on their own infrastructure.

Do not commit real secrets. Use `.env.example` as the template and create a private `.env` on the target server.

## Required Files

```text
ai_bot.py
api.py
ai_tool_router.py
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
