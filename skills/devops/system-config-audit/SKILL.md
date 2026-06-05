---
name: system-config-audit
category: devops
description: Systematic exploration and documentation of a software system's configuration files, paths, environment variables, and dependencies.
---

# System Configuration Audit

## Trigger Conditions
Use this skill when the user asks to:
- "整理配置文件" / "整理一份配置文件"
- Document all program paths and key configuration info
- Explore and inventory a software system's setup (own agent OR third-party project)
- Create a comprehensive config documentation file
- "检查其配置是否正确" / check whether a program's configuration is correct
- Audit a third-party project's configuration for correctness and security
- "Excel 导出没有数据" / "下载只有表头" / Excel export with headers but no data
- Debug Java/Spring Boot data export functionality
- "前端页面和数据库做个匹配" / "功能对应哪些表" / Map frontend features to database tables
- Reverse-engineer a full-stack codebase to produce feature-to-DB mapping
- "源码分析" / "代码分析" for Vue + Spring Boot + MyBatis projects

## Workflow

### Phase 1: Environment Baseline
```bash
echo "HOME: $HOME"
echo "PWD: $PWD"
echo "USER: $USER"
echo "SHELL: $SHELL"
echo "PATH: $PATH"
echo "HERMES_HOME: $HERMES_HOME"
echo "XDG_CONFIG_HOME: $XDG_CONFIG_HOME"
```

### Phase 2: Discover Home/Data Directory
```bash
# List the agent's home directory (~/.hermes/ or equivalent)
ls -la ~/.hermes/
# Note: look for config.yaml, .env, auth.json, SOUL.md, state.db, etc.
```

### Phase 3: Read All Config Files
Read every configuration file discovered — do NOT skip any:
- `config.yaml` — model/provider config
- `.env` — environment variables and API keys
- `auth.json` — credential pool
- `SOUL.md` — system personality
- Any other JSON, YAML, TOML files in the data directory

### Phase 4: Explore Subdirectories
List contents of every subdirectory:
- `bin/` — binary tools
- `skills/` — skill files
- `cron/` — scheduled tasks
- `memories/` — persistent memory
- `logs/` — log files (agent.log, errors.log)
- `sessions/` — session archives

### Phase 5: Package & Version Info
```bash
# Python package info
pip3 show <package-name>

# Check site-packages for package structure
find /path/to/venv/lib/python*/site-packages/ -maxdepth 1 -name "*<package>*" -type d

# Entry point script
cat /path/to/venv/bin/<cli-name>
```

### Phase 6: System Information
```bash
# OS info
cat /etc/os-release | head -5

# Kernel
uname -a
cat /proc/version

# Python version
python3 --version
```

### Phase 7: Check Logs for Warnings/Errors
```bash
cat ~/.hermes/logs/errors.log
cat ~/.hermes/logs/agent.log | tail -20
```
Log warnings often reveal misconfiguration issues that should be documented.

### Phase 8: Docker Build & Gateway Deployment (for third-party Docker-based projects)

> **Project-specific reference**: For OpenClaw Gateway + DeepSeek specifics (env vars, model config, error table), see `references/openclaw-docker-deepseek.md`.
> For other projects, adapt the general methodology below and follow the project's own README/docs.

#### 8A: Docker Build Through Corporate Proxy

When building a Docker image through a corporate proxy:

1. **Check Docker daemon proxy settings**:
   ```bash
   cat /etc/docker/daemon.json
   cat /etc/systemd/system/docker.service.d/*.conf
   ```
   - daemon.json `proxies` section applies to containers at runtime
   - systemd config applies to daemon itself (image pulls)

2. **Know the gap**: Docker daemon proxy config does NOT automatically pass to `docker build` containers. Build containers need explicit `--build-arg`:
   ```bash
   DOCKER_BUILDKIT=1 docker build \
     --build-arg HTTP_PROXY="http://proxy:3128" \
     --build-arg HTTPS_PROXY="http://proxy:3128" \
     --build-arg http_proxy="http://proxy:3128" \
     --build-arg https_proxy="http://proxy:3128" \
     --build-arg NO_PROXY="localhost,127.0.0.1,::1" \
     --build-arg no_proxy="localhost,127.0.0.1,::1" \
     -t image:tag \
     -f Dockerfile \
     .
   ```
   - Without these build-args, RUN commands inside the build (`curl`, `apt-get`, `pnpm install`) fail with DNS resolution errors.

