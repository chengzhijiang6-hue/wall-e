# Mem0 Self-Hosted Deployment Reference

Deployment walkthrough and pitfalls discovered during Mem0 (mem0ai/mem0) self-hosted setup on WSL2 + Docker + corporate proxy.

## Architecture

```
Docker Compose (3 containers):
  mem0 (FastAPI)  →  PostgreSQL (pgvector)  →  mem0-dashboard (Next.js)
  port 59110         port 59102                 port 59101
```

## Critical Pitfalls

### 1. pgvector dimension mismatch
**Error**: `psycopg.errors.DataException: expected 1536 dimensions, not 1024`
**Cause**: Default vector store uses 1536 dims (OpenAI text-embedding-3-small). DashScope text-embedding-v3 returns 1024 dims.
**Fix**: Configure BOTH:
```json
{
  "vector_store": {"provider": "pgvector", "config": {"embedding_model_dims": 1024}},
  "embedder": {"provider": "openai", "config": {"embedding_dims": 1024, "openai_base_url": "..."}}
}
```
If table already exists with wrong dims: `DROP TABLE memories;` then reconfigure.

### 2. OpenAI-compatible base_url parameter name
**Error**: `TypeError: BaseEmbedderConfig.__init__() got an unexpected keyword argument 'base_url'`
**Cause**: Mem0 uses `openai_base_url` (not `base_url`) for OpenAI-compatible providers.
**Fix**: Use `openai_base_url` in both LLM and embedder config.

### 3. Embedder bundled providers
**Error**: `Embedder provider 'xxx' is not bundled in this image`
**Cause**: Server only bundles openai + gemini for embedders.
**Fix**: To add other providers (e.g. ollama), edit `server/main.py`:
```python
BUNDLED_EMBEDDER_PROVIDERS = ("openai", "gemini", "ollama")
```
Then rebuild: `docker compose build mem0`

### 4. Dashboard Dockerfile: Node version
**Error**: `ERR_UNKNOWN_BUILTIN_MODULE: No such built-in module: node:sqlite`
**Cause**: pnpm 11.x requires Node 22+, but dashboard Dockerfile uses node:20-alpine.
**Fix**: Change to `node:22-alpine` and pin pnpm to v10: `npm install -g pnpm@10`

### 5. Auth: X-API-Key vs Bearer token
- `Authorization: Bearer <JWT>` — from `/auth/login`, expires
- `X-API-Key: <ADMIN_API_KEY>` — from `.env`, never expires
- For service-to-service (MCP server), always use `X-API-Key`

### 6. Search API filter format
**Error**: `Top-level entity parameters frozenset({'user_id'}) are not supported in search()`
**Fix**: Use `{"query": "...", "filters": {"user_id": "..."}}` not `{"query": "...", "user_id": "..."}`

### 7. Port 59100 stuck in Docker
**Symptom**: `ss` shows port free but Docker says "address already in use"
**Fix**: Use a different port. Docker's port allocation can get stuck after failed container starts.

## Environment Variables (.env)
```env
OPENAI_API_KEY=<dashscope-key>
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
JWT_SECRET=<random-48-chars>
ADMIN_API_KEY=<your-admin-key>
AUTH_DISABLED=false
MEM0_DEFAULT_LLM_MODEL=qwen-plus
MEM0_DEFAULT_EMBEDDER_MODEL=text-embedding-v3
MEM0_TELEMETRY=false
```

## Verify
```bash
curl --noproxy localhost -s http://localhost:59110/auth/setup-status
curl --noproxy localhost -s http://localhost:59101/api/health
docker exec mem0-dev-postgres-1 pg_isready -U postgres
```
