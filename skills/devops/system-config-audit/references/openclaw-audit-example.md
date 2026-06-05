# OpenClaw Configuration Audit — Session Example

**Date:** 2026-04-29
**Project:** OpenClaw (AI gateway / agent orchestration platform)
**Location:** `/mnt/c/wsl/openclaw/`

## Files Discovered

| File | Path | Purpose |
|------|------|---------|
| Gateway config | `.openclaw/openclaw.json` | Provider/model defaults |
| Environment | `.env` | API keys, tokens |
| Local config | `config/config.yml` | Gateway mode |
| Agent config | `.openclaw/agents/main/agent/agent.json` | Active agent definition |
| Auth profiles | `.openclaw/agents/main/agent/auth-profiles.json` | Provider API keys |
| Model registry | `.openclaw/agents/main/agent/models.json` | Custom model definitions |
| Docker compose | `docker-compose.yml` | Container orchestration |
| Entry point | `openclaw.mjs` | Node.js bootstrap (requires v22.12+) |

## 🔴 Critical Issues Found

### 1. Project Not Built
- **File:** `dist/` (missing)
- **Impact:** OpenClaw cannot start. Entry point `openclaw.mjs` loads `./dist/entry.js` or `./dist/entry.mjs`.
- **Fix:** `pnpm install && pnpm build`

### 2. Node.js Not Installed
- **Check:** `which node` → not found
- **Requirement:** Node.js v22.12+ (hardcoded in `openclaw.mjs:8-9`)
- **Fix:** Install via nvm: `nvm install 22`

### 3. TLS Verification Disabled
- **File:** `.env` and `docker-compose.yml`
- **Value:** `NODE_TLS_REJECT_UNAUTHORIZED=0`
- **Impact:** All HTTPS connections skip certificate validation — man-in-the-middle attack vector
- **Fix:** Remove this env var; use valid certificates instead

### 4. Weak Gateway Token
- **File:** `.env` and `docker-compose.yml`
- **Value:** `OPENCLAW_GATEWAY_TOKEN=ethan2026`
- **Impact:** Brute-forceable; token is a simple word+year pattern
- **Fix:** Generate strong token: `openssl rand -hex 32`

### 5. World-Writable Config Directory
- **File:** `config/`
- **Permission:** `drwxrwxrwx` (777)
- **Impact:** Any user on the system can modify configuration files
- **Fix:** `chmod 755 config/`

### 6. allowUnconfigured Enabled
- **File:** `config/config.yml`
- **Value:** `allowUnconfigured: true`
- **Impact:** Clients can connect without full authentication
- **Fix:** Set to `false` after initial setup is complete

## 🟡 Warnings Found

### 7. Google API Key Stored in Three Places
- `.env`, `docker-compose.yml`, `.openclaw/agents/main/agent/auth-profiles.json`
- **Risk:** Rotation requires updating all three — easy to miss one

### 8. Custom Non-Standard Models
- **File:** `.openclaw/agents/main/agent/models.json`
- **Provider:** `codex` → `https://chatgpt.com/backend-api/v1`
- **Models:** `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.2` (not official OpenAI model names)
- **Note:** This is a ChatGPT reverse-proxy endpoint; stability depends on the proxy

## 🟢 OK Items

- Gateway configured with `google/gemini-1.5-pro` and matching API key
- Port mapping `18789:18789` correct in docker-compose.yml
- One device paired (openclaw-control-ui) with full operator scopes
- Backup docker-compose.yml.bak exists (uses `network_mode: host` variant)

## 🔧 Docker Build Resolution (This Session)

After the initial audit, the project was built via Docker. Key findings:

### Docker Build Success
- **Image:** `openclaw:local` (3.52 GB disk, 734 MB content)
- **Base:** `node:24-bookworm` (SHA256 pinned)
- **Build steps:** 43 in total
- **Total build time:** ~13 minutes (through corporate proxy)

### Proxy Resolution
- **Problem:** `docker build` RUN commands (curl bun.sh, apt-get, pnpm install) failed with DNS resolution errors
- **Root cause:** Docker daemon proxy settings (`/etc/docker/daemon.json` proxies section + systemd http-proxy.conf) apply to containers at runtime, NOT to build containers
- **Fix:** Pass proxy as explicit `--build-arg`:
  ```
  --build-arg HTTP_PROXY=http://10.197.216.7:3128
  --build-arg HTTPS_PROXY=http://10.197.216.7:3128
  --build-arg NO_PROXY=localhost,127.0.0.1,::1
  ```

### Infrastructure Details
- **Docker:** v29.1.3, Docker Compose v2.26.1
- **BuildKit:** v0.26.2
- **Host:** WSL2 Ubuntu 24.04, 12 CPUs, 7.6 GB RAM
- **Docker Root:** `/var/lib/docker`
- **Proxy:** `http://10.197.216.7:3128` (HTTP + HTTPS)
- **Build cache:** 610.8 MB (18 entries) before build; grew significantly after
