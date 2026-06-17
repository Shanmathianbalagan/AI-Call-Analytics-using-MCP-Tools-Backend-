import os
from typing import Any

import mysql.connector
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from mysql_mcp_server import (
    get_all_issue_patterns,
    get_improvement_areas,
    get_language_distribution,
    get_mysql_dataset_summary,
    get_mysql_full_call_by_id,
    get_mysql_full_call_by_recording_id,
    get_repeated_issue_patterns,
    get_top_products_discussed,
    search_mysql_any_value_optimized,
    get_connection,
)


load_dotenv()

MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")

app = FastAPI(
    title="Hosted MCP Server",
    description="Authenticated HTTP access to MySQL-backed MCP tools.",
    version="1.0.0",
)


class ToolCallRequest(BaseModel):
    """Request body for authenticated hosted tool execution."""

    tool_name: str = Field(..., min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    """Response body returned by the hosted tool endpoint."""

    tool_name: str
    result: dict[str, Any]


ALLOWED_TOOLS = {
    "get_mysql_dataset_summary": get_mysql_dataset_summary,
    "search_mysql_any_value_optimized": search_mysql_any_value_optimized,
    "get_mysql_full_call_by_id": get_mysql_full_call_by_id,
    "get_mysql_full_call_by_recording_id": get_mysql_full_call_by_recording_id,
    "get_all_issue_patterns": get_all_issue_patterns,
    "get_improvement_areas": get_improvement_areas,
    "get_language_distribution": get_language_distribution,
    "get_top_products_discussed": get_top_products_discussed,
    "get_repeated_issue_patterns": get_repeated_issue_patterns,
}


def verify_bearer_token(authorization: str | None = Header(default=None)) -> None:
    """Require Authorization: Bearer <MCP_AUTH_TOKEN> for hosted tool calls."""

    if not MCP_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MCP_AUTH_TOKEN is not configured.",
        )

    expected_header = f"Bearer {MCP_AUTH_TOKEN}"

    if authorization != expected_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return service and database health without exposing secrets."""

    database_status = "connected"

    try:
        conn = get_connection()
        conn.close()
    except mysql.connector.Error:
        database_status = "disconnected"

    return {
        "status": "running",
        "service": "Hosted MCP Server",
        "database": database_status,
    }


@app.post(
    "/tools/call",
    response_model=ToolCallResponse,
    dependencies=[Depends(verify_bearer_token)],
)
def call_tool(request: ToolCallRequest) -> dict[str, Any]:
    """Execute one whitelisted MCP tool with validated JSON arguments."""

    if request.tool_name not in ALLOWED_TOOLS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported tool_name: {request.tool_name}",
        )

    if not isinstance(request.arguments, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="arguments must be a JSON object.",
        )

    tool = ALLOWED_TOOLS[request.tool_name]

    try:
        result = tool(**request.arguments)
    except TypeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid arguments for {request.tool_name}: {error}",
        ) from error
    except mysql.connector.Error as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database tool execution failed: {error}",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {error}",
        ) from error

    return {
        "tool_name": request.tool_name,
        "result": result,
    }
