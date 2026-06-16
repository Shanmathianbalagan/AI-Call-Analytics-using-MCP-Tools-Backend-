# AI Call Analytics Chatbot - Full Project Documentation

## 1. Project Purpose

This project is an AI-powered call analytics chatbot.

It allows a user to ask natural-language questions about a MySQL call analytics dataset. The system decides which retrieval tool is needed, fetches data from MySQL, and returns a human-readable answer.

The project has two working usage modes:

```text
1. FastAPI chatbot flow
2. Claude Desktop MCP flow
```

The FastAPI flow uses GPT-4o-mini for routing and answer formatting.

The Claude Desktop flow uses Claude as the AI interface and uses the existing MCP tools as the retrieval layer.

## 2. Current Project Location

```text
C:\mcp-ai-tool-router
```

## 3. Database Details

The project uses MySQL.

```text
Database: call_analytics_db
Table: calls
Total records verified: 4,792
Total columns verified: 25
```

The dataset contains call metadata, sentiment scores, product discussion details, focus areas, strengths, areas of improvement, and skill-level scoring fields.

Examples of columns:

```text
id
recording_id
call_uuid
call_date
overall_score
gender
language
positive_sentiment
negative_sentiment
neutral_sentiment
call_summary
areas_of_improvement
strengths
focus_areas
products_discussed
greeting
listening_skills
probing
closure
upsell_cross_sell
```

## 4. Original Project Components

The existing project already had:

```text
FastAPI backend
GPT-4o-mini integration
MySQL database
MCP-style retrieval logic
Frontend chatbot
Working MCP server
```

Core files:

```text
api.py
ai_tool_router.py
mysql_mcp_server.py
requirements.txt
.env
```

## 5. Final Project Structure

```text
C:\mcp-ai-tool-router
|-- .env
|-- .env.example
|-- .gitignore
|-- ai_bot.py
|-- ai_tool_router.py
|-- api.py
|-- mysql_mcp_server.py
|-- requirements.txt
|-- README.md
|-- DEPLOYMENT_GUIDE.md
|-- PROJECT_FULL_DOCUMENTATION.md
`-- claude_mcp
    |-- claude_desktop_config.example.json
    |-- README_CLAUDE_MCP.md
    |-- tool_routing_guide.md
    `-- test_queries.md
```

## 6. Main Architecture

### 6.1 FastAPI Chatbot Architecture

```text
User
Frontend Chatbot
FastAPI Backend
GPT-4o-mini Tool Router
MCP-style Retrieval Function
MySQL call_analytics_db.calls
GPT-4o-mini Final Formatter
Frontend Response
```

### 6.2 Claude Desktop MCP Architecture

```text
User
Claude Desktop
MCP Tool Selection
mysql_mcp_server.py
MySQL call_analytics_db.calls
MCP Result
Claude Response
```

Important separation:

```text
Claude/GPT = reasoning and response layer
MCP tools = retrieval layer
MySQL = data layer
```

Claude does not directly connect to MySQL.

MySQL access happens only through the MCP server/retrieval functions.

## 7. MCP Server Details

The MCP server file is:

```text
mysql_mcp_server.py
```

It uses:

```python
FastMCP
```

The server exposes tools using:

```python
@mcp.tool()
```

The MCP server entrypoint is:

```python
if __name__ == "__main__":
    mcp.run()
```

This allows Claude Desktop to start the server as a local MCP process.

## 8. MCP Tools

The project exposes these MCP tools:

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

### 8.1 get_mysql_dataset_summary

Purpose:

```text
Returns database/table summary, total records, columns, and sample full records.
```

Example user query:

```text
Show dataset summary
```

### 8.2 search_mysql_any_value_optimized

Purpose:

```text
Searches any user-provided keyword/value across all dataset columns.
Returns compact important fields.
```

Example user queries:

```text
Show iPhone calls
Show Tamil calls
Find warranty calls
Search pricing calls
```

### 8.3 get_mysql_full_call_by_id

Purpose:

```text
Fetches a complete call record using numeric MySQL id.
```

Example:

```text
Show full details for id 5
```

### 8.4 get_mysql_full_call_by_recording_id

Purpose:

```text
Fetches a complete call record using recording_id.
```