3. **Use `--progress=plain` for machine-readable output** (redirect to log file):
   ```bash
   docker build ... --progress=plain ... > /tmp/build.log 2>&1
   ```
   - Without `--progress=plain`, BuildKit uses terminal escape codes that don't capture as text.

4. **Monitor build progress** via the log file using foreground tail commands:
   ```bash
   wc -l /tmp/build.log
   tail -5 /tmp/build.log
   ```
   - Parse context transfer size: `grep -oP '[\d.]+(?=MB)'`
   - Parse step completion: `grep "DONE"` lines
   - Parse pnpm progress: `grep "Progress:"`
   - Parse errors: `grep -i "ERROR:"`

5. **Build progress breakdown** (typical timings for a project like OpenClaw):
   - Context transfer (2-5 min, ~100MB for a full project)
   - System deps + Bun install (1-2 min)
   - pnpm install (1-5 min, 1000+ packages)
   - TypeScript build (1-5 min)
   - Image export (1-2 min)

6. **Verify the built image**:
   ```bash
   docker image ls <image>:<tag>
   ```

7. **CRITICAL PITFALL — env_file changes require container recreation**: If `docker-compose.yml` uses `env_file: .env`, changing `.env` after the container is already running does NOT take effect with `docker compose restart`. `restart` only restarts the existing container process — it does not re-read environment variable files. You MUST use `docker compose down && docker compose up -d` to recreate the container with the new variables. This is easily confused because `restart` appears to work (container comes back healthy), but the old env vars are still in memory.

#### 8B: Docker Compose Service Deployment

After a successful Docker image build, deploy and configure the gateway service:

1. **Check existing config files** before starting:
   - `docker-compose.yml` — service definition, port mapping, volume mounts, env sources
   - `.env` — secrets and environment variables
   - Project-specific subdirectories to mount (`.openclaw/`, `config/`, `workspace/`)
   
2. **Remove hardcoded secrets from docker-compose.yml**: API keys, tokens, and passwords should use `env_file: .env` instead of inline `environment:` entries. This prevents accidental secret exposure and simplifies rotation.

3. **Fix volume mount ownership** for the container's runtime user:
   - OpenClaw Docker image runs as `node` (uid 1000)
   - Mounted directories (`.openclaw/`, `config/`) must be writable by uid 1000
   - On WSL /mnt/c/ (DrvFs), use Windows-native permissions; on native Linux, use `chown 1000:1000`
   - The official setup script runs a one-shot root container to fix permissions; this is preferred

4. **Start the service**:
   ```bash
   docker compose up -d
   ```
   (Use `background=true` in terminal tool since `docker compose up -d` may trigger a long-lived process warning.)

5. **Verify container health**:
   - Check `docker ps` for `(healthy)` status
   - For OpenClaw: `curl --noproxy "*" -sS http://127.0.0.1:18789/healthz` should return `{"ok":true,"status":"live"}`
   - Use `--noproxy "*"` to bypass proxy for localhost requests

#### 8C: Post-Deploy Gateway Configuration

Some services require runtime configuration via their own CLI tools inside the container. The general approach:

1. Check the project's docs for runtime CLI commands (e.g., `docker exec <container> <cli-tool> config set ...`)
2. Set required environment variables, API keys, and model defaults
3. Verify settings take effect (check logs, run test queries)
4. Restart if needed

> **OpenClaw specific**: See `references/openclaw-docker-deepseek.md` for DeepSeek model config, env vars, and error troubleshooting.

#### 8D: Background Process Notification Management

When running Docker builds or other long-lived operations in background terminal mode:

- Killed or interrupted background processes (exit code -15 for SIGTERM, -9 for SIGKILL, 130/143 for Ctrl+C) produce `[IMPORTANT: Background process ... completed (exit code N)]` notifications.
- These notifications appear even after the process has been superseded by a newer attempt.
- **Ignore these notifications** for: any killed/interrupted process where a newer build attempt succeeded (exit code 0).
- Only act on background process notifications for processes you are actively waiting on or that have not been superseded.
- To avoid clutter: prefer a single successful background process over multiple interrupted attempts. If you need to retry, consider whether the previous attempt's notification will confuse the conversation flow.


