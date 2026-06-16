import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ai_tool_router import decide_tool, execute_tool, format_final_response


load_dotenv()

app = FastAPI(
    title="AI Call Analytics Chatbot Backend",
    description="FastAPI backend for AI-driven call analytics chat.",
    version="1.0.0",
)

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Request body for chat messages."""

    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Response body returned by the router API."""

    tool_decision: dict
    tool_result: dict
    final_answer: str


@app.get("/")
def health_check() -> dict:
    """Return API health status."""
    return {
        "status": "running",
        "message": "AI Call Analytics Chatbot Backend is running",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> dict:
    """Route a user message, execute the selected tool, and format output."""
    user_query = request.message.strip()

    decision = decide_tool(user_query)
    tool_result = execute_tool(decision)
    final_answer = format_final_response(
        user_query=user_query,
        decision=decision,
        tool_result=tool_result,
    )

    return {
        "tool_decision": decision,
        "tool_result": tool_result,
        "final_answer": final_answer,
    }
