#!/usr/bin/env python3
import asyncio
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Any, Dict, List
import json
import logging

from mcp.server import Server
import mcp.types as types

# Set up detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info("MCP: Tools list requested")
    return [
        types.Tool(
            name="get_secret_text",
            description="Returns a secret text message",
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
    logger.info(f"MCP: Tool called - {name}")
    
    if name == "get_secret_text":
        return [
            types.TextContent(
                type="text",
                text="Hello World! The secret text is: ANTHROPIC"
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

# Manual MCP request handling
async def handle_mcp_request(request_data: dict) -> dict:
    """Manually handle MCP requests."""
    method = request_data.get("method")
    params = request_data.get("params", {})
    request_id = request_data.get("id")
    
    logger.info(f"Handling MCP method: {method}")
    
    try:
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "secret-text-server",
                        "version": "1.0.0"
                    }
                }
            }
        elif method == "tools/list":
            tools = await handle_list_tools()
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [tool.model_dump() for tool in tools]
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await handle_call_tool(tool_name, arguments)
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [content.model_dump() for content in result]
                }
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }
    
    return response

# Health check endpoints
@app.get("/")
async def health_check():
    logger.info("Health check (GET) requested")
    return {"status": "healthy", "service": "secret-text-server"}

@app.head("/")
async def health_check_head():
    logger.info("Health check (HEAD) requested")
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
        logger.info(f"MCP REQUEST: {json.dumps(body, indent=2)}")
        
        response = await handle_mcp_request(body)
        
        logger.info(f"MCP RESPONSE: {json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"MCP ERROR: {str(e)}", exc_info=True)
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP requests at /mcp"""
    try:
        body = await request.json()
        logger.info(f"MCP REQUEST (/mcp): {json.dumps(body, indent=2)}")
        
        response = await handle_mcp_request(body)
        
        logger.info(f"MCP RESPONSE (/mcp): {json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"MCP ERROR (/mcp): {str(e)}", exc_info=True)
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}

# OAuth endpoints (return 404 as expected)
@app.get("/.well-known/oauth-authorization-server")
@app.get("/.well-known/oauth-protected-resource")
@app.post("/register")
async def oauth_not_supported():
    logger.info("OAuth endpoint accessed (returning 404)")
    raise HTTPException(status_code=404, detail="OAuth not supported")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)