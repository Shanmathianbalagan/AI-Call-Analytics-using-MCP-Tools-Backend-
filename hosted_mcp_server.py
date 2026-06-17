import os
import secrets
from typing import Any

import mysql.connector
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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

MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "").strip()

app = FastAPI(
    title="Hosted MCP Server",
    description=(
        "Authenticated HTTP wrapper around the existing MySQL-backed MCP "
        "tools. Local Claude Desktop stdio MCP mode remains in "
        "mysql_mcp_server.py; this app is for hosted/server access."
    ),
    version="1.0.0",
)

bearer_scheme = HTTPBearer(
    scheme_name="MCP Bearer Token",
    description="Use the Render MCP_AUTH_TOKEN value as a Bearer token.",
)


class ToolCallRequest(BaseModel):
    """Request body for authenticated hosted tool execution."""

    tool_name: str = Field(
        ...,
        min_length=1,
        description="Name of one whitelisted MCP tool to execute.",
        examples=["search_mysql_any_value_optimized"],
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON arguments passed to the selected MCP tool.",
        examples=[{"search_value": "iPhone", "limit": 5}],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tool_name": "get_mysql_dataset_summary",
                    "arguments": {"limit": 1},
                },
                {
                    "tool_name": "search_mysql_any_value_optimized",
                    "arguments": {"search_value": "iPhone", "limit": 5},
                },
                {
                    "tool_name": "get_mysql_full_call_by_id",
                    "arguments": {"id": 1},
                },
            ]
        }
    }


class ToolCallResponse(BaseModel):
    """Response body returned by the hosted tool endpoint."""

    tool_name: str = Field(
        ...,
        description="Tool that was executed.",
        examples=["get_mysql_dataset_summary"],
    )
    result: dict[str, Any] = Field(
        ...,
        description="JSON result returned by the existing MCP tool function.",
    )


TOOL_DESCRIPTIONS = {
    "get_mysql_dataset_summary": "Return database/table summary, columns, counts, and sample records.",
    "search_mysql_any_value_optimized": "Search a keyword/value across all MySQL columns and return compact matching records.",
    "get_mysql_full_call_by_id": "Fetch one full call record by numeric MySQL id.",
    "get_mysql_full_call_by_recording_id": "Fetch one full call record by recording_id.",
    "get_all_issue_patterns": "Analyze grouped customer issue patterns across calls.",
    "get_improvement_areas": "Analyze repeated call quality improvement areas.",
    "get_language_distribution": "Return calls grouped by language.",
    "get_top_products_discussed": "Return ranked products discussed in calls.",
    "get_repeated_issue_patterns": "Return high-frequency recurring issue categories.",
}

