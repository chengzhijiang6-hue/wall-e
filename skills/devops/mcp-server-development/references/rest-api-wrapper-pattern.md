# REST API Wrapper MCP Server Pattern

When wrapping an existing REST API (like Mem0, Grafana, etc.) as an MCP server for Hermes Agent integration.

## Architecture

```
Hermes Agent → MCP Protocol (SSE) → MCP Server → HTTP → REST API
```

## Key Design Decisions

### 1. Authentication — Use non-expiring credentials
- Prefer `X-API-Key` header over `Authorization: Bearer <JWT>` for service-to-service
- JWT tokens expire and require refresh logic; API keys don't
- Store API key in environment variable, not hardcoded

### 2. Proxy handling — Skip proxy for localhost
```python
import httpx

def _api_request(method: str, path: str, **kwargs):
    url = f"{API_BASE_URL}{path}"
    is_localhost = "localhost" in API_BASE_URL or "127.0.0.1" in API_BASE_URL
    with httpx.Client(
        proxy=None if is_localhost else PROXY,
        timeout=30.0,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    ) as client:
        return getattr(client, method)(url, **kwargs)
```

**Why**: Corporate proxy (e.g. `10.x.x.x:3128`) intercepts localhost requests and fails with `Connection reset by peer`. Always check if the target is localhost before applying proxy.

### 3. Tool design — Map to CRUD operations
```
add    → POST /resources
search → POST /search (or GET /resources?q=...)
list   → GET /resources
delete → DELETE /resources/{id}
```

### 4. Error handling — Return user-friendly messages
```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "tool_name":
            return _do_operation(arguments)
    except httpx.HTTPStatusError as e:
        return _result(f"API 错误 ({e.response.status_code}): {e.response.text[:200]}")
    except Exception as e:
        return _result(f"错误: {e}")
```

## Template

```python
"""MCP Server wrapping REST API for Hermes Agent.

Usage:
    MCP_PORT=59180 python mcp_server.py
Connect: http://localhost:59180/sse
Health:  http://localhost:59180/health
"""
import os, httpx, uvicorn
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

API_URL = os.getenv("API_URL", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "")
PROXY = os.getenv("HTTP_PROXY", "")

server = Server("my-api-mcp")

TOOLS = [
    Tool(name="example_tool", description="...", inputSchema={...}),
]

@server.list_tools()
async def list_tools():
    return TOOLS

def _result(text):
    return [TextContent(type="text", text=text)]

@server.call_tool()
async def call_tool(name, arguments):
    try:
        # dispatch to API calls
        ...
    except Exception as e:
        return _result(f"Error: {e}")

# SSE transport
sse = SseServerTransport("/messages/")
async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())
    return Response()

app = Starlette(routes=[
    Route("/health", lambda r: JSONResponse({"status": "ok"})),
    Route("/sse", endpoint=handle_sse),
    Mount("/messages/", app=sse.handle_post_message),
])

if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "18080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## Registration in Hermes config.yaml

```yaml
mcp_servers:
  MY-API:
    url: "http://localhost:59180/sse"
    transport: sse
    timeout: 60
    connect_timeout: 10
```

**Note**: Config key is `mcp_servers` (snake_case), NOT `mcpServers` (camelCase).
New session required to load MCP tools after config change.
