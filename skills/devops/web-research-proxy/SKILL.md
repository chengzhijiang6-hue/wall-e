---
name: web-research-proxy
category: devops
description: Proxy-aware terminal operations in corporate environments (WSL2, SSL inspection, no direct internet). Covers npm, git, curl, Docker builds, GitHub API, and Node.js proxy quirks.
triggers:
  - user asks to research something on the internet
  - browser tools timeout or urllib/python requests get blocked by security scanner
  - need to fetch structured data from GitHub API or search engines
  - corporate proxy environment blocks certain HTTP client patterns
  - running npm install, git clone, pip install, or any network command in terminal
  - Docker build fails to fetch external dependencies
  - Node.js fetch or native module download fails with ENOTFOUND
tags:
  - web
  - research
  - proxy
  - github-api
  - scraping
---

# Proxy-Aware Terminal Operations in Corporate Environments

Working patterns for any network operation through corporate HTTP proxy (e.g. `10.197.216.7:3128`). **Every terminal command that touches the internet MUST use the proxy.**

## CRITICAL: Always Use Proxy for Terminal Commands

**This is the #1 forgotten rule. The user has corrected this MULTIPLE TIMES.** Every `curl`, `git clone`, `npm install`, `pip install`, `docker build` that fetches from the internet MUST specify the proxy. Failure causes ENOTFOUND, timeout, or silent hangs.

**Before executing ANY network command, ask: "Does this command touch the internet?" If yes, add proxy. No exceptions. No "let me try without proxy first."**

```bash
# The proxy address (use this everywhere)
PROXY=http://10.197.216.7:3128
```

**Anti-pattern to NEVER repeat:**
```bash
# ❌ WRONG — user will correct you angrily
npm install some-package

# ✅ CORRECT — always proxy first
npm config set proxy http://10.197.216.7:3128 && npm config set https-proxy http://10.197.216.7:3128 && npm install some-package
```

## Tool-Specific Proxy Patterns

### curl
```bash
curl -x http://10.197.216.7:3128 -sL "https://example.com"
# Or with env var:
curl --proxy http://10.197.216.7:3128 -sL "https://example.com"
```

### git
```bash
# One-off:
git -c http.proxy=http://10.197.216.7:3128 clone https://github.com/...
# Or config globally (already done in this env, but verify):
git config --global http.proxy http://10.197.216.7:3128
git config --global https.proxy http://10.197.216.7:3128
```

### npm / pnpm
```bash
npm config set proxy http://10.197.216.7:3128
npm config set https-proxy http://10.197.216.7:3128
# Then npm install works without env vars
```

### pip
```bash
pip install --proxy http://10.197.216.7:3128 package
# Or env var: HTTP_PROXY / HTTPS_PROXY
```

### Docker build
Dockerfile ARG/ENV must pass proxy:
```dockerfile
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
```
Build command: `docker build --build-arg HTTP_PROXY=http://10.197.216.7:3128 --build-arg HTTPS_PROXY=http://10.197.216.7:3128 .`

## Why Standard Tools Fail

| Tool | Failure Mode | Root Cause |
|------|-------------|------------|
| `browser_navigate` | Timeout (60s) | Browser process can't route through HTTP proxy |
| Python `urllib.request` + proxy | `BLOCKED: User denied` | Security scanner flags IP+HTTP combo as SSRF risk |
| `curl` piping to `python3 -c` | `BLOCKED: User denied` | Pipe to dynamic Python code triggers security scan |
| Direct internet (no proxy) | Connection refused | Corporate network requires proxy for external access |

## Accessing Internal SSO-Protected Sites from WSL

Bosch internal sites (Docupedia/Confluence, SharePoint, etc.) use Windows Integrated Authentication (Kerberos/NTLM). WSL has no SSO session, but the Windows host does. Use `powershell.exe` to leverage the host's credentials.

### Core Pattern: PowerShell + UseDefaultCredentials

```powershell
# Basic fetch with SSO
powershell.exe -NoProfile -Command "
\$r = Invoke-WebRequest -Uri 'https://inside-docupedia.bosch.com/...' -UseBasicParsing -TimeoutSec 30 -UseDefaultCredentials
\$r.Content | Out-File -FilePath 'C:\Users\CZE8WX\Desktop\output.html' -Encoding utf8
"
```

**Key flags:**
- `-UseDefaultCredentials` — uses the Windows user's Kerberos/NTLM token (REQUIRED for SSO sites)
- `-UseBasicParsing` — avoids IE COM dependency, faster
- `-TimeoutSec 30` — internal sites can be slow

### File I/O Between WSL and PowerShell

| Direction | Method |
|-----------|--------|
| WSL → PowerShell | Use Windows path: `C:\Users\CZE8WX\Desktop\file.txt` |
| PowerShell → WSL | Read via `/mnt/c/Users/CZE8WX/Desktop/file.txt` |

**BOM issue:** PowerShell `Out-File -Encoding utf8` writes UTF-8 with BOM. Python reads with `encoding='utf-8-sig'`, not `utf-8`.

### Confluence REST API (Bosch Docupedia)

Bosch Docupedia (`inside-docupedia.bosch.com`) has a restricted REST API:

| Endpoint | Status | Notes |
|----------|--------|-------|
| `/confluence/rest/api/content/ID` | 404 | Content endpoint blocked |
| `/rest/api/content/ID` (no prefix) | 200 HTML | Redirects to Dashboard, not JSON |
| `/confluence/rest/api/search?cql=...` | 200 JSON | **Only working API endpoint** |
| `/confluence/plugins/pagetree/naturalchildren.action` | 403 | Exists but needs session cookie |

**Working CQL queries:**
```powershell
# Search by space
\$encoded = [uri]::EscapeDataString('space = SPACEKEY AND type = page')
\$url = "https://inside-docupedia.bosch.com/confluence/rest/api/search?cql=\$encoded&limit=50"

# Search by title
\$encoded = [uri]::EscapeDataString('title = "Page Title" AND space = SPACEKEY')

# Search by ancestor
\$encoded = [uri]::EscapeDataString('ancestor = PAGEID')
```

**Important:** `[uri]::EscapeDataString()` is the correct URL encoder in PowerShell. `[System.Web.HttpUtility]::UrlEncode()` requires `Add-Type -AssemblyName System.Web` first and is less reliable.

### JS-Rendered Content: Edge Headless Dump-DOM

When content is loaded via JavaScript (e.g. Confluence page trees, SPAs), `Invoke-WebRequest` only gets the server HTML. Use Edge headless to get the fully rendered DOM:

```powershell
powershell.exe -NoProfile -Command "
\$edgePath = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
\$outFile = 'C:\Users\CZE8WX\Desktop\rendered.txt'
\$process = Start-Process -FilePath \$edgePath `
  -ArgumentList @('--headless', '--disable-gpu', '--dump-dom', '--no-sandbox', 'https://...') `
  -RedirectStandardOutput \$outFile -NoNewWindow -Wait -PassThru
Write-Host 'Exit code:' \$process.ExitCode
"
```

**Key details:**
- `--dump-dom` outputs the fully rendered DOM to stdout (redirect with `-RedirectStandardOutput`)
- Edge inherits Windows SSO credentials automatically
- Output is typically 3-5x larger than raw HTML (JS-rendered content included)
- Error messages go to stderr, not the output file
- Works for any JS-heavy site: SPAs, Confluence page trees, React/Angular apps

### When to Use Each Approach

| Scenario | Tool |
|----------|------|
| SSO site, static content | `powershell.exe Invoke-WebRequest -UseDefaultCredentials` |
| SSO site, JS-rendered content | `powershell.exe` + Edge headless `--dump-dom` |
| SSO site, structured API | PowerShell + REST API with CQL (Confluence) or native API |
| External site via proxy | `curl --proxy http://10.197.216.7:3128` |
| External site, JS-rendered | curl + manual analysis (Edge headless needs proxy config) |

## Working Pattern: curl + File + grep

**The reliable extraction pipeline:**

```bash
# Step 1: Fetch to file (curl with proxy is approved by security scanner)
curl -s --proxy http://PROXY_IP:PORT "https://example.com/search?q=query" \
  -H "User-Agent: Mozilla/5.0" \
  -o /tmp/result.html

# Step 2: Extract with grep (no Python pipe needed)
grep -oP 'class="target_class"[^>]*>\K[^<]+' /tmp/result.html | head -5
```

**Why this works:** `curl` with proxy gets user approval (low risk). File I/O + grep is static analysis, not code execution.

## GitHub API via Proxy

