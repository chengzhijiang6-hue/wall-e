# OpenClaw Docker Deployment — Full Workflow

## Environment
- **Host:** WSL2 Ubuntu 24.04 on Windows
- **Docker:** v29.1.3, Compose v2.26.1, BuildKit v0.26.2
- **Network:** Corporate proxy at `http://10.197.216.7:3128` (HTTPS inspection)
- **Project location:** `/mnt/c/wsl/openclaw/`

## Phase 1: Pre-build Checks

### Docker Availability
```bash
docker --version          # v29.1.3
docker compose version    # v2.26.1
docker info               # check daemon proxy, storage, resources
```

### Network Connectivity
```bash
# Test proxy-forwarded access to build-critical hosts
curl -sI --max-time 10 https://registry.npmjs.org/   # npm registry
curl -sI --max-time 10 https://github.com             # GitHub
curl -sI --max-time 10 https://bun.sh                 # Bun installer
```

### Daemon Proxy Configuration Check
```bash
cat /etc/docker/daemon.json         # proxies section -> runtime containers
cat /etc/systemd/system/docker.service.d/http-proxy.conf  # daemon itself
```
**Key insight:** Daemon proxy applies to container runtime AND image pulls, but NOT to `docker build` RUN commands. Build containers need explicit `--build-arg`.

## Phase 2: Docker Build

### Command (with corporate proxy)
```bash
DOCKER_BUILDKIT=1 docker build \
  --build-arg HTTP_PROXY="http://proxy:3128" \
  --build-arg HTTPS_PROXY="http://proxy:3128" \
  --build-arg http_proxy="http://proxy:3128" \
  --build-arg https_proxy="http://proxy:3128" \
  --build-arg NO_PROXY="localhost,127.0.0.1,::1" \
  --build-arg no_proxy="localhost,127.0.0.1,::1" \
  --progress=plain \
  -t openclaw:local \
  -f Dockerfile \
  . > /tmp/docker_build.log 2>&1
```

### Build Steps (OpenClaw-specific, ~43 total)
| Step | Description | Typical Time |
|------|-------------|-------------|
| Context transfer | ~104MB source to Docker daemon | 2-3 min |
| System deps | apt-get upgrade + install | 1 min |
| Bun install | curl https://bun.sh/install | 15 s |
| pnpm install | 1300+ packages | 2 min |
| pnpm build:docker | TypeScript compilation | 2 min |
| UI install | pnpm ui:install | 2 min |
| Bundled plugins | postinstall (AWS/Azure/OTel etc.) | 4 min |
| Image export | layers+manifest+naming | 1.5 min |

**Total:** ~13 minutes through corporate proxy

### Progress Monitoring
```bash
wc -l /tmp/docker_build.log
tail -5 /tmp/docker_build.log
grep "transferring context:" /tmp/docker_build.log | tail -1
grep "Progress:" /tmp/docker_build.log | tail -1
grep -i "ERROR:" /tmp/docker_build.log
```

## Phase 3: Docker Compose Service

### docker-compose.yml (clean)
```yaml
version: '3.8'
services:
  openclaw-gateway:
    image: openclaw:local
    container_name: openclaw-gateway
    restart: unless-stopped
    ports:
      - "18789:18789"
    env_file:
      - .env
    volumes:
      - ./.openclaw:/home/node/.openclaw
      - ./config:/app/config
      - ./workspace:/app/workspace
```

### .env
```
OPENCLAW_GATEWAY_TOKEN=<token>
DEEPSEEK_API_KEY=sk-...
GOOGLE_API_KEY=AIzaSy...
OPENAI_BASE_URL=https://api.deepseek.com/v1
NODE_TLS_REJECT_UNAUTHORIZED=0
NO_PROXY=localhost,127.0.0.1,::1
```

### env_file Pitfall (CRITICAL)
`docker compose restart` does **NOT** re-read `env_file`. Environment variables are injected at container creation time only. If you modify `.env`, you must recreate the container:
```bash
# WRONG — doesn't pick up new .env:
docker compose restart openclaw-gateway

# CORRECT — recreates with fresh env:
docker compose down && docker compose up -d
```
Verify env vars are actually loaded inside the container:
```bash
docker exec openclaw-gateway printenv | grep KEY_NAME
```

