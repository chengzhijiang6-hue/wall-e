# Mem0 Self-Hosted Deployment

## Overview
Mem0 is an open-source memory layer for AI agents (56k+ GitHub stars). Self-hosted version uses PostgreSQL + pgvector for vector storage.

## Architecture
- **API Server**: FastAPI (Python 3.12), port 8000 internal
- **Dashboard**: Next.js (Node 22), port 3000 internal
- **Database**: PostgreSQL with pgvector extension
- **Auth**: JWT-based, enabled by default

## Port Assignments (Ethan's Setup)
| Service    | Host Port | Container Port |
|------------|-----------|----------------|
| API        | 59110     | 8000           |
| Dashboard  | 59101     | 3000           |
| PostgreSQL | 59102     | 5432           |
| ~~Ollama~~    | ~~59143~~ | ~~11434~~      | *已从 compose 移除*
| ~~Embed-srv~~ | ~~59144~~ | ~~8001~~       | *已从 compose 移除*

## Key Files
- `/mnt/c/wsl/mem0/server/docker-compose.yaml` — main compose file (NOTE: in `server/` subdir, NOT project root)
- `/mnt/c/wsl/mem0/server/.env` — configuration
- `/mnt/c/wsl/mem0/server/dev.Dockerfile` — API server image
- `/mnt/c/wsl/mem0/server/dashboard/Dockerfile` — dashboard image

## LLM/Embedder Configuration

### Configuring DashScope (OpenAI-Compatible) as Provider

The bundled providers are: LLM (openai, anthropic, gemini), Embedder (openai, gemini).

To use DashScope Qwen as the "openai" provider, call the `/configure` API:

```bash
TOKEN=$(curl -s -X POST http://localhost:59110/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Mem0Admin2026!"}' \
  | grep -oP '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -s -X POST http://localhost:59110/configure \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "llm": {
      "provider": "openai",
      "config": {
        "api_key": "<DASHSCOPE_API_KEY>",
        "model": "qwen-plus",
        "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
      }
    },
    "embedder": {
      "provider": "openai",
      "config": {
        "api_key": "<DASHSCOPE_API_KEY>",
        "model": "text-embedding-v3",
        "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
      }
    }
  }'
```

### CRITICAL: Parameter Name

Mem0's OpenAI embedder uses `openai_base_url` — NOT `base_url`.

Passing `base_url` in the embedder config causes:
```
TypeError: BaseEmbedderConfig.__init__() got an unexpected keyword argument 'base_url'
```

The LLM also uses `openai_base_url` (reads from config or `OPENAI_BASE_URL` env var).

### CRITICAL: Embedding Dimension Must Match pgvector Schema

When switching embedding providers (e.g. OpenAI text-embedding-ada-002 → DashScope text-embedding-v3), the **vector dimension changes**:
- OpenAI ada-002 / text-embedding-3-small: **1536** dimensions
- DashScope text-embedding-v3: **1024** dimensions

The pgvector column dimension is **baked into the table schema at creation time**. Switching models without updating the table causes:
```
psycopg.errors.DataException: expected 1536 dimensions, not 1024
```
Every memory insert silently fails after this.

**Fix**: Drop the old table and let alembic recreate with correct dimensions:
```bash
# Enter postgres container
docker exec -it mem0-dev-postgres-1 psql -U postgres -d mem0_app

-- Drop old table (loses all stored memories)
DROP TABLE IF EXISTS memories;
DROP TABLE IF EXISTS alembic_version;
\q

# Restart mem0 to trigger alembic migration
docker restart mem0-dev-mem0-1
```

**Check current dimension**:
```sql
SELECT attname, atttypmod FROM pg_attribute
WHERE attrelid = 'memories'::regclass AND attname = 'vector';
-- atttypmod = dimension + 4 (e.g. 1028 → 1024 dimensions)
```

## Pitfalls Encountered

1. **Port 59100 stuck**: Docker NAT rules held port despite `ss` showing free. Fixed by using 59110.
2. **Volume `.:/app`**: Overrides packages installed during build. Removed the mount.
3. **Runtime pip install**: Compose command had `pip install --force-reinstall` which fails behind proxy. Removed it.
4. **Node 20 + pnpm 11**: `node:sqlite` module missing. Upgraded to `node:22-alpine`.
5. **`base_url` vs `openai_base_url`**: Embedder config parameter name mismatch.
6. **pgvector dimension mismatch**: Switching embedding models (OpenAI 1536d → DashScope 1024d) without recreating the table causes all inserts to fail silently with `expected 1536 dimensions, not 1024`.
7. **Compose blocks on large-image download**: ollama image is 3.8GB; `docker compose up -d` blocks ALL services until download completes. Use selective startup: `docker compose up -d postgres mem0 mem0-dashboard`.

