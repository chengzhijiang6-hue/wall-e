---
name: mem0-self-hosted
description: Self-hosted Mem0 memory service management — Docker Compose lifecycle, dimension mismatch diagnosis, MCP Server integration with Hermes, and troubleshooting.
version: 1.0.0
category: devops
triggers:
  - user asks about mem0 service status, startup, or troubleshooting
  - user asks about mem0 MCP server not loading tools
  - user asks about mem0 embedding dimension mismatch
  - user mentions mem0 docker compose issues
  - user asks to configure mem0 as Hermes long-term memory
---

# Mem0 Self-Hosted Management

Manage the self-hosted Mem0 memory service — a persistent, semantic memory layer for AI agents. Deployed via Docker Compose (PostgreSQL/pgvector + FastAPI API + Dashboard), integrated with Hermes Agent via MCP Server.

## Architectural Notes

### PostgreSQL 被多个服务共享

Mem0 的 PostgreSQL 实例（端口 59102）同时被 **multi-user-api**（WALL-E 管理面板，端口 59120）共享。这意味着：

- **不要单独删除或重建 Mem0 的 PostgreSQL**，除非确认没有其他服务在使用
- Multi-user-api 的 `.env` 中 `DB_PASSWORD` 必须与 Mem0 的 `POSTGRES_PASSWORD` 一致
- 两个服务使用**同一个 Postgres 实例但不同的数据库**（Mem0 用 `mem0_app`，multi-user-api 用 `postgres` 或 `multi_user`）

详见 [Multi-User Admin Panel Deployment](../docker-service-deployment/references/multi-user-admin-deployment.md)。

```
mem0/
├── server/
│   ├── docker-compose.yaml    # All services
│   ├── .env                   # Configuration
│   ├── main.py                # FastAPI API server
│   ├── embed-server/          # Optional local embedding server (NOT used)
│   └── dashboard/             # Next.js dashboard
├── mcp-server/
│   ├── mem0_mcp_server.py     # MCP bridge (SSE transport)
│   └── requirements.txt
```

## Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Mem0 API | 59110 | REST API (add/search/list/delete memories) |
| Dashboard | 59101 | Web UI (login: admin@example.com / Mem0Admin2026!) |
| PostgreSQL | 59102 | pgvector database |
| MCP Server | 59180 | Hermes MCP bridge (SSE at /sse) |

## Docker Compose — Minimal Configuration

The default docker-compose.yaml includes ollama and embed-server, which are **not needed** when using cloud LLM/embedding APIs (e.g. DashScope). Remove them to avoid slow startup from large image downloads.

**Services to keep:**
- `postgres` — pgvector database (required)
- `mem0` — FastAPI API server (required)
- `mem0-dashboard` — Web UI (optional but useful)

**Services to remove:**
- `ollama` — Local LLM inference engine. Only needed for offline/embedded LLM usage
- `embed-server` — Local embedding (all-MiniLM-L6-v2, 384d). Only needed for offline embedding

After removing ollama, also remove the `ollama_data` volume.

**Startup command (without ollama/embed-server):**
```bash
cd /mnt/c/wsl/mem0/server && docker compose up -d postgres mem0 mem0-dashboard
```

## Configuration (.env)

```env
# LLM: DashScope Qwen (OpenAI-compatible)
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# Models
MEM0_DEFAULT_LLM_MODEL=qwen-plus
MEM0_DEFAULT_EMBEDDER_MODEL=text-embedding-v3

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mem0_secure_2026

# Auth
JWT_SECRET=mem0-jwt-secret-xxx
ADMIN_API_KEY=mem0-admin-key-xxx
AUTH_DISABLED=false

# Proxy (for Docker build)
HTTP_PROXY=http://10.197.216.7:3128
HTTPS_PROXY=http://10.197.216.7:3128
NO_PROXY=localhost,127.0.0.1,::1,mem0,postgres,mem0-dashboard
```

## MCP Server Integration with Hermes

### Config (~/.hermes/config.yaml)

```yaml
mcp_servers:
  MEM0:
    url: http://localhost:59180/sse
    transport: sse
    timeout: 60
    connect_timeout: 10
```

### MCP Server Startup

The MCP server requires the **hermes venv Python** because system Python lacks the `mcp` package (see `mcp-server-development` skill for why).

**Manual start:**
```bash
cd /mnt/c/wsl/mem0/mcp-server && \
  MCP_PORT=59180 /mnt/c/wsl/hermes_official/venv/bin/python3 mem0_mcp_server.py
```