TOOL_USAGE_GUIDE = {
    "get_mysql_dataset_summary": {
        "when_to_use": [
            "User asks for dataset summary, database overview, table columns, total records, or sample records.",
            "User asks what data is available before asking a more specific question.",
        ],
        "arguments": {
            "limit": "Optional integer. Number of sample records to return. Default is 3.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Show dataset summary",
            "Give me database overview",
            "How many records are there?",
        ],
        "example_tool_call": {
            "tool_name": "get_mysql_dataset_summary",
            "arguments": {"limit": 3},
        },
    },
    "search_mysql_any_value_optimized": {
        "when_to_use": [
            "User searches for a keyword, product, language, issue, sentiment, offer, topic, gender, or any general value.",
            "User asks for matching calls but does not ask for one specific full record.",
        ],
        "arguments": {
            "search_value": "Required string to search across all columns.",
            "limit": "Optional integer. Number of compact records to return. Default is 5.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Show iPhone calls",
            "Show Tamil calls",
            "Find warranty calls",
            "Search pricing calls from 2026-06-08 to 2026-06-10",
        ],
        "example_tool_call": {
            "tool_name": "search_mysql_any_value_optimized",
            "arguments": {"search_value": "iPhone", "limit": 5},
        },
    },
    "get_mysql_full_call_by_id": {
        "when_to_use": [
            "User asks for complete/full details for a specific numeric id.",
            "Use after compact search results when the user chooses a specific id.",
        ],
        "arguments": {
            "id": "Required integer MySQL id.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Show full details for id 5",
            "Open record id 10",
        ],
        "example_tool_call": {
            "tool_name": "get_mysql_full_call_by_id",
            "arguments": {"id": 5},
        },
    },
    "get_mysql_full_call_by_recording_id": {
        "when_to_use": [
            "User asks for complete/full details using recording_id.",
            "Use when the identifier is a recording id string instead of numeric id.",
        ],
        "arguments": {
            "recording_id": "Required string recording_id.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Show full details for recording id rec-test-001",
            "Get complete record for recording id ABC123",
        ],
        "example_tool_call": {
            "tool_name": "get_mysql_full_call_by_recording_id",
            "arguments": {"recording_id": "rec-test-001"},
        },
    },
    "get_all_issue_patterns": {
        "when_to_use": [
            "User asks for all issue patterns, customer problems, complaints, or pain points.",
            "Use for broad issue analysis across the dataset.",
        ],
        "arguments": {
            "limit": "Optional integer. Number of issue categories to return. Default is 10.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Show issue patterns",
            "What problems are customers discussing?",
            "Group all customer issues",
        ],
        "example_tool_call": {
            "tool_name": "get_all_issue_patterns",
            "arguments": {"limit": 10},
        },
    },
    "get_improvement_areas": {
        "when_to_use": [
            "User asks where agents should improve or asks for quality improvement areas.",
            "Use for repeated call-quality weaknesses such as greeting, listening, probing, or closure.",
        ],
        "arguments": {
            "limit": "Optional integer. Number of improvement areas to return. Default is 10.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Show improvement areas",
            "Where should agents improve?",
            "Analyze call quality improvement points",
        ],
        "example_tool_call": {
            "tool_name": "get_improvement_areas",
            "arguments": {"limit": 10},
        },
    },
    "get_language_distribution": {
        "when_to_use": [
            "User asks for calls grouped by language or language comparison.",
            "Use for language counts and distribution.",
        ],
        "arguments": {
            "limit": "Optional integer. Number of language buckets to return. Default is 20.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Show language distribution",
            "How many calls per language?",
            "Which language has the most calls?",
        ],
        "example_tool_call": {
            "tool_name": "get_language_distribution",
            "arguments": {"limit": 20},
        },
    },
    "get_top_products_discussed": {
        "when_to_use": [
            "User asks for top products, popular products, or most discussed products.",
            "Use for product frequency analysis from products_discussed.",
        ],
        "arguments": {
            "limit": "Optional integer. Number of products to return. Default is 10.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Top products discussed",
            "Which products are customers talking about?",
            "Show most discussed products",
        ],
        "example_tool_call": {
            "tool_name": "get_top_products_discussed",
            "arguments": {"limit": 10},
        },
    },
    "get_repeated_issue_patterns": {
        "when_to_use": [
            "User asks for recurring issues, repeated complaints, or high-frequency customer frustrations.",
            "Use when the user wants only repeated/high-frequency issues instead of all issue categories.",
        ],
        "arguments": {
            "limit": "Optional integer. Number of repeated issue categories to return. Default is 10.",
            "minimum_frequency": "Optional integer. Minimum frequency threshold. Default is 3.",
            "start_date": "Optional YYYY-MM-DD filter on call_date.",
            "end_date": "Optional YYYY-MM-DD filter on call_date.",
        },
        "example_user_queries": [
            "Show repeated customer frustrations",
            "What are the recurring issues?",
            "Find frequent customer problems",
        ],
        "example_tool_call": {
            "tool_name": "get_repeated_issue_patterns",
            "arguments": {"limit": 10, "minimum_frequency": 3},
        },
    },
}

