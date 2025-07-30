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
    tools = [
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
    logger.info(f"MCP: Returning {len(tools)} tools")
    return tools

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls."""
    logger.info(f"MCP: Tool called - name: {name}, arguments: {arguments}")
    if name == "get_secret_text":
        result = [
            types.TextContent(
                type="text",
                text="Hello World! The secret text is: ANTHROPIC"
            )
        ]
        logger.info(f"MCP: Tool result: {result}")
        return result
    else:
        logger.error(f"MCP: Unknown tool requested: {name}")
        raise ValueError(f"Unknown tool: {name}")

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
        
        response = await server._handle_request(body)
        
        logger.info(f"MCP RESPONSE: {json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"MCP ERROR: {str(e)}", exc_info=True)
        error_response = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}
        try:
            if "id" in body:
                error_response["id"] = body["id"]
        except:
            pass
        return error_response

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP requests at /mcp"""
    try:
        body = await request.json()
        logger.info(f"MCP REQUEST (/mcp): {json.dumps(body, indent=2)}")
        
        response = await server._handle_request(body)
        
        logger.info(f"MCP RESPONSE (/mcp): {json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"MCP ERROR (/mcp): {str(e)}", exc_info=True)
        error_response = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}
        try:
            if "id" in body:
                error_response["id"] = body["id"]
        except:
            pass
        return error_response

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