### Phase 9: Dependencies
```bash
# From pip package metadata
cat /path/to/dist-info/METADATA | grep -E "^Requires-Dist|^Provides-Extra"
```

### Phase 9: Root Cause Investigation (for any detected issues)
After finding an issue, do NOT stop at reporting it. Investigate WHY it exists:

```bash
# Check file ownership and timestamps
stat -c '%a %U:%G %y %n' path/to/suspicious/file

# Did a Docker container create this?
# Docker containers run as root inside, so Docker-created files on WSL/mounts
# often show root ownership, 777 permissions, or docker group GID.
# Compare creation timestamps with docker-compose up times.

# Check if secrets/tokens are protected by .gitignore
grep -n "\\.env\\|secret\\|token\\|password" .gitignore .dockerignore 2>/dev/null

# Check if a file was user-created vs shipped with the project
# Files in .git → shipped; files not in .git → user-created
# Also check .env.example to see if an env var is documented or user-added.

# For config values that seem unsafe (e.g., disabled TLS, weak passwords):
# Search the source code or docs for the intended default
grep -rn "NODE_TLS_REJECT\\|allowUnconfigured\\|DEFAULT_TOKEN" src/ docs/ --include="*.ts" --include="*.md" 2>/dev/null | head -10
# If the value only appears in user files (.env, docker-compose.yml, config/)
# but NOT in upstream source code, it was user-added — ask the user why.

# For "project not built" issues:
# Check package.json for "build" script and "main" field
# Check if node_modules/ exists (pnpm install / npm install)
# Check if the project is npm-installed (has dist/) vs source-cloned (no dist/)
# Check for .git directory to distinguish source vs release
```

**Trace the dependency chain**: Each config file serves a specific role in the startup sequence. Document not just what each file contains, but WHY it's necessary for the program to function. This is especially important when auditing your own agent (e.g., Hermes Agent).

### Phase 9B: Session-Level Forensics

When investigating SYSTEM-LEVEL inconsistencies (files vanishing, unexpected state changes, parallel operations):

**1. Check for parallel/concurrent sessions:**
```python
import json, os
from datetime import datetime

sessions_dir = os.path.expanduser("~/.hermes/sessions/")
for f in sorted(os.listdir(sessions_dir), reverse=True)[:3]:
    path = os.path.join(sessions_dir, f)
    with open(path) as fh:
        data = json.load(fh)
    msgs = data.get('messages', [])
    sid = data.get('session_id', '?')
    updated = data.get('last_updated', '?')
    first_user = str(msgs[0].get('content', ''))[:80] if msgs else ''
    print(f"{f}: {sid} | {updated} | first: {first_user}")
```
Look for session files with IDENTICAL first-user-messages — this indicates parallel sessions spawned from the same context compaction event.

**2. Trace session events for specific operations:**
```python
for f in sorted(os.listdir(sessions_dir), reverse=True):
    path = os.path.join(sessions_dir, f)
    with open(path) as fh:
        data = json.load(fh)
    msgs = data.get('messages', [])
    for m in msgs:
        content = str(m.get('content', ''))
        if '<keyword>' in content:
            print(f"[{f}] {m['role']}: {content[:200]}")
```
Use keywords like `skill_manage`, `action=delete`, or the name of a file/skill that vanished.

**3. Check cross-session message correlation:**
```python
# Do two sessions have the same first 5 messages?
# If yes, they are parallel instances of the same conversation fork.
for f in sorted(os.listdir(sessions_dir), reverse=True):
    # ... compare message sequences
```

**4. Cross-reference timestamps across filesystem and logs:**

| Data Source | What It Reveals |
|-------------|-----------------|
| `ls -la ~/.hermes/sessions/` | Session file creation/modification times |
| `~/.hermes/logs/agent.log` | System activity timeline (compression, auxiliary calls) |
| `~/.hermes/skills/.usage.json` | Skill registry (when a skill was created/deleted/patched) |
| `~/.hermes/sessions/*.json` | Individual session message timestamps and tool calls |
| `stat` on skill directory | Physical file creation time on disk |

**5. Check the skill curator state:**
```bash
cat ~/.hermes/skills/.curator_state
cat ~/.hermes/skills/.usage.json
```
- `.curator_state` shows when the last curator run happened and what it did
- If the curator did NOT run (e.g., "auto: no changes"), the deletion was agent-driven, not scheduler-driven
- `.usage.json` shows every skill's lifecycle (created_at, last_patched_at, state: active/deleted)