**Auto-start via systemd user service (recommended):**

WSL2 支持 systemd 用户服务，可以实现 MCP Server 开机自启。

```bash
# 创建服务文件
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/mem0-mcp.service << 'EOF'
[Unit]
Description=Mem0 MCP Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/mnt/c/wsl/mem0/mcp-server
ExecStart=/mnt/c/wsl/hermes_official/venv/bin/python3 mem0_mcp_server.py
Environment=MCP_PORT=59180
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

# 启用并启动
systemctl --user daemon-reload
systemctl --user enable mem0-mcp.service
systemctl --user start mem0-mcp.service
```

**管理命令:**
```bash
# 查看状态
systemctl --user status mem0-mcp.service

# 重启
systemctl --user restart mem0-mcp.service

# 停止
systemctl --user stop mem0-mcp.service

# 查看日志
journalctl --user -u mem0-mcp.service -f
```

**Pitfall:** 用户可能认为 WSL2 无法创建 systemd 服务（"宿主机无法创建system服务"），但实际上 systemd 用户服务在 WSL2 中正常工作。无需 root 权限，只需用户级 systemd 配置。

### MCP Tools

| Tool | Description |
|------|-------------|
| `mem0_add` | Add memory (auto-extracts facts from text) |
| `mem0_search` | Semantic search (vector-based, not keyword) |
| `mem0_list` | List all memories |
| `mem0_delete` | Delete a specific memory |

### Pitfall: MCP Tools Not Loading

MCP tools load at **session startup only** — there is no hot-reload. This is a general MCP limitation, not mem0-specific. See `mcp-server-development` skill for full details.

**If systemd auto-start is enabled:** MCP Server 应该已经在运行（端口 59180）。检查状态：
```bash
systemctl --user status mem0-mcp.service
curl -s -o /dev/null -w "%{http_code}" http://localhost:59180/health  # 应返回 200
```

**If MCP Server is not running:**
1. 启动 MCP server（见上方 MCP Server Startup 章节）
2. 告诉用户**启动新的 Hermes 会话**
3. Tools 会出现在下个会话的工具列表中

## Diagnosis: Embedding Dimension Mismatch

### Symptom
```
psycopg.errors.DataException: expected 1536 dimensions, not 1024
```

### Cause
The `memories` table was created with a different embedding model (e.g. OpenAI text-embedding-ada-002 = 1536d) but the current model (e.g. DashScope text-embedding-v3 = 1024d) outputs a different dimension.

### Diagnosis Steps
```bash
# Check current table dimensions
cd /mnt/c/wsl/mem0/server
docker compose exec postgres psql -U postgres -d postgres -c "\d memories"
# Look at the vector column: vector(1536) vs vector(1024)
```

### Fix
If the table has the wrong dimension, it must be recreated. This **destroys existing memories**:

```bash
# Drop and let alembic recreate on next restart
docker compose exec postgres psql -U postgres -d postgres -c "DROP TABLE memories;"
docker compose restart mem0
# alembic upgrade head will recreate with correct dimensions
```

## Pitfall: 不要过早判定产品"不存在"

在做 AI 工具/产品对比研究时，初次搜索失败不等于产品不存在。

**错误模式**: 搜索 `hindsight memory ai` 没找到主仓库 → 判定"Hindsight 不存在"

**正确搜索策略**:
1. GitHub API: 用 `sort=stars` 排序，主仓库通常 stars 最多
2. PyPI/npm: 搜索 `pip install <keyword>` 看有没有包
3. PyPI 包列表: `https://pypi.org/simple/` 搜索关键词，看整个生态
4. 多种关键词组合: `<name> memory agent`、`<name> semantic`、`<name>-client`

**教训来源**: Hindsight (vectorize-io/hindsight, 14k stars) 在初次调研中被错误排除。

## Diagnosis: Container Exit Codes

| Exit Code | Meaning | Common Cause |
|-----------|---------|--------------|
| 0 | Clean shutdown | Docker/WSL restart, manual `docker compose down` |
| 255 | Abnormal termination | Dependency failure (postgres down), OOM, signal kill |
| 1 | Application error | Python exception, missing env var, config error |

### When All Containers Are Exited
1. Check postgres first: `docker compose logs postgres --tail=20`
2. If postgres received "fast shutdown request" → Docker/WSL was restarted
3. Restart: `docker compose up -d postgres mem0 mem0-dashboard`

## Dashboard Health Check

**Resolved (2026-05-21):** The healthcheck uses BusyBox `wget` inside an Alpine container. BusyBox wget resolves `localhost` to IPv6 (`::1`) first, but Next.js only listens on IPv4 (`0.0.0.0:3000`), causing `Connection refused`. The `/api/health` endpoint DOES exist and returns `{"status":"ok"}`.

**Fix applied:** In `docker-compose.yaml`, healthcheck URL uses `127.0.0.1` instead of `localhost`:
```yaml
healthcheck:
  test: ["CMD", "wget", "-qO-", "http://127.0.0.1:3000/api/health"]
```

**Pitfall:** Alpine/BusyBox containers universally prefer IPv6 for `localhost`. Always use `127.0.0.1` in healthchecks for IPv4-only services.

## API Integration Pitfalls (Critical for Programmatic Access)

When integrating Mem0 API into other services (e.g., Multi-User Profile System):

### Pitfall: Authentication Header is `x-api-key`, NOT `Authorization: Bearer`

Mem0 self-hosted uses `x-api-key` header for authentication. Standard `Authorization: Bearer` returns 401.

```python
# ❌ Wrong — returns 401 "Invalid or expired token"
headers = {"Authorization": f"Bearer {api_key}"}

# ✅ Correct
headers = {"x-api-key": api_key}
```

The API key is `ADMIN_API_KEY` from Mem0's `.env`.

### Pitfall: Search API Requires `filters` Wrapper for `user_id`

Mem0 v3+ changed the search API. `user_id` is no longer a top-level parameter — it must be inside `filters`.

```python
# ❌ Wrong — returns 502 "Top-level entity parameters frozenset({'user_id'}) are not supported"
payload = {"query": "Docker", "user_id": "abc123"}

# ✅ Correct
payload = {"query": "Docker", "filters": {"user_id": "abc123"}}
```

**Note**: `POST /memories` (create) still accepts `user_id` as top-level. Only `/search` requires the `filters` wrapper.

### Pitfall: API Endpoints Have NO `/v1/` Prefix

Mem0 endpoints are at the root path, not under `/v1/`:

```
POST   /memories          — Create memories
POST   /search            — Search memories
GET    /memories           — List memories
DELETE /memories/{id}      — Delete memory
```

Not `/v1/memories`, `/v1/search`, etc.

### Pitfall: user_id Must Match Between Storage and Query (Critical)

当 Mem0 与多用户系统集成时，`user_id` 的一致性至关重要。存储和查询必须使用相同格式（推荐 username 而非 UUID）。详见 [Multi-User Mem0 Integration Pitfalls](references/multi-user-mem0-integration.md)。

### Pitfall: `AUTH_DISABLED=false` Means Authentication Required

When `AUTH_DISABLED=false` in Mem0's `.env`, all API calls must include the `x-api-key` header. Without it, returns 401.

## API Usage

### Login (get JWT token)
```bash
curl -s -X POST http://localhost:59110/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Mem0Admin2026!"}'
```

### Search memories
```bash
TOKEN=<jwt-from-login>
curl -s -X POST http://localhost:59110/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "test", "filters": {"AND": [{"user_id": "ethan"}]}}'
```

### Using ADMIN_API_KEY
The `ADMIN_API_KEY` from .env can be used directly as Bearer token for admin operations (bypasses JWT login).

## Reference Files

- **[Hindsight vs Mem0 对比](references/hindsight-vs-mem0.md)** — 两款 AI 记忆系统的详细对比，包括架构、API、适用场景、调研教训
- **[MCP Server ID Mismatch 分析](references/mcp-server-id-mismatch-analysis.md)** — mem0_delete 返回 502 的根因分析和解决方案（2026-06-04）

## Troubleshooting: MCP Tools Return "Connection refused"

When Hermes MCP tools for mem0 return `错误: [Errno 111] Connection refused`, the MCP server is running but **the backend Mem0 API Docker containers are stopped**.

**Diagnosis:**
```bash
# 1. Check MCP server health (usually still OK)
curl -s http://localhost:59180/health  # Returns {"status":"ok"}

# 2. Check Mem0 API health (will fail if containers are down)
curl -s http://localhost:59110/health  # Connection refused or empty

# 3. Check Docker container status
docker ps -a | grep mem0
# If all show "Exited" → containers need restart
```

**Root Cause Chain:**
```
Docker/WSL restart or system reboot
  → mem0 Docker containers enter Exited state
    → MCP Server still running (systemd user service) but backend API gone
      → MCP tools return "Connection refused"
```

