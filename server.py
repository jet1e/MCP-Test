#!/usr/bin/env python3
import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Any, Dict, List
import json

from mcp.server import Server
import mcp.types as types

app = FastAPI()
server = Server("secret-text-server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="get_secret_text",
            description="Returns a secret text",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls."""
    if name == "get_secret_text":
        return [
            types.TextContent(
                type="text",
                text="Hello World!"
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """Handle MCP requests over HTTP"""
    method = request.get("method")
    
    if method == "tools/list":
        tools = await handle_list_tools()
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"tools": [tool.dict() for tool in tools]}
        }
    elif method == "tools/call":
        params = request.get("params", {})
        result = await handle_call_tool(
            params.get("name"), 
            params.get("arguments", {})
        )
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"content": [content.dict() for content in result]}
        }
    
    return {"error": "Unknown method"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)