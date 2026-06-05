---
name: mcp-server-development
category: devops
description: MCP (Model Context Protocol) Server development with Python SDK — correct API patterns, SSE transport, tool registration, and Docker deployment integration.
---

# MCP Server Development

## Purpose
Build MCP-compliant servers using the Python `mcp` SDK, exposing tools via SSE transport for IDE integration (Claude Code, VS Code, etc.).

## Trigger Conditions
- Building an MCP server from scratch
- Registering tools with the MCP Python SDK
- Setting up SSE transport for MCP
- Integrating MCP server with Docker deployment

---

## MCP Python SDK API (v1.27.x)

### Correct Tool Registration Pattern

The `Server` object does NOT have a `@server.tool()` decorator. Use this pattern instead:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-server")

# Step 1: Define tool schemas as Tool objects
TOOLS = [
    Tool(
        name="my_tool",
        description="What this tool does",
        inputSchema={
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "param description"}
            },
            "required": ["param1"],
        },
    ),
]

# Step 2: Register list handler
@server.list_tools()
async def list_tools():
    return TOOLS

# Step 3: Register call handler (single dispatcher for all tools)
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_tool":
        result = do_something(arguments["param1"])
        return [TextContent(type="text", text=result)]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
```

### Pitfall: `@server.tool()` does not exist
**Symptom**: `AttributeError: 'Server' object has no attribute 'tool'`
**Fix**: Use `@server.list_tools()` + `@server.call_tool()` pattern above.

---

## SSE Transport with Starlette

```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

sse_transport = SseServerTransport("/messages/")

async def handle_sse(request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())
    return Response()  # REQUIRED: avoid NoneType error on client disconnect

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
```

### Pitfall: `handle_sse` must return `Response()`
**Symptom**: `TypeError: 'NoneType' object is not callable` when MCP client disconnects from SSE
**Root cause**: Starlette route handlers must return a Response. `handle_sse` returns None after the `async with` block ends.
**Fix**: Add `return Response()` after the `async with sse_transport.connect_sse(...)` block. Import `Response` from `starlette.responses`.
**Ref**: MCP SDK v1.27.1 source docstring explicitly documents this requirement.

### IDE Connection
Configure MCP client in IDE to connect to: `http://localhost:<port>/sse`

---

## Docker Deployment Integration

### Pitfall: Source code COPY vs Volume Mount divergence

When developing with Docker, source files are COPY'd at build time into the image. If you also mount the project directory as a volume, there are TWO copies of the source:

| Path | Source | Staleness |
|------|--------|-----------|
| `/app/src/` | COPY at build time | Frozen until rebuild |
| `/app/data/src/` | Volume mount from host | Always current |

**Implication**: Code changes on the host are only visible at the volume mount path (`/app/data/src/`), NOT at the COPY path (`/app/src/`).

**Solutions**:
1. **Rebuild container** after each source change: `docker-compose down && docker-compose up -d --build`
2. **Use volume-mounted source for testing**: Run scripts via `docker exec <container> python /app/data/src/script.py`
3. **Mount source directly** (alternative): Change volume mount to `- ./src:/app/src` so source is always current

### Health check endpoint
Always include a `/health` endpoint alongside SSE for container health verification:
```bash
curl -s --noproxy '*' http://localhost:<port>/health
# Note: use --noproxy '*' in WSL to avoid corporate proxy intercepting localhost
```

---

## Required Dependencies

```
# requirements.txt
mcp
fastapi          # or just starlette
uvicorn
httpx            # for proxy support in LLM clients
```

### Pitfall: MCP Server Requires Hermes Venv Python

The `mcp` Python package is installed in the Hermes venv (`/mnt/c/wsl/hermes_official/venv/`), NOT in the system Python. Running an MCP server with `python3` (system) will fail with `ModuleNotFoundError: No module named 'mcp'`.

**Fix**: Always use the hermes venv Python to start MCP servers:
```bash
MCP_PORT=59180 /mnt/c/wsl/hermes_official/venv/bin/python3 mem0_mcp_server.py
```