**Fix:**
```bash
# 1. Start Docker containers (from the compose directory)
cd /mnt/c/wsl/mem0/server && docker compose up -d

# 2. Verify all containers are healthy
docker ps | grep mem0
# Expected: mem0-dev-postgres-1 (healthy), mem0-dev-mem0-1, mem0-dev-mem0-dashboard-1 (healthy)

# 3. Restart MCP server to re-establish connections
systemctl --user restart mem0-mcp.service

# 4. IMPORTANT: Start a NEW Hermes session
# MCP connections are established at session startup only
# The current session's connection is stale (ClosedResourceError)
```

**Pitfall:** Even after fixing Docker containers and restarting MCP server, the **current Hermes session** may still get `ClosedResourceError`. This is because the SSE connection was established at session start and cannot be hot-reloaded. The user must start a new session. Tell the user explicitly: "请开新会话后再试".

**Prevention:** Docker containers should use `restart: unless-stopped` policy to survive system reboots.

## Pitfall: mem0_delete Returns 502 — ID Mismatch Between List and Database

`mem0_list` 显示的记忆 ID 是**截断的前8字符**（如 `[2683daa9...]`），不是完整 UUID。但即使构造完整 UUID，`mem0_delete` 也可能返回 **502 Bad Gateway**（"Memory with id ... not found"）。

**错误模式**:
```
mem0_list → 显示 [2683daa9...]
→ 猜测完整ID为 2683daa9-98c7-4d7d-b798-04a53f1eb1e4
→ mem0_delete(id="2683daa9-98c7-4d7d-b798-04a53f1eb1e4")
→ 502 "Memory with id ... not found"
```

**根因分析（2026-06-04 确认）**:
MCP Server 的 `_list_memories` 函数调用 `/memories?entity_id=user_id&entity_type=user`，但 Mem0 API 的 `GET /memories` 端点**不支持 `entity_id` 参数**（只接受 `user_id`、`run_id`、`agent_id`）。FastAPI 忽略无效参数，导致返回**所有用户的记忆**而非特定用户的记忆。这些跨用户的 ID 在 delete 时无法找到，返回 502。

**永久修复（2026-06-04 已实施）**:

修改 `/mnt/c/wsl/mem0/mcp-server/mem0_mcp_server.py` 中的 `_list_memories` 函数：

```python
# ❌ 旧代码（错误参数）
r = _api_request("get", "/memories", params={"entity_id": user_id, "entity_type": "user"})

# ✅ 新代码（正确参数）
r = _api_request("get", "/memories", params={"user_id": user_id})
```

修复后：
- `mem0_list` 只返回指定用户的记忆（从 56 条降至 20 条）
- `mem0_delete` 对返回的 ID 正常工作
- 测试验证：add → delete → list 全流程通过

**重启 MCP Server 使修改生效**:
```bash
systemctl --user restart mem0-mcp.service
sleep 2 && curl -s http://localhost:59180/health
```

**验证方法**:
```bash
# 检查 Mem0 容器日志，确认 502 原因
docker logs mem0-dev-mem0-1 2>&1 | grep "DELETE" | tail -5
# 日志会显示: "ValueError: Memory with id {id} not found"
```

**如果修复后仍有问题**:
1. 通过 Mem0 Dashboard (http://localhost:59101) Web UI 手动删除
2. 用 `mem0_search` 搜索目标内容，搜索结果的 ID 可能是正确的
3. 通过 Docker 内 PostgreSQL 直接操作：
   ```bash
   docker compose exec postgres psql -U postgres -d postgres \
     -c "DELETE FROM memories WHERE memory LIKE '%目标内容%' AND user_id='ethan';"
   ```

**重要用户偏好**: 清理重复条目时，**必须先展示内容让用户决定**，不能自行删除。用户要求"以最新的时间戳版本为准"。

## Verification Checklist

After any mem0 operation:

- [ ] `docker compose ps` — all services running
- [ ] `curl http://localhost:59110/memories` — API responds (returns 200 or 401)
- [ ] `systemctl --user status mem0-mcp.service` — MCP server running (if auto-start enabled)
- [ ] `curl http://localhost:59180/health` — MCP server responds (returns 200)
- [ ] Dashboard loads at http://localhost:59101
- [ ] Test memory add/search via MCP tools in a new Hermes session

**Note**: Mem0 has NO `/health` endpoint. Use `/memories` (or `/openapi.json`) to verify API is responding. A 200 or 401/403 response means the service is up.