## Database Layout Detail

- `memories` table (vector store) lives in the **`postgres`** database (default DB)
- `mem0_app` database contains: `users`, `api_keys`, `settings`, `request_logs`, `refresh_token_jtis`, `alembic_version`
- When debugging vector issues, connect to the correct DB: `psql -U postgres -d postgres`

## Dashboard Healthcheck False Negative

The compose healthcheck uses `wget -qO- http://localhost:3000/api/health` but this endpoint may not exist in all dashboard builds. The dashboard is actually functional (serves login page at `/`). If `docker compose ps` shows `unhealthy` for dashboard but it responds on port 59101, the healthcheck config is the issue — not the service.

## Auth Login Field Name

The `/auth/login` endpoint expects `email` (not `username`):
```json
{"email": "admin@example.com", "password": "Mem0Admin2026!"}
```

## Removed Services

Ollama and embed-server were removed from `docker-compose.yaml` (2026-05-21) because:
- **Ollama**: 3.8GB image download blocked all other services from starting. Not needed when using cloud DashScope API.
- **Embed-server**: Local sentence-transformers (all-MiniLM-L6-v2, 384d) conflicts with DashScope text-embedding-v3 (1024d). Not needed when using cloud embeddings.

If local LLM/embedding is needed in the future, re-add these services to docker-compose.yaml.

## Startup Failure Diagnostic Flow

```
docker compose ps -a
  ├─ All Exited? → Check logs for dependency failures
  │   └─ (ollama/embed-server removed, no longer a download-block risk)
  ├─ mem0 exited (255)? → docker compose logs mem0 --tail=50
  │   ├─ "expected N dimensions, not M" → pgvector dimension mismatch, see above
  │   └─ "connection refused" → postgres not healthy yet, check depends_on
  └─ postgres exited? → docker compose logs postgres --tail=20
      └─ Usually clean shutdown (Docker/WSL restart), just restart
```

## Useful Commands

```bash
# Check service status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep mem0

# View API logs
docker logs mem0-dev-mem0-1 --tail 20

# Restart API
docker restart mem0-dev-mem0-1

# Clear config overrides (reset to defaults)
docker exec mem0-dev-postgres-1 psql -U postgres -d mem0_app -c "DELETE FROM settings;"

# Full restart
cd /mnt/c/wsl/mem0/server && docker compose restart

# Full restart (ollama/embed-server removed, safe to up all)
cd /mnt/c/wsl/mem0/server && docker compose up -d
```

## Embedding Provider Limitation (CRITICAL)

Mem0 server's bundled embedder providers are **only `openai` and `gemini`** (defined in `server/main.py` as `BUNDLED_EMBEDDER_PROVIDERS`). The `/configure` endpoint rejects any other embedder provider with a 400 error.

### Provider Compatibility Matrix

| Provider | LLM Support | Embedding Support | Notes |
|----------|------------|-------------------|-------|
| DashScope (Qwen) | ✅ OpenAI-compatible | ✅ text-embedding-v3 | Account must be in good standing (Arrearage = all models blocked) |
| Xiaomi MIMO | ✅ OpenAI-compatible | ❌ No embeddings endpoint | Returns 404 on /v1/embeddings |
| DeepSeek | ✅ OpenAI-compatible | ❌ No public embedding model | Returns 404 |
| Ollama (local) | ✅ (add to BUNDLED_LLM_PROVIDERS) | ✅ (add to BUNDLED_EMBEDDER_PROVIDERS) | Requires Docker image (~3.8GB) + model pull |

### Adding Ollama as Embedder Provider

1. Add `ollama` to `BUNDLED_EMBEDDER_PROVIDERS` in `server/main.py`:
   ```python
   BUNDLED_EMBEDDER_PROVIDERS = ("openai", "gemini", "ollama")
   ```
2. Add `ollama` to `server/requirements.txt`
3. Rebuild: `docker compose build mem0`
4. Add Ollama container to `docker-compose.yaml`
5. Pull embedding model: `docker exec ollama-container ollama pull nomic-embed-text`

### Adding Any Custom Provider

Same pattern: edit `BUNDLED_*_PROVIDERS` in `server/main.py`, add Python package to `requirements.txt`, rebuild image. See [Mem0 docs: Supported Providers](https://docs.mem0.ai/open-source/setup#supported-providers).

### DashScope Arrearage Error

When DashScope account is overdue, ALL models (LLM + embedding) return:
```json
{"error": {"type": "Arrearage", "code": "Arrearage"}}
```
HTTP 400. This is account-level, not model-level. Recharge at Aliyun console to restore.

## Admin Credentials
- Email: admin@example.com
- Password: Mem0Admin2026!
