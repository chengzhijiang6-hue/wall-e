"""Mem0 MCP Server — 让 Hermes Agent 通过 MCP 协议管理记忆。

工具:
  mem0_add     — 添加记忆（从对话中自动提取事实）
  mem0_search  — 语义搜索记忆
  mem0_list    — 列出所有记忆
  mem0_delete  — 删除指定记忆

Usage:
    MCP_PORT=59180 python mem0_mcp_server.py

Health check: http://localhost:59180/health
MCP endpoint: http://localhost:59180/sse
"""

import os
import json
import httpx
import uvicorn
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# ─── Configuration ────────────────────────────────────────

MEM0_API_URL = os.getenv("MEM0_API_URL", "http://localhost:59110")
MEM0_API_KEY = os.getenv("MEM0_API_KEY", "mem0-admin-key-Z9x9C3vB2nM1aS0dF7gH5jK4l")
DEFAULT_USER_ID = os.getenv("MEM0_DEFAULT_USER_ID", "ethan")
PROXY = os.getenv("HTTP_PROXY", "http://10.197.216.7:3128")

server = Server("mem0-mcp")

# ─── HTTP Client ──────────────────────────────────────────

def get_client():
    """创建 HTTP 客户端 — localhost 请求不走代理"""
    return httpx.Client(
        proxy=PROXY,
        timeout=30.0,
        headers={
            "Authorization": f"Bearer {MEM0_API_KEY}",
            "Content-Type": "application/json",
        },
        transport=httpx.HTTPTransport(proxy=PROXY),
    )


def _api_request(method: str, path: str, **kwargs):
    """发送请求到 Mem0 API — localhost 不走代理"""
    url = f"{MEM0_API_URL}{path}"
    is_localhost = "localhost" in MEM0_API_URL or "127.0.0.1" in MEM0_API_URL
    with httpx.Client(
        proxy=None if is_localhost else PROXY,
        timeout=30.0,
        headers={
            "X-API-Key": MEM0_API_KEY,
            "Content-Type": "application/json",
        },
    ) as client:
        return getattr(client, method)(url, **kwargs)

# ─── Tool Definitions ─────────────────────────────────────

TOOLS = [
    Tool(
        name="mem0_add",
        description="添加记忆。从用户消息中自动提取事实并存储。传入对话消息列表和可选的 user_id。",
        inputSchema={
            "type": "object",
            "properties": {
                "messages": {
                    "type": "string",
                    "description": "要存储的对话内容（纯文本，会自动提取事实）"
                },
                "user_id": {
                    "type": "string",
                    "description": f"用户标识，默认 {DEFAULT_USER_ID}"
                },
            },
            "required": ["messages"],
        },
    ),
    Tool(
        name="mem0_search",
        description="语义搜索记忆。根据查询文本找到最相关的记忆。",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询文本"
                },
                "user_id": {
                    "type": "string",
                    "description": f"用户标识，默认 {DEFAULT_USER_ID}"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量，默认 5"
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="mem0_list",
        description="列出所有记忆。返回记忆 ID、内容和创建时间。",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": f"用户标识，默认 {DEFAULT_USER_ID}"
                },
            },
        },
    ),
    Tool(
        name="mem0_delete",
        description="删除指定记忆。需要提供记忆 ID。",
        inputSchema={
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "要删除的记忆 ID"
                },
            },
            "required": ["memory_id"],
        },
    ),
]


@server.list_tools()
async def list_tools():
    return TOOLS


def _result(text: str):
    return [TextContent(type="text", text=text)]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    user_id = arguments.get("user_id", DEFAULT_USER_ID)

    try:
        if name == "mem0_add":
            return _add_memory(arguments["messages"], user_id)
        elif name == "mem0_search":
            return _search_memories(
                arguments["query"], user_id, arguments.get("limit", 5)
            )
        elif name == "mem0_list":
            return _list_memories(user_id)
        elif name == "mem0_delete":
            return _delete_memory(arguments["memory_id"])
        else:
            return _result(f"未知工具: {name}")
    except Exception as e:
        return _result(f"错误: {e}")


# ─── API Calls ────────────────────────────────────────────

def _add_memory(messages_text: str, user_id: str) -> list:
    """添加记忆 — 将文本包装为对话格式发送"""
    payload = {
        "messages": [
            {"role": "user", "content": messages_text},
            {"role": "assistant", "content": "ok"},
        ],
        "user_id": user_id,
    }
    r = _api_request("post", "/memories", json=payload)
    r.raise_for_status()
    data = r.json()

    results = data.get("results", [])
    if not results:
        return _result("未提取到可存储的记忆")

    lines = []
    for item in results:
        lines.append(f"[{item.get('event', 'ADD')}] {item.get('memory', '')}  (id: {item.get('id', 'N/A')})")
    return _result(f"成功存储 {len(results)} 条记忆:\n" + "\n".join(lines))


def _search_memories(query: str, user_id: str, limit: int) -> list:
    """语义搜索记忆"""
    payload = {
        "query": query,
        "filters": {"user_id": user_id},
    }
    r = _api_request("post", "/search", json=payload)
    r.raise_for_status()
    data = r.json()

    results = data.get("results", [])
    if not results:
        return _result(f"未找到与 \"{query}\" 相关的记忆")

    lines = []
    for i, item in enumerate(results[:limit], 1):
        score = item.get("score", 0)
        memory = item.get("memory", "")
        mid = item.get("id", "N/A")
        lines.append(f"{i}. [{score:.3f}] {memory}  (id: {mid})")
    return _result(f"找到 {len(results)} 条相关记忆:\n" + "\n".join(lines))


def _list_memories(user_id: str) -> list:
    """列出指定用户的记忆"""
    r = _api_request("get", "/memories", params={"user_id": user_id})
    r.raise_for_status()
    data = r.json()

    results = data.get("results", [])
    if not results:
        return _result(f"用户 {user_id} 没有记忆")

    lines = []
    for item in results:
        mid = item.get("id", "N/A")
        memory = item.get("memory", "")
        created = item.get("created_at", "N/A")
        lines.append(f"- [{mid[:8]}...] {memory}  ({created})")
    return _result(f"共 {len(results)} 条记忆:\n" + "\n".join(lines))


def _delete_memory(memory_id: str) -> list:
    """删除指定记忆"""
    r = _api_request("delete", f"/memories/{memory_id}")
    r.raise_for_status()
    return _result(f"已删除记忆: {memory_id}")


# ─── SSE Transport ────────────────────────────────────────

sse_transport = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())
    return Response()


async def handle_messages(request):
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)


async def health(request: Request):
    return JSONResponse({"status": "ok", "service": "mem0-mcp"})


app = Starlette(
    routes=[
        Route("/health", health),
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse_transport.handle_post_message),
    ],
)

if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "59180"))
    print(f"Mem0 MCP Server starting on port {port}")
    print(f"  Mem0 API: {MEM0_API_URL}")
    print(f"  Default user: {DEFAULT_USER_ID}")
    print(f"  Proxy: {PROXY}")
    uvicorn.run(app, host="0.0.0.0", port=port)
