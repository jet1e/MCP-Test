#!/usr/bin/env python3
import asyncio
import os
from fastapi import FastAPI, Request, HTTPException
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
                text="Hello World! The secret text is: ANTHROPIC"
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

# Health check endpoints
@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "secret-text-server"}

@app.head("/")
async def health_check_head():
    return {"status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# MCP endpoint
@app.post("/")
async def mcp_root(request: Request):
    """Handle MCP requests at root"""
    try:
        body = await request.json()
        # Use the actual MCP server to handle requests
        response = await server.handle_request(body)
        return response
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP requests at /mcp"""
    try:
        body = await request.json()
        # Use the actual MCP server to handle requests
        response = await server.handle_request(body)
        return response
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}

# OAuth endpoints (return 404 as expected)
@app.get("/.well-known/oauth-authorization-server")
@app.get("/.well-known/oauth-protected-resource")
@app.post("/register")
async def oauth_not_supported():
    raise HTTPException(status_code=404, detail="OAuth not supported")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)