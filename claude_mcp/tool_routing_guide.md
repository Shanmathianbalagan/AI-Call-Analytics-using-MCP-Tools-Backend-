\# Claude MCP Tool Routing Guide



This guide explains how Claude should choose MCP tools based on user intent.



Claude should not directly query MySQL. Claude should retrieve data only by calling MCP tools exposed by `mysql\_mcp\_server.py`.



\## Architecture



```text

User Query

Claude Understands Intent

Claude Selects MCP Tool

MCP Tool Queries MySQL

MCP Tool Returns Data

Claude Explains Result