AI_CLIENT_INSTRUCTIONS = {
    "role": "Use this hosted MCP API as a retrieval layer for call analytics data.",
    "flow": [
        "Understand the user query.",
        "Choose exactly one whitelisted tool from /tools.",
        "Call POST /tools/call with Authorization: Bearer <MCP_AUTH_TOKEN>.",
        "Use only the returned JSON result to answer the user.",
        "Do not directly query MySQL.",
        "Do not invent records, counts, ids, summaries, or dates.",
    ],
    "routing_rules": [
        "Use search_mysql_any_value_optimized for keyword/product/language/topic searches.",
        "Use get_mysql_dataset_summary for overview, columns, total records, and sample records.",
        "Use get_mysql_full_call_by_id for full details by numeric id.",
        "Use get_mysql_full_call_by_recording_id for full details by recording_id.",
        "Use get_language_distribution for language counts.",
        "Use get_top_products_discussed for product frequency.",
        "Use get_improvement_areas for agent/call quality improvement analysis.",
        "Use get_all_issue_patterns for broad customer issue grouping.",
        "Use get_repeated_issue_patterns for recurring or high-frequency customer complaints.",
    ],
    "date_filter_rule": (
        "If the user gives a date range, pass start_date and end_date as "
        "YYYY-MM-DD when the selected tool supports them."
    ),
    "response_rule": (
        "After the tool returns, summarize the result in human-readable language. "
        "Mention counts, matched records, rankings, trends, and no-result cases clearly."
    ),
}


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


def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> None:
    """Require Authorization: Bearer <MCP_AUTH_TOKEN> for hosted tool calls."""

    if not MCP_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MCP_AUTH_TOKEN is not configured.",
        )

    if (
        credentials.scheme.lower() != "bearer"
        or not secrets.compare_digest(credentials.credentials.strip(), MCP_AUTH_TOKEN)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


@app.get(
    "/",
    tags=["Service"],
    summary="Hosted MCP service information",
)
def service_info() -> dict[str, Any]:
    """Explain the hosted MCP HTTP endpoints."""

    return {
        "status": "running",
        "service": "Hosted MCP Server",
        "description": (
            "Use /health to check service/database status and POST "
            "/tools/call with Bearer authentication to execute MCP tools."
        ),
        "endpoints": {
            "health": "GET /health",
            "tool_call": "POST /tools/call",
            "docs": "GET /docs",
        },
        "authentication": "Authorization: Bearer <MCP_AUTH_TOKEN>",
        "supported_tools": TOOL_DESCRIPTIONS,
        "ai_client_instructions_url": "GET /instructions",
    }


@app.get(
    "/health",
    tags=["Service"],
    summary="Health check",
    description="Returns service status and whether the configured MySQL database can be reached.",
)
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
    tags=["MCP Tools"],
    summary="Execute a whitelisted MCP tool",
    description=(
        "Execute one existing MySQL-backed MCP tool over HTTP. Requires "
        "Authorization: Bearer <MCP_AUTH_TOKEN>. The server only allows "
        "the whitelisted tool names documented by GET /tools."
    ),
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


@app.get(
    "/tools",
    tags=["MCP Tools"],
    summary="List supported hosted MCP tools",
    description="Returns the whitelisted tool names and short descriptions.",
)
def list_tools(_: None = Depends(verify_bearer_token)) -> dict[str, Any]:
    """Return the hosted MCP tool whitelist."""

    return {
        "tools": [
            {
                "tool_name": tool_name,
                "description": TOOL_DESCRIPTIONS[tool_name],
                "usage": TOOL_USAGE_GUIDE[tool_name],
            }
            for tool_name in ALLOWED_TOOLS
        ]
    }


@app.get(
    "/instructions",
    tags=["MCP Tools"],
    summary="AI client instructions for hosted MCP tool routing",
    description=(
        "Returns routing guidance that an AI client can use to decide which "
        "hosted MCP tool to call for a user query."
    ),
)
def get_ai_client_instructions(
    _: None = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """Return AI-facing instructions for tool selection and response behavior."""

    return {
        "instructions": AI_CLIENT_INSTRUCTIONS,
        "tools": TOOL_USAGE_GUIDE,
        "tool_call_endpoint": "POST /tools/call",
        "auth_header": "Authorization: Bearer <MCP_AUTH_TOKEN>",
    }
