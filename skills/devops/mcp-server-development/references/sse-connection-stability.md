# SSE Connection Stability in Proxy Environments

## Problem

SSE (Server-Sent Events) uses HTTP long-lived connections. In corporate proxy environments (especially with SSL inspection), these connections are prone to:

1. **Proxy timeout** — proxies close idle connections after N seconds
2. **Connection reset** — proxy restarts or network fluctuations break the stream
3. **No auto-reconnect** — MCP clients may not automatically reconnect after disconnect

## Symptoms

| Symptom | Meaning |
|---------|---------|
| `0.0s [MCP server 'XXX' is not connected]` | Client has no active SSE connection |
| `BrokenResourceError: BrokenR...` | SSE stream broke mid-connection |
| `TimeoutError: MCP call timed out` | Either LLM slow OR connection stalled |
| Mix of 30s normal + 180s timeout responses | Intermittent connection drops |

## Root Cause Analysis

```
MCP Client (Hermes)
  ↓ SSE long connection
Corporate Proxy (10.197.216.7:3128)
  ↓ may timeout/close
MCP Server (llm-wiki on localhost:18080)
```

The proxy doesn't understand SSE semantics — it sees an HTTP connection that never "completes" and may close it.

## Diagnostic Commands

```bash
# 1. Check container uptime (was it restarted?)
docker ps --filter "name=XXX" --format "{{.Names}} {{.Status}}"

# 2. Check restart count
docker inspect XXX --format '{{.RestartCount}}'

# 3. Check Docker events for restarts
docker events --filter "container=XXX" --since "6h" | grep -E "start|stop|die|kill"

# 4. Test SSE endpoint directly (will hang if working — that's expected)
timeout 5 curl -s http://localhost:<port>/sse | head -5

# 5. Check health endpoint (should return immediately)
curl -s -o /dev/null -w "HTTP: %{http_code} Time: %{time_total}s\n" http://localhost:<port>/health
```

## Solutions

### 1. SSE Heartbeat (Server-Side)

Add periodic heartbeat comments to the SSE stream to prevent proxy timeout:

```python
# In handle_sse, wrap with heartbeat
async def handle_sse(request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        heartbeat_task = asyncio.create_task(
            _send_heartbeat(request._send, interval=30)
        )
        try:
            await server.run(streams[0], streams[1], server.create_initialization_options())
        finally:
            heartbeat_task.cancel()
    return Response()

async def _send_heartbeat(send, interval=30):
    """Send SSE comment as keepalive every N seconds."""
    try:
        while True:
            await asyncio.sleep(interval)
            await send({"type": "http.response.body", "body": b": heartbeat\n\n", "more_body": True})
    except asyncio.CancelledError:
        pass
```

**Note**: SSE comments (lines starting with `:`) are ignored by compliant SSE clients but keep the TCP connection alive through proxies.

### 2. MCP Client Reconnect (Hermes Config)

Check `~/.hermes/config.yaml` for reconnect settings:

```yaml
mcp_servers:
  LLM-WIKI:
    url: http://localhost:18080/sse
    transport: sse
    timeout: 180
    connect_timeout: 10
```

If reconnect is not automatic, the user must start a new Hermes session after connection loss.

### 3. Local Bypass (Best for WSL)

Since the MCP server runs on localhost, bypass the proxy entirely:

```bash
# In .env or config
NO_PROXY=localhost,127.0.0.1,::1
no_proxy=localhost,127.0.0.1,::1
```

This ensures SSE connections to localhost don't go through the corporate proxy.

## Three-Person Group Discussion Methodology

When diagnosing complex performance issues, use the "三人小组讨论" (Three-Person Group Discussion) methodology:

1. **优化派 (Optimizer)** — Focus on immediate fixes, model switching, prompt optimization
2. **架构派 (Architect)** — Focus on structural solutions, caching, async, streaming
3. **务实派 (Pragmatist)** — Evaluate ROI, usage frequency, whether optimization is needed at all

Each agent analyzes independently, then synthesize consensus. This prevents tunnel vision (e.g., blaming LLM latency when the real issue is connection stability).

## Key Lesson

**Always distinguish between "slow response" and "no connection"**:
- Slow response (27-60s) = LLM inference latency
- No connection (0.0s failure) = SSE stream disconnected
- Timeout (180s) = ambiguous — could be either

When patterns mix, check connection stability FIRST before blaming LLM speed.