**Why**: The `mcp` package is an optional dependency of hermes-agent, installed via `pip install mcp` in the venv. System Python (`/usr/bin/python3`) has its own package set.

### Pitfall: MCP Tools Only Load at Session Start

MCP tools registered in `~/.hermes/config.yaml` under `mcp_servers` are loaded when a Hermes session starts. If the MCP server is not running at that point, the tools won't be available in that session. There is no hot-reload.

**Fix**:
1. Start the MCP server first
2. Tell user to start a new Hermes session
3. Tools appear in the next session

---

## Full Working Skeleton

See `references/mcp-server-skeleton.py` for a complete, tested MCP server template with:
- Tool registration pattern
- SSE transport
- Health endpoint
- CLI entry point

## LLM-Backed Tools

When a tool needs to call an LLM (Q&A, content generation, summarization):
- Collect context from filesystem or DB, truncate to fit token budget
- Use lazy global provider singleton (don't recreate client per call)
- Use `max_tokens >= 512` for reasoning models (MiMo), `>= 1024` for Q&A
- Handle empty knowledge base gracefully

See [LLM-backed tool pattern](references/llm-backed-tool-pattern.md) for implementation.

## Pipeline Integration

When wrapping existing pipeline modules (ingest, index, query) as MCP tools:
- Tools are thin dispatchers; business logic stays in pipeline modules
- Use `sys.path.insert(0, os.path.dirname(__file__))` for sibling imports
- Test with volume-mounted source, then rebuild to bake in

See [MCP + pipeline integration](references/mcp-pipeline-integration.md) for details.

## MCP Tool Design Patterns

### Dry-Run Default for Destructive Operations

When a tool performs batch deletes, mass approvals, or other irreversible actions, default to preview mode. User must explicitly opt in to execute.

```python
Tool(
    name="approve_all_diffs",
    description="批量审核通过所有 diff。dry_run=true 时只预览不执行。",
    inputSchema={
        "type": "object",
        "properties": {
            "dry_run": {"type": "boolean", "description": "true=仅预览，不实际操作（默认 true）"}
        },
    },
)

# In handler:
def call_tool(name, arguments):
    dry_run = arguments.get("dry_run", True)  # default True!
    if dry_run:
        return _result(preview_text + "\n\n[Dry Run] 以上为预览，未实际操作。传入 dry_run=false 执行。")
    # ... execute actual operation
```

**Why**: MCP tools are called by LLMs which may misunderstand intent. A batch delete triggered by accident is unrecoverable. The dry_run default creates a safe preview → confirm workflow.

### Fuzzy Match Suggestions on File Not Found

When a tool accepts a file path and the file doesn't exist, search for similar files and suggest alternatives instead of just returning "not found".

```python
def call_tool(name, arguments):
    if name == "read_wiki_page":
        file_path = arguments.get("file_path", "")
        full_path = WIKI_DIR / file_path
        if not full_path.exists():
            matches = list(WIKI_DIR.rglob(f"*{file_path}*"))
            if matches:
                suggestions = "\n".join(f"  - {m.relative_to(WIKI_DIR)}" for m in matches[:5])
                return _result(f"错误: 文件不存在 — {file_path}\n\n你是否要找:\n{suggestions}")
            return _result(f"错误: 文件不存在 — {file_path}")
```

**Why**: LLMs often guess filenames slightly wrong (e.g., `docker-network.md` vs `docker-容器网络.md`). Fuzzy suggestions let the LLM self-correct in the next call without user intervention.

### Output Cap for Search/Query Results

When a tool returns a variable number of results, cap the output and indicate truncation:

```python
if len(matches) > 50:
    shown = "\n".join(matches[:50])
    return _result(header + shown + f"\n\n... 共 {len(matches)} 条，仅显示前 50 条")
return _result(header + "\n".join(matches))
```

**Why**: MCP clients (especially IDE integrations) have limited display capacity. Unbounded output floods the context window and degrades the LLM's ability to process results.

### Complete Audit Loop Pattern

When building a review/approval workflow, provide three distinct tool stages:

```
list (overview) → read/inspect (detail) → approve/reject (action)
```

Do NOT combine list + content into one tool — the list tool should be lightweight (filenames + metadata only) so the LLM can decide which items to inspect. The read tool returns full content. The action tool mutates state.

```
review_diffs  →  read_diff  →  approve_diff / reject_diff
(list names)     (show content)  (decide and act)
```

**Why**: Combining list + content in one tool produces massive output when there are many items. Separating them lets the LLM selectively inspect only the items it needs to review, keeping context usage efficient.

### Tool Categorization for Large MCP Servers

When an MCP server has 10+ tools, organize them into logical categories in documentation. This improves discoverability for both LLMs and human users.

**Pattern**: Group tools by workflow stage or domain:

```
### 摄入 (Ingestion)
| ingest_file | file_path: str | ... |
| ingest_all | 无 | ... |
| list_raw_files | 无 | ... |

### 审核 (Review)
| review_diffs | 无 | ... |
| read_diff | diff_filename: str | ... |
| approve_diff | diff_filename: str | ... |

### 查询 (Query)
| ask_wiki | question: str | ... |
| search_wiki | query: str | ... |

### 运维 (Ops)
| build_index | 无 | ... |
| check_health | 无 | ... |
```

**Why**: LLMs calling MCP tools scan descriptions to pick the right tool. Categories create a mental model that speeds up selection. Without categories, a flat list of 14 tools overwhelms the context window.

**Rule of thumb**: If you have 8+ tools, categorize. If you have 4-7, a single table is fine.

### Documentation Accuracy: Phase/Stage Labels

When documentation marks a feature as "Phase N" or "阶段 N", verify the implementation status before writing new docs or updating existing ones.

**Pitfall**: Marking an already-implemented feature as "Phase 3 (planned)" in README.md confuses users and makes the project look incomplete.

**Check before using phase labels**:
```bash
# Verify feature is actually implemented
grep -r "feature_keyword" src/ --include="*.py"
# Check if data/config exists
ls -la var/feature_data/
# Test the feature
docker exec container python3 -c "import module; module.test()"
```

**Rule**: If the code exists and works, remove the phase label. Phase labels are for planned features only.

## MCP Server Troubleshooting

### Pitfall: Do NOT Call MCP Tools When Diagnosing Performance Issues

When a user reports MCP server slowness or timeouts, **do NOT call the MCP tools** to diagnose — this adds load to the already-struggling service and can make things worse.

### Pitfall: Do NOT Blame LLM Latency When the Real Problem Is Connection Stability

When MCP calls show mixed patterns of slow responses AND connection failures, **do NOT immediately attribute all delays to LLM inference speed**. Check connection stability first.

**Diagnostic red flags that indicate CONNECTION issues, not LLM latency**:
- `0.0s [MCP server 'XXX' is not connected]` — instant failure = no connection, not slow LLM
- `BrokenResourceError` — SSE stream broke mid-connection
- Mix of normal (30-60s) and timeout (180s) responses — intermittent connection drops
- Container recently restarted (check `docker ps` uptime vs error timestamps)

**Correct diagnostic sequence**:
1. Check container uptime: `docker ps --filter "name=XXX" --format "{{.Status}}"`
2. Check restart count: `docker inspect XXX --format '{{.RestartCount}}'`
3. Check SSE endpoint: `curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/sse`
4. Check Docker events: `docker events --filter "container=XXX" --since "1h"`
5. THEN check LLM model speed if connection is stable

**Why this matters**: In corporate proxy environments, SSE long connections are prone to timeout/disconnect. The MCP client may not auto-reconnect, causing subsequent calls to fail instantly (0.0s). Blaming LLM latency leads to unnecessary model switching when the real fix is connection stability (heartbeat, reconnect logic).

**Correct diagnosis sequence** (infrastructure tools only):
1. `docker stats <container> --no-stream` — check CPU, memory, disk I/O
2. `docker logs <container> --tail 50 | grep -E "ERROR|WARN|timeout|slow"` — check for errors
3. Read container config (`.env`, environment vars) — check LLM model, timeout settings
4. `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:<port>/health` — verify HTTP responsiveness

**Root cause analysis for LLM-backed MCP tools**:
- MCP call → LLM inference → response = compounded latency
- Bottleneck is usually the LLM model speed, not the MCP server code
- Check: which LLM model is configured → compare expected vs actual response times
- Check: Hermes MCP timeout config in `~/.hermes/config.yaml` under `mcp_servers`

**Common slow-MCP root causes**:
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| All calls 30-60s | Slow LLM model (e.g. mimo-v2.5-pro) | Switch to faster model or optimize prompt |
| `0.0s [not connected]` | SSE connection lost (proxy timeout, container restart) | Check container uptime, add SSE heartbeat |
| `BrokenResourceError` | SSE stream broke mid-connection | Check proxy config, add reconnect logic |
| Intermittent 180s timeouts | Connection drops + LLM occasionally slow | Check connection stability first, then LLM speed |
| Consistent 0s responses | Service not ready | Wait for startup, check health endpoint |

### MCP Performance Tuning

When LLM-backed tools are slow, evaluate in this order:
1. **Model speed**: Fast models (deepseek-v4-flash) vs slow reasoning models (mimo-v2.5-pro)
2. **Prompt optimization**: Shorter prompts = faster LLM response
3. **Timeout alignment**: Ensure MCP client timeout > typical LLM response time + buffer
4. **Caching**: Cache frequent queries to avoid repeated LLM calls

### Structured Output Quality: Sanitize LLM-Generated Frontmatter

**Problem**: LLMs generating YAML frontmatter occasionally produce duplicate keys (`tags:` twice, `views:` twice). Downstream tools (Quartz, Hugo, Jekyll) crash on duplicate YAML keys.

**Root cause**: LLM follows a template but re-emits fields or appends extras — an output quality issue, not a template design problem.

**Solution**: Add a `_sanitize_frontmatter()` function that parses frontmatter, detects duplicate keys, removes all but the first occurrence, and is called **immediately before writing** the file:

```python
content = _sanitize_frontmatter(content)
target_file.write_text(content, encoding="utf-8")
```

**Integration**: Apply at EVERY write path — `approve_diff` (single), `approve_all_diffs` (batch), and any other tool that writes LLM-generated content to disk.

**See `references/frontmatter-quality-validation.md`** for full implementation, test cases, and integration patterns.

### Static Site Generator Compatibility

When an MCP server generates wiki pages consumed by a static site generator (Quartz, Hugo, Jekyll, MkDocs), frontmatter quality is critical:

| Issue | Symptom | Prevention |
|-------|---------|------------|
| Duplicate YAML keys | `ERROR: duplicated mapping key` → container crash | `_sanitize_frontmatter()` before write |
| Invalid date format | Build warning or silent skip | Enforce ISO 8601 in template |
| Missing required fields | Visual glitch or broken navigation | Lint after write, report errors |

**Quartz-specific**: Quartz v4.x does a full rebuild on file changes. A single bad frontmatter file kills the entire process. Always validate before the write reaches the watched directory.

## References
- [Frontmatter quality validation for LLM-generated content](references/frontmatter-quality-validation.md)
- [MCP tool consumer patterns (llm-wiki case study)](references/mcp-tool-consumer-patterns.md)
- [Complete MCP server skeleton](references/mcp-server-skeleton.py)
- [MiMo reasoning token budget pitfall](references/mimo-reasoning-tokens.md)
- [MCP + pipeline integration](references/mcp-pipeline-integration.md)
- [LLM-backed tool pattern](references/llm-backed-tool-pattern.md)
- [Vector retrieval + LLM synthesis pattern](references/vector-retrieval-pattern.md)
- [Auto-index on approve pattern](references/auto-index-on-approve.md)
- [Lint / quality check pipeline pattern](references/lint-quality-check-pattern.md)
- [ChromaDB in corporate proxy / SSL inspection](references/chromadb-corporate-proxy.md)
- [LLM-Wiki management (embedding fix, ingest optimization, quality tuning)](references/llm-wiki-management.md)
- [SSE connection stability in proxy environments](references/sse-connection-stability.md)
