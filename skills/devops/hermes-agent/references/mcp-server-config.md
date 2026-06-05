# MCP Server Configuration Reference

## Config Location
`~/.hermes/config.yaml` under `mcp_servers` key.

## Transport Types

| Transport | When to use | Required fields |
|-----------|-------------|-----------------|
| `sse` | MCP server exposes `/sse` endpoint | `url`, `transport: sse` |
| `streamable_http` | MCP server exposes `/mcp` endpoint (default) | `url` |
| `stdio` | Local process, spawned by Hermes | `command`, `args` |

## Real-World Examples

### LLM-WIKI (SSE, local container)
```yaml
mcp_servers:
  LLM-WIKI:
    url: "http://localhost:18080/sse"
    transport: sse
    timeout: 180
    connect_timeout: 10
```
- Container: `llm-wiki` on port 18080
- 14 MCP tools available
- Related: LLM Wiki project at `~/llm-wiki/`

## Config Key Naming Convention

| Source | Key format | Notes |
|--------|-----------|-------|
| Hermes Agent | `mcp_servers` | snake_case |
| VS Code / Cursor | `mcpServers` | camelCase |
| Claude Desktop | `mcpServers` | camelCase |

User may share config in camelCase from other tools — always convert to `mcp_servers` for Hermes.

## Prerequisites

The `mcp` Python package **must** be installed in Hermes's venv. Without it, the MCP client module is a silent no-op — all MCP servers show as "failed" with no error message.

```bash
# Check if installed
/mnt/c/wsl/hermes_official/venv/bin/pip show mcp

# Install if missing
/mnt/c/wsl/hermes_official/venv/bin/pip install mcp
```

Both the LLM-WIKI server container and Hermes client need matching `mcp` SDK versions (currently 1.27.1).

## Verification

After adding MCP config:
1. CLI: run `/reload-mcp` or start new session
2. WebUI: start new conversation (no hot-reload)
3. Check tools loaded: agent should be able to call MCP tools automatically

To test SSE endpoint (will hang — SSE is long-lived):
```bash
# Don't curl SSE directly — it hangs. Check container instead:
docker ps --filter "name=<container>" --format "{{.Names}} {{.Status}}"
curl -s --noproxy localhost -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:<port>/
# 404 = server reachable (root path has no handler, normal)
```

## SSE Connection Drop Troubleshooting

### Symptom: "MCP server 'X' is not connected" with 0.0s response

When MCP tool calls return instantly (0.0s) with "MCP server is not connected", this is a **connection issue**, NOT a performance or LLM issue. Do NOT blame the LLM model speed.

### Misdiagnosis Pattern (AVOID)

```
❌ Wrong: "LLM response is slow, causing timeouts"
✅ Right: "SSE connection dropped, client not reconnected"
```

Evidence that it's a connection issue (not LLM):
- 0.0s response time = no request was even sent
- "not connected" message = client lost the SSE stream
- BrokenResourceError = TCP connection severed

### Diagnostic Sequence

```bash
# 1. Check container status and uptime
docker ps --filter "name=<container>" --format "{{.Names}} {{.Status}}"

# 2. Check restart count (0 = no auto-restarts)
docker inspect <container> --format '{{.RestartCount}}'

# 3. Check Docker events for recent restarts
docker events --filter "container=<container>" --since "1h" | grep -E "start|stop|die"

# 4. Check container logs for errors
docker logs <container> --tail 50 2>&1 | grep -E "ERROR|WARN|timeout|crash"

# 5. Verify SSE endpoint responds
timeout 5 curl -s http://localhost:<port>/sse 2>&1 | head -3
```

### Common Causes

| Cause | Evidence | Fix |
|-------|----------|-----|
| Container restart | RestartCount > 0, Docker events show start/stop | Wait for auto-reconnect or restart Hermes session |
| SSE connection timeout | No restart, but long idle period | SSE lacks heartbeat; proxy may drop idle connections |
| Proxy environment drops | Corporate proxy (SSL inspection) | Add `NO_PROXY=localhost,127.0.0.1` to container env |
| Network flap | Intermittent, no pattern | Hermes MCP client should auto-reconnect on next call |

### Key Insight: Container "Up X minutes" Can Be Misleading

Docker's status display may show "Up 3 minutes" even if the container has been running for hours — this is a status refresh artifact, not proof of restart. Always check `RestartCount` and `State.StartedAt` for accurate uptime:

```bash
docker inspect <container> --format 'Started: {{.State.StartedAt}} Restarts: {{.RestartCount}}'
```

### Resolution

SSE connection drops are transient. The Hermes MCP client auto-reconnects on the next tool call. If repeated drops occur:
1. Check proxy configuration (NO_PROXY for localhost)
2. Consider increasing `timeout` in MCP server config
3. Check if container has memory pressure (`docker stats`)