```bash
# Search repositories
curl -s --proxy http://PROXY_IP:PORT \
  "https://api.github.com/search/repositories?q=QUERY&sort=stars&per_page=5" \
  -H "Accept: application/vnd.github.v3+json" \
  -o /tmp/gh_result.json

# Extract key fields with grep (avoids python3 pipe)
grep -oP '"full_name"\s*:\s*"[^"]*"|"stargazers_count"\s*:\s*\d+|"description"\s*:\s*"[^"]*"|"language"\s*:\s*"[^"]*"' /tmp/gh_result.json
```

**Rate limits:**
- Unauthenticated: 60 requests/hour per IP
- Authenticated (GITHUB_TOKEN): 5,000 requests/hour
- `git ls-remote` is NOT rate-limited (use for checking latest commit)

## DuckDuckGo HTML Search

DuckDuckGo's HTML endpoint (`html.duckduckgo.com/html/`) returns lightweight HTML that grep can parse. Google's HTML is heavily obfuscated.

```bash
curl -s --proxy http://PROXY_IP:PORT \
  "https://html.duckduckgo.com/html/?q=search+terms+here" \
  -H "User-Agent: Mozilla/5.0" \
  -o /tmp/ddg_result.html

# Extract result titles
grep -oP 'class="result__a"[^>]*>\K[^<]+' /tmp/ddg_result.html | head -5
```

## Pitfalls

### Security Scanner Blocks Python urllib
Even with proxy set, `python3 -c "import urllib.request; ..."` gets auto-blocked as SSRF when the URL contains an IP address. Use `curl` instead — it gets manual approval flow.

### Pipe to python3 -c Gets Blocked
`curl ... | python3 -c "import sys; ..."` is blocked by security scanner. Always save to file first, then use `grep`/`awk`/`sed` for extraction, or read the file in a separate terminal call.

### GitHub API Returns Empty on Rate Limit
When rate-limited, GitHub returns `{"message":"API rate limit exceeded..."}` with HTTP 403, not an error. Check response size: if `/tmp/gh_result.json` is <200 bytes, it's likely a rate limit response, not search results.

### Browser Always Times Out in Proxy
`browser_navigate` consistently times out in this environment. Don't retry — go straight to curl.

### Node.js fetch() Ignores HTTP_PROXY
Node.js native `fetch()` does NOT respect `HTTP_PROXY`/`HTTPS_PROXY` environment variables. When npm postinstall scripts use `fetch()` to download binaries (e.g. Camoufox, Playwright, Puppeteer), they fail with `ENOTFOUND`.

**Workaround:** Download manually with `curl -x proxy`, then place in the expected cache directory. See `references/nodejs-proxy-quirks.md` for details.

### npm Native Modules May Need Manual Install
When `npm install` in a project with optional native dependencies (e.g. `impit-linux-x64-gnu`), npm may install the wrong platform's module (e.g. Windows `.node` in WSL). Fix: download the correct `.tgz` via curl+proxy and extract to `node_modules/` manually.

### Docker Healthcheck IPv6/localhost
Alpine BusyBox `wget` resolves `localhost` to IPv6 (`::1`). If the app only listens on IPv4 (`0.0.0.0`), healthcheck fails. Fix: use `127.0.0.1` in healthcheck URL. `docker restart` won't pick up compose changes — must `stop/rm/create/start`. See `references/docker-ipv6-healthcheck.md`.

WSL2 xvfb Causes Windows Screen Flash
When a Node.js/Python service starts xvfb (X Virtual Frame Buffer) in WSL2, it triggers the Windows GUI bridge, causing flashing terminal windows on the host.

**Affected tools**: Camofox, Playwright headed mode, any tool using `VirtualDisplay` on Linux.

**Detection**: `xvfb` appears in process list (`ps aux | grep xvfb`).

**Fix**: Set `NO_XVFB=1` environment variable or configure headless mode. For Camofox specifically, see `references/camofox-proxy-setup.md`.

### External API Availability Check Before Configuration

```bash
curl -sk --proxy http://10.197.216.7:3128 "https://target-api.com/endpoint" 2>&1 | grep -i "Access Restricted\|denied\|forbidden"
```

If the proxy returns `Access Restricted`, the integration cannot work in this environment without IT role changes. Don't spend time on configuration — inform the user immediately.

### ... existing pitfalls from above ...