Example:

```text
Show full details for recording id ABC123
```

### 8.5 get_all_issue_patterns

Purpose:

```text
Groups customer issue patterns from call summaries, focus areas, improvement areas, final conclusion, and negative sentiment.
```

Example:

```text
Show issue patterns
```

### 8.6 get_improvement_areas

Purpose:

```text
Finds repeated quality improvement areas across calls.
```

Example:

```text
Show improvement areas
```

### 8.7 get_language_distribution

Purpose:

```text
Groups calls by language.
```

Example:

```text
Show language distribution
```

### 8.8 get_top_products_discussed

Purpose:

```text
Finds the most discussed products in calls.
```

Example:

```text
Top products discussed
```

### 8.9 get_repeated_issue_patterns

Purpose:

```text
Returns high-frequency recurring customer issue categories.
```

Example:

```text
Show repeated customer frustrations
```

## 9. Phase 1 - Existing MCP Server Validation

Goal:

```text
Verify the existing MCP + MySQL setup before connecting Claude or preparing deployment.
```

Steps completed:

```text
1. Confirmed project folder exists.
2. Confirmed mysql_mcp_server.py exists.
3. Confirmed virtual environment exists.
4. Confirmed required packages are installed.
5. Confirmed MySQL configuration points to call_analytics_db.calls.
6. Confirmed 9 MCP tools are registered using @mcp.tool().
7. Confirmed mcp.run() entrypoint exists.
8. Confirmed MySQL80 service is running.
9. Started MCP server manually.
```

Important observation:

```text
The MCP server may appear silent when manually started because it waits for an MCP client over stdio.
```

When stopped using Ctrl + C, a `KeyboardInterrupt` can appear. That is normal during manual testing.

Phase 1 result:

```text
Existing MCP server is working and ready for Claude Desktop integration.
```

## 10. Phase 2 - Claude MCP Project Structure

Goal:

```text
Create a separate Claude integration folder without modifying existing MCP logic.
```

Created folder:

```text
claude_mcp
```

Created files:

```text
claude_mcp\claude_desktop_config.example.json
claude_mcp\README_CLAUDE_MCP.md
claude_mcp\tool_routing_guide.md
claude_mcp\test_queries.md
```

Purpose of each file:

```text
claude_desktop_config.example.json
Example MCP server registration for Claude Desktop.

README_CLAUDE_MCP.md
Claude Desktop setup guide.

tool_routing_guide.md
Explains which query should map to which MCP tool.

test_queries.md
List of prompts to verify Claude MCP tool usage.
```

No changes were made to:

```text
mysql_mcp_server.py
```

## 11. Phase 3 - Claude Desktop MCP Configuration

Goal:

```text
Register the existing MCP server with Claude Desktop.
```

Claude Desktop config file:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Added MCP registration:

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

Meaning:

```text
Claude Desktop starts the project Python executable.
That Python executable runs mysql_mcp_server.py.
Claude discovers tools exposed by @mcp.tool().
Claude can call those tools during chat.
```

Important:

```text
Claude Desktop must be fully restarted after changing claude_desktop_config.json.
Claude browser/website does not connect to local MCP servers.
Use Claude Desktop app.
```

Phase 3 verification:

```text
Claude discovered the call analytics MCP tools.
Claude successfully used search_mysql_any_value_optimized for "Show iPhone calls".
Claude returned 650 iPhone matches from 4,792 records.
```

Phase 3 result:

```text
Claude Desktop is connected to the local MCP server.
```

## 12. Phase 4 - Claude MCP Tool Verification

Goal:

```text
Verify all major MCP tools from Claude Desktop.
```

Verified tools:

```text
[done] search_mysql_any_value_optimized
[done] get_mysql_dataset_summary
[done] get_mysql_full_call_by_id
[done] get_mysql_full_call_by_recording_id
[done] get_language_distribution
[done] get_top_products_discussed
[done] get_improvement_areas
[done] get_all_issue_patterns
[done] get_repeated_issue_patterns
```

Verified example prompts:

```text
Show iPhone calls
Show dataset summary
Show full details for id 5
Show full details for recording id <recording_id>
Show language distribution
Top products discussed
Show improvement areas
Show issue patterns
Show repeated customer frustrations
```

Example verified result:

```text
Show dataset summary returned:
Database: call_analytics_db
Table: calls
Total records: 4,792
Total columns: 25
```

Phase 4 result:

```text
Claude MCP integration is fully verified.
```

## 13. Deployment Preparation Requirement

After Claude MCP verification, the project was prepared for server deployment handover.

Important instructions followed:

```text
Do not host the project.
Do not deploy the project.
Do not change business logic.
Do not break existing functionality.
```

Goal:

```text
Make the project deployment-ready so another team/server admin can host it later.
```

## 14. Deployment Preparation - Environment Variables

Hardcoded deployment values were moved into environment variables.

Supported variables:

```text
OPENAI_API_KEY
MYSQL_HOST
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
MYSQL_PORT
PORT
FRONTEND_ORIGIN
```

Created:

```text
.env.example
```

Example:

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

The real `.env` file remains private and is ignored by Git.

Security note:

```text
Do not commit real API keys or database passwords.
Use .env.example only as a template.
```

## 15. Deployment Preparation - MySQL Configuration

Previously, MySQL values were hardcoded in `mysql_mcp_server.py`.

Now they are loaded using environment variables:

```text
MYSQL_HOST
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
MYSQL_PORT
```

This supports:

```text
Local MySQL
Cloud MySQL
Different database users
Different ports
```

without changing code.

## 16. Deployment Preparation - FastAPI Entry Point

The existing FastAPI app was in:

```text
api.py
```

Deployment requirement:

```powershell
uvicorn ai_bot:app --host 0.0.0.0 --port 8001
```

Created:

```text
ai_bot.py
```

Content:

```python
from api import app
```

Purpose:

```text
Expose the existing FastAPI app under the deployment entrypoint ai_bot:app.
```

No business logic was added to `ai_bot.py`.

## 17. Deployment Preparation - Health Endpoint

Required endpoint:

```http
GET /
```

Required response:

```json
{
  "status": "running",
  "message": "AI Call Analytics Chatbot Backend is running"
}
```

The health endpoint was updated and verified.

## 18. Deployment Preparation - CORS

CORS was made configurable using:

```text
FRONTEND_ORIGIN
```

Supported local origins:

```text
http://localhost:5500
http://127.0.0.1:5500
```

Multiple origins can be configured using comma-separated values:

```env
FRONTEND_ORIGIN=http://localhost:5500,http://127.0.0.1:5500
```

For production:

```env
FRONTEND_ORIGIN=https://your-production-frontend-domain.example
```

## 19. Deployment Preparation - Requirements

Verified `requirements.txt`:

```text
openai
python-dotenv
mysql-connector-python
mcp
fastapi
uvicorn
```

These packages support:

```text
OpenAI API integration
Environment variable loading
MySQL connection
MCP server/tools
FastAPI backend
Uvicorn server
```

## 20. Deployment Preparation - Git Ignore

Updated `.gitignore` to exclude:

```text
.env
venv/
.venv/
__pycache__/
**/__pycache__/
*.pyc
logs/
*.log
```

Purpose:

```text
Prevent secrets, virtual environments, cache files, and logs from being committed.
```

## 21. Deployment Documentation Created

Created:

```text
DEPLOYMENT_GUIDE.md
```

Updated:

```text
README.md
```

Documentation includes:

```text
Project overview
Architecture
Folder structure
Environment variables
Installation steps
Database setup
Database export/import
Backend startup
Frontend startup notes
API endpoints
Sample queries
Troubleshooting
Verification checklist
```

## 22. Database Export And Restore

Export command:

```powershell
mysqldump -u root -p call_analytics_db > call_analytics_db.sql
```

Restore command:

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS call_analytics_db;"
mysql -u root -p call_analytics_db < call_analytics_db.sql
```

Server admins should:

```text
1. Export the database from the source machine.
2. Copy the SQL dump to the target server.
3. Create/import the database.
4. Configure MySQL env vars in .env.
5. Start the backend.
```

## 23. Backend Startup Commands

Fixed local/server port:

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

## 24. API Endpoints

### 24.1 Health Check

```http
GET /
```

Response:

```json
{
  "status": "running",
  "message": "AI Call Analytics Chatbot Backend is running"
}
```

### 24.2 Chat Endpoint

```http
POST /chat
```

Request:

```json
{
  "message": "Show dataset summary"
}
```

Response includes:

```text
tool_decision
tool_result
final_answer
```

## 25. Deployment Verification Performed

Verification completed:

```text
Python files compile successfully.
ai_bot:app imports correctly.
GET / health endpoint works.
MySQL retrieval works from environment-based config.
POST /chat works with GPT routing, MySQL retrieval, and final answer formatting.
```

Because port 8001 was already occupied by another backend process on the local machine, final verification was done on temporary port 8002.

This was only a local smoke test.

No hosting or deployment was performed.

## 26. Verified `/chat` Flow

Test prompt:

```text
Show dataset summary
```

Verified behavior:

```text
GPT selected get_mysql_dataset_summary.
MCP-style retrieval fetched MySQL data.
GPT formatted the final response.
```

Verified dataset result:

```text
Database: call_analytics_db
Table: calls
Total records: 4,792
Total columns: 25
```

## 27. Files Created

```text
.env.example
ai_bot.py
DEPLOYMENT_GUIDE.md
PROJECT_FULL_DOCUMENTATION.md
claude_mcp\claude_desktop_config.example.json
claude_mcp\README_CLAUDE_MCP.md
claude_mcp\tool_routing_guide.md
claude_mcp\test_queries.md
```

## 28. Files Modified

```text
.gitignore
api.py
mysql_mcp_server.py
README.md
.env
```

## 29. Important Files And Their Purpose

### .env.example

Template showing required environment variables.

Used by deployment/admin team to create real `.env`.

### ai_bot.py

Deployment entrypoint.

Allows:

```powershell
uvicorn ai_bot:app --host 0.0.0.0 --port 8001
```

### DEPLOYMENT_GUIDE.md

Step-by-step deployment handover guide for server administrators.

### README.md

Professional project overview and setup guide.

### mysql_mcp_server.py

MCP server and MySQL retrieval tools.

### ai_tool_router.py

GPT-4o-mini tool routing and final response formatting.

### api.py

FastAPI backend app and `/chat` endpoint.

### claude_mcp/

Claude Desktop MCP setup and testing documentation.

## 30. What Was Not Done

By requirement, the following were not done:

```text
No hosting.
No production deployment.
No business logic changes.
No frontend redesign.
No database schema changes.
No replacement of existing MCP tools.
```

## 31. Final Handover Checklist

Server/admin team should verify:

```text
[ ] Project files copied to server
[ ] Python installed
[ ] Virtual environment created
[ ] requirements.txt installed
[ ] .env created from .env.example
[ ] OPENAI_API_KEY configured
[ ] MySQL database imported
[ ] MYSQL_HOST configured
[ ] MYSQL_USER configured
[ ] MYSQL_PASSWORD configured
[ ] MYSQL_DATABASE configured
[ ] MYSQL_PORT configured
[ ] FRONTEND_ORIGIN configured
[ ] Backend starts with uvicorn ai_bot:app
[ ] GET / returns running status
[ ] POST /chat works
[ ] GPT routing works
[ ] MySQL retrieval works
[ ] Frontend can call backend
[ ] Sample queries return correct answers
```

## 32. Sample Queries For Final Demo

```text
Show dataset summary
Show iPhone calls
Show Tamil calls
Show full details for id 5
Show full details for recording id <recording_id>
Show language distribution
Top products discussed
Show improvement areas
Show issue patterns
Show repeated customer frustrations
```

## 33. Lead-Friendly Final Summary

The AI Call Analytics Chatbot project has been prepared for deployment handover.

The system supports two validated interfaces:

```text
1. FastAPI chatbot backend using GPT-4o-mini
2. Claude Desktop integration using MCP tools
```

The existing MySQL/MCP retrieval logic remains intact.

Hardcoded database settings were moved to environment variables.

The backend now has a clean deployment entrypoint:

```text
ai_bot:app
```

The required health check is implemented.

Deployment documentation and admin handover instructions are complete.

The project has not been hosted or deployed. It is ready for another team to deploy on their own infrastructure.