**6. Distinguish agent-driven vs curator-driven deletion:**

| Evidence | Agent-Driven | Curator-Driven |
|----------|-------------|----------------|
| Session file contains `skill_manage(action='delete')` tool call | ✅ | ❌ |
| `.curator_state` shows a run at the relevant time | ❌ | ✅ |
| Assistant message explains why it deleted the skill | ✅ | ❌ |
| `.usage.json` state changes to "archived" | ❌ curator changes state | ❌ usage.json just loses entry |

**7. Check the specific source code that caused the issue:**
```python
# Navigate to the Hermes Agent package
pip_path = "<venv>/lib/python3.x/site-packages/"
# Read the relevant tool implementation
with open(f"{pip_path}/tools/skill_manager_tool.py") as f:
    source = f.read()
# Search for the delete operation
# Look for _delete_skill(), _security_scan_skill(), _atomic_write_text()
```

**8. Final recommendation:**
After `skill_manage(action='create')` returns success, ALWAYS immediately verify persistence with `skill_view()`. A success return value is NOT a durability guarantee if parallel sessions may be operating. See `references/context-compaction-race-condition.md` for the full reproduction record.

### Phase 10: Security Posture Assessment (for third-party project audits)
When auditing a third-party project (e.g., Docker-compose-based app):

```bash
# Check file permissions on key directories
stat -c '%a %n' config/ .openclaw/ workspace/
# Any 777 directories? That's a security issue.

# Check for disabled TLS
grep -r "NODE_TLS_REJECT_UNAUTHORIZED=0" .env docker-compose.yml *.env* 2>/dev/null
# If found, flag as critical — disables all HTTPS certificate verification.

# Check token/password strength
grep -r "TOKEN\|PASSWORD\|SECRET\|API_KEY" .env docker-compose.yml 2>/dev/null
# Flag weak tokens (e.g., 'ethan2026', 'password123', short alphabetic strings).

# Check build output exists
test -d dist/ && echo "BUILT" || echo "NOT BUILT — project cannot run"

# Check runtime requirements
# e.g., openclaw.mjs requires Node.js v22.12+
grep -E "MIN_NODE|require.*node.*version" *.mjs *.ts 2>/dev/null | head -5
which node 2>/dev/null && node --version || echo "node not in PATH"

# Cross-reference API keys across files
# Same key appearing in .env, docker-compose.yml, AND auth config?
# Flag as maintenance hazard (rotation requires updating N places).

# Check for deprecated/broken backup configs
# e.g., docker-compose.yml.bak with different networking (network_mode: host vs port mapping)
```

### Phase 11: Compile Findings with Severity Ratings
For third-party audits, categorize issues:
- 🔴 **Critical** — prevents startup, or is a severe security vulnerability
- 🟡 **Warning** — misconfiguration, weak security, maintenance burden
- 🟢 **OK** — properly configured items

Format as a table: | Config File | Path | Status |
Then list each issue with a clear description, the problematic value, and the file location.

### Phase 12: Create Windows Batch Launcher (when user requests bat file)

When the user asks for a Windows `.bat` script to launch a WSL-based tool (e.g., Hermes Agent, OpenClaw):

1. **Determine the launch command:**
   ```
   wsl -d <DISTRO_NAME> --cd <WORK_DIR> <EXECUTABLE_PATH>
   ```
   - DISTRO_NAME: from `wsl.exe -l -q` or `$WSL_DISTRO_NAME`
   - WORK_DIR: typically the project root in WSL (e.g., `/mnt/c/wsl/hermes_official`)
   - EXECUTABLE: full path to the CLI entry point (e.g., `/mnt/c/wsl/hermes_official/venv/bin/hermes`)

2. **Encoding rule (CRITICAL):**
   - **NEVER use Chinese characters or any non-ASCII text in a .bat file.**
   - Windows cmd.exe on non-English systems may default to different code pages (437, 936, 65001, etc.), and the encoding used by WSL's filesystem write may not match what cmd.exe expects.
   - GBK/UTF-8/ASCII with BOM approaches are unreliable across different Windows configurations.
   - **Use ONLY pure ASCII (7-bit) characters** in the bat file.
   - If the user wants Chinese messages, explain that ASCII-only is required for reliability and suggest they add their own localized text after testing.

3. **Write the bat file to the Windows Desktop:**
   ```
   /mnt/c/Users/<WIN_USER>/Desktop/<name>.bat
   ```
   - WIN_USER can be found via `cmd.exe /c "echo %USERNAME%"` or by listing `/mnt/c/Users/`

4. **Verify with hex check:**
   ```python
   with open(path, 'rb') as f:
       raw = f.read(200)
   # Every byte should be < 128 (ASCII)
   assert all(b < 128 for b in raw), "Non-ASCII bytes found!"
   ```

5. **Basic bat template (ASCII only):**
   ```bat
   @echo off
   title WALL-E - Hermes Agent
   echo ================================
   echo    Launch WALL-E (Hermes Agent)
   echo ================================
   echo.

   wsl -d Ubuntu-24.04 --cd /mnt/c/wsl/hermes_official /mnt/c/wsl/hermes_official/venv/bin/hermes

   echo.
   if %errorlevel% neq 0 (
       echo Exit code: %errorlevel%
       echo If launch failed, check that WSL is running normally.
       pause
   )
   ```

### Phase 13: Create Windows Desktop Shortcut with Custom Icon (from WSL)

When the user wants a desktop icon for a WSL-based tool:

1. **Check for source image**: Look in the user-specified directory (typically `C:\Users\<USER>\Desktop\ai-os\hermes-icon\` or similar). The image may be `.webp`, `.png`, `.jpg`, or another format.

2. **Convert image to .ico using Pillow:**
   ```python
   from PIL import Image
   img = Image.open('/mnt/c/.../source.png')
   if img.mode != 'RGBA':
       img = img.convert('RGBA')
   
   # Generate multi-resolution ICO (Windows requires multiple sizes)
   sizes = [16, 24, 32, 48, 64, 128, 256]
   # Build ICO manually — Pillow's save() with format='ICO' and sizes=
   # does NOT reliably save multiple frames. Use manual BMP-in-ICO construction:
   # Write ICO header (6 bytes: reserved=0, type=1, count=N)
   # Write directory entries (16 bytes each: w, h, palette=0, reserved=0, planes=1, bpp=32, size, offset)
   # Write BMP data blocks (BITMAPINFOHEADER + BGRA pixel data, bottom-to-top rows)
   # See references/wsl-ico-shortcut.md for the full working implementation.
   ```

3. **Delete any old .lnk file** before creating a new one.

4. **Create shortcut via VBScript (NOT PowerShell COM):**
   - Write a `.vbs` file to `/mnt/c/tmp/` (accessible as `C:\tmp\` from Windows)
   - Execute with: `cscript.exe //nologo "C:\tmp\create_shortcut.vbs"`
   - VBScript content:
     ```vbs
     Set shell = CreateObject("WScript.Shell")
     Set shortcut = shell.CreateShortcut("C:\Users\<USER>\Desktop\<name>.lnk")
     shortcut.TargetPath = "C:\Users\<USER>\Desktop\<name>.bat"
     shortcut.WorkingDirectory = "C:\Users\<USER>\Desktop"
     shortcut.IconLocation = "C:\Users\<USER>\Desktop\ai-os\hermes-icon\hermes.ico"
     shortcut.Description = "description text"
     shortcut.Save
     ```

5. **Verify** the shortcut file exists and contains the icon path reference:
   ```bash
   ls -la "/mnt/c/Users/<USER>/Desktop/<name>.lnk"
   strings "/mnt/c/Users/<USER>/Desktop/<name>.lnk" | grep -i "icon\|ico"
   ```

6. **CRITICAL — Acknowledge the limitation**: You are operating from WSL and CANNOT see the Windows desktop to verify the icon actually renders. After completing the steps above, tell the user honestly: "The shortcut has been created with the icon reference set. I cannot visually verify from WSL whether it renders correctly — please double-click the shortcut to confirm the icon displays properly."

7. **If user reports failure**, do NOT retry blindly. Ask:
   - Is the `.lnk` file on the desktop?
   - Does it have any icon at all (default bat icon)?
   - Did you refresh the desktop (F5) or restart explorer.exe?
   - Is the `.ico` file present in the specified path?

## Output Format
Write findings to a `.txt` file in the project root or user-specified location. Use clear section headers with `===` separators.

### Phase 14: Save Configuration Documentation to Knowledge Base

When the user asks to save configuration documentation to a specific directory (e.g., `知识库` on the Windows Desktop):

1. **Collect all config files** — .env, docker-compose.yml, config.yml, openclaw.json, agent.json, auth-profiles.json, models.json, Dockerfile
2. **Redact sensitive values** — mask API keys (keep first/last 3-4 chars for identification), tokens, passwords
3. **Organize into clear sections** — use structure like:
   - Project overview (path, container name, ports, status)
   - Docker deployment (build commands, start/stop/logs/healthcheck)
   - File tree (each file's purpose)
   - Environment variables table (name = value/description)
   - Each config file's content with explanation
   - Known pitfalls /注意事项
   - Maintenance commands reference
   - Security todo list
4. **Set target path**:
   ```bash
   /mnt/c/Users/<WIN_USER>/Desktop/knowledge/<文件名>
   ```
   WIN_USER is typically `CZE8WX` for this user (check `/mnt/c/Users/`).
   No file extension needed — it's a plain text config reference.
5. **Verify content** — read back first 5 lines AND last 5 lines to confirm file integrity
6. **Confirm to user** — state the Windows path explicitly (e.g., `C:\\Users\\CZE8WX\\Desktop\\knowledge\\EVA配置信息`)

### Phase 15: Third-Party API Provider Exploration & Quota Audit

When the user asks to check a third-party AI model provider's available models, quotas, or usage status (e.g., Aliyun DashScope/Bailian):

1. **Determine the API type**:
   - **REST API with API Key (sk-*)**: Used for inference. Model list + quota limits available via simple HTTP calls.
   - **Cloud Provider OpenAPI (AccessKey/AKSK)**: Used for billing/account management. Needs signed requests via SDK.
   - **Console UI**: Full data (usage + remaining) often only visible in the web console. Programmatic fallback when APIs are insufficient.

2. **Try DashScope-compatible REST API first**:
   ```bash
   # List models
   GET https://dashscope.aliyuncs.com/api/v1/models?page_size=100
   Authorization: Bearer <sk-xxx>
   
   # List quota limits
   GET https://dashscope.aliyuncs.com/api/v1/quotas?page_size=100
   Authorization: Bearer <sk-xxx>
   ```
   Response fields to extract: `model_limit.request_limit`, `usage_limit`, `usage_limit_period`, `prices`, `features` (check for `model-experience` → free trial available).

3. **If billing data is needed, try Aliyun BSS API** (requires RAM AK with AliyunBSSReadOnlyAccess):
   ```python
   # SDK: aliyun-python-sdk-core
   # Endpoint: business.aliyuncs.com
   # API: QueryResourcePackageInstances, QueryInstanceBill
   ```
   Note: Free quotas are NOT tracked as resource packages → billing API returns empty results for free tier.

4. **Console fallback** — if programmatic APIs cannot provide actual consumption data:
   - Tell the user the limitations clearly
   - Provide three options: (a) user copies data from console, (b) provide additional credentials, (c) settle for quota limits only

5. **Data integration** — merge data from multiple sources into a unified report:
   - From API: model names, quota limits, request limits, prices
   - From console: remaining amounts, expiry dates, enabled/disabled status
   - Calculated: used = total - remaining, percentage consumed

6. **Key API response structure**:
   - `/api/v1/models` response: `output.models[].{model, name, prices, capabilities, features, model_info, provider}`
   - `/api/v1/quotas` response: `output.quotas[].{model, workspace_id, model_limit: {request_limit, usage_limit, ...}}`
   - Console TSV format: 5 lines per model (model_code, quota_line, expiry, status, action)

7. **See reference**: `references/aliyun-dashscope-quota-query.md` for full API detail, error investigation, and model mapping.

### Phase 16: Configure API Provider as Hermes Agent Fallback

When adding a new AI model provider as a fallback/secondary model for Hermes Agent:

1. **Add API key to .env** with a descriptive variable name (e.g., `QIANWEN_API_KEY`)
2. **Add provider to config.yaml** — OpenAI-compatible providers work with:
   ```yaml
   providers:
     <provider-name>:
       api_key: ${ENV_VAR_NAME}
       model: <default-model>
       base_url: <openai-compatible-endpoint>
   ```
3. **Configure fallback chain** — if the provider supports multiple models for different use cases:
   ```yaml
   fallback_model:
     - provider: <provider-name>
       model: <model-1>
     - provider: <provider-name>
       model: <model-2>
   ```
4. **Test connectivity** — call the models endpoint or send a minimal chat completion
5. **Note quota/limitations** — record any free tier limits and expiry dates so you know when to expect issues
6. **See reference**: `references/hermes-qwen-dashscope-fallback.md` for the full Qwen/DashScope configuration

## Reference Files
- `references/hermes-v0.11-config-audit.md` — complete config audit output
- `references/openclaw-audit-example.md` — third-party project audit with 🔴/🟡/🟢 ratings
- `references/openclaw-docker-deepseek.md` — OpenClaw Gateway Docker + DeepSeek setup guide (build, .env, model config, errors)
- `references/hermes-agent-config-dependency-chain.md` — why each Hermes Agent config file must exist in the startup sequence
- `references/wsl-bat-launcher.md` — Windows .bat launcher creation with encoding troubleshooting
- `references/wsl-ico-shortcut.md` — ICO generation and Windows shortcut creation from WSL
- `references/context-compaction-race-condition.md` — parallel-session race condition (skills silently deleted by concurrent agent instances during context compaction)
- `references/aliyun-dashscope-quota-query.md` — DashScope/Bailian 配额与用量查询方法论（API + AK/SK + UI 三方案）
- `references/hermes-qwen-dashscope-fallback.md` — Qwen/DashScope 作为 Hermes Agent 备用 provider 的配置
- `references/java-springboot-excel-export-debug.md` — Java Spring Boot Excel 导出调试（有表头无数据的常见原因和排查流程）
- `references/java-project-sql-analysis.md` — Java Maven 项目 SQL 脚本分析方法论（批量提取表名、字段定义、索引、视图，生成数据库结构报告）
- `references/fullstack-codebase-mapping.md` — Full-stack codebase mapping: Vue + Spring Boot + MyBatis 全链路前端→API→Controller→数据库表映射方法论

## Pitfalls
- **ALWAYS load this skill via skill_view() when the task matches trigger conditions.** The workflow ensures no step is missed. Do NOT start an audit without loading it first.
- Don't forget to check for symlinks vs actual files
- Check both ~/.local/bin and ~/.hermes/bin for binaries
- Some configs reference each other (e.g., config.yaml references .env); trace these chains
- SQLite files (state.db) have companion files (.db-shm, .db-wal)
- WSL paths: Windows drives mount at /mnt/c/, /mnt/d/, etc.
- When placing output on Windows Desktop, translate path: C:\Users\NAME\Desktop\ → /mnt/c/Users/NAME/Desktop/knowledge/
- If a log contains a warning, flag it explicitly to the user
- When auditing your own agent (Hermes Agent), you can trace the full config dependency chain. The relationship between config files isn't arbitrary — each one serves a specific role at a specific stage in startup. Documenting "why this file must exist" is as important as "what it contains."
- **Bat file encoding**: Never put non-ASCII characters in .bat files written from WSL. Pure ASCII only. The encoding mismatch between WSL (UTF-8) and Windows cmd.exe (variable code page) makes non-ASCII text unreliable.
- **Context compaction parallel-session race condition**: If the context window fills during a long session, Hermes Agent may auto-spawn a parallel session that independently processes the same user requests. This parallel session can autonomously review skill files and delete them as "redundant" without user approval, while the original session continues unaware. After creating a skill with `skill_manage()`, always verify persistence with `skill_view()` — a success return value is not a guarantee of durability. See `references/context-compaction-race-condition.md` for the full reproduction record.
- **Directory rename/path migration**: When the user renames a major directory (e.g., `知识库` → `knowledge`), the agent must systematically update ALL references in this order: (1) rename the folder via `mv`, (2) update SOUL.md and MEMORY.md, (3) search and update all skill SKILL.md files, (4) search and update files within the renamed directory itself. Distinguish "path references" (e.g., `Desktop/知识库/`) that need updating from "concept references" (e.g., "知识库 as a generic term") that do NOT. Do NOT modify session history JSON files — those are historical records. Use `execute_code` with batch string replacement for efficiency. Always verify with `grep` after completion.