## Phase 4: Gateway Configuration

### Step 1: Fix openclaw.json format
Old (rejected): `{"gateway": {"defaultProvider":"google","defaultModel":"gemini-1.5-pro"}}`
New: `{"gateway": {"mode":"local","bind":"lan","port":18789}}`

### Step 2: Add API keys to auth-profiles.json
```json
{
  "deepseek": { "apiKey": "sk-..." },
  "google": { "apiKey": "AIzaSy..." }
}
```
**Note:** For OpenAI-compatible providers (like DeepSeek), you do NOT need auth-profiles.json entries. The built-in `openai` provider reads `OPENAI_API_KEY` and `OPENAI_BASE_URL` from environment variables. The auth-profiles.json entry is optional — the env vars take precedence.

### Step 3: Configure agent.json
```json
{
  "id": "main",
  "name": "DeepSeek V4 Flash",
  "provider": "deepseek",
  "model": "deepseek-v4-flash",
  "active": true
}
```
**Note:** This file sets the agent's desired provider/model, but the gateway does NOT read it at startup to determine the default model. It reads `agents.defaults.model` from the gateway config (set via CLI — see Step 5).

### Step 4: Add provider to models.json
Add an OpenAI-compatible provider entry:
```json
{
  "providers": {
    "deepseek": {
      "baseUrl": "https://api.deepseek.com/v1",
      "apiKey": "sk-...",
      "auth": "apiKey",
      "api": "openai",
      "models": [
        {
          "id": "deepseek-v4-flash",
          "name": "DeepSeek V4 Flash",
          "api": "openai",
          "reasoning": false,
          "input": ["text"],
          "contextWindow": 128000,
          "maxTokens": 16384,
          "compat": { "supportsUsageInStreaming": true }
        }
      ]
    }
  }
}
```

### Step 5: Set gateway defaults via CLI (MUST DO)
The gateway ignores `agent.json` for default model selection. Always set via CLI:
```bash
docker exec openclaw-gateway node dist/index.js config set agents.defaults.model "deepseek/deepseek-v4-flash"
docker exec openclaw-gateway node dist/index.js config get agents.defaults
```
**Model naming convention:** `provider/model-id`. The `/` separator tells the gateway which provider to use. For built-in providers, use the provider's short name (e.g., `openai`, `anthropic`, `google`). The provider segment must match a registered provider.

### Step 6: Restart and verify
```bash
docker compose down && docker compose up -d
sleep 12
docker logs openclaw-gateway 2>&1 | grep "agent model"
# Expected: agent model: deepseek/deepseek-v4-flash
```

## Phase 5: Health Verification
```bash
docker ps --filter name=openclaw-gateway
curl --noproxy "*" -sS http://127.0.0.1:18789/healthz
# Expected: {"ok":true,"status":"live"}
```

## Phase 6: Browser Access
Open `http://127.0.0.1:18789/` in a browser. In Control UI Settings, enter the gateway token (`OPENCLAW_GATEWAY_TOKEN` from `.env`) to pair.

## Pitfalls
1. **Build context large (~104MB)** over proxy is slow. Set timeout >=10 min.
2. **pnpm through proxy:** some packages at ~10 KiB/s. UI deps are slowest.
3. **postinstall runs silent** for 1-4 min. Use `ps aux | grep postinstall` to check.
4. **Gateway ignores agent.json model** — always set `agents.defaults.model` via CLI.
5. **Old config keys rejected:** `defaultProvider`, `defaultModel`, `providers` array cause startup errors.
6. **Port conflict:** `docker rm -f openclaw-gateway` before `docker compose up -d`.
7. **env_file changes ignored by restart:** Always use `down && up` to pick up new environment variables.
8. **Control UI pairing:** Browser connects via WebSocket. First connection shows `token_missing` in logs until you enter the token in Settings.
