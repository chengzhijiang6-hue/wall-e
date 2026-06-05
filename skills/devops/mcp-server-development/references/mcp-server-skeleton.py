"""MCP Server skeleton — SSE transport, tool registration, health endpoint.

Usage:
    MCP_PORT=18080 python mcp_server.py

Connect IDE to: http://localhost:18080/sse
Health check:   http://localhost:18080/health
"""

import os
import uvicorn
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

server = Server("my-mcp-server")


# ─── Tool Definitions ─────────────────────────────────────

TOOLS = [
    Tool(
        name="hello",
        description="Say hello to someone",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name to greet"}
            },
            "required": ["name"],
        },
    ),
]


@server.list_tools()
async def list_tools():
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "hello":
        return [TextContent(type="text", text=f"Hello, {arguments['name']}!")]
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ─── SSE Transport ────────────────────────────────────────

sse_transport = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())
    return Response()  # REQUIRED: avoid NoneType on client disconnect


async def handle_messages(request):
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)


async def health(request: Request):
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route("/health", health),
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse_transport.handle_post_message),
    ],
)

if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "18080"))
    print(f"MCP Server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
