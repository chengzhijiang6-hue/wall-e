# Hermes Agent v0.11.0 — Full Config Audit (Reference Example)

**Session Date**: 2026-04-29
**System**: WSL2 (Ubuntu 24.04, Linux 6.6.87.2-microsoft-standard-WSL2)
**User**: ethan

## Key Paths Discovered

| Component | Path |
|-----------|------|
| Project root | `/mnt/c/wsl/hermes_official/` |
| Python venv | `/mnt/c/wsl/hermes_official/venv/` |
| CLI entry | `/mnt/c/wsl/hermes_official/venv/bin/hermes` (Python script) |
| Data dir | `/home/ethan/.hermes/` |
| Config | `~/.hermes/config.yaml` |
| Env vars | `~/.hermes/.env` |
| Auth creds | `~/.hermes/auth.json` |
| SOUL | `~/.hermes/SOUL.md` |
| SQLite state | `~/.hermes/state.db` (+ .shm, .wal) |
| Sandbox binary | `~/.hermes/bin/tirith` (12MB ELF 64-bit) |
| Node.js | `~/.hermes/node/bin/node` (linked from ~/.local/bin) |

## Config Details

```yaml
# config.yaml
model:
  default: deepseek-v4-flash
  provider: deepseek

providers:
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-v4-flash
    base_url: https://api.deepseek.com/v1
```

```ini
# .env
DEEPSEEK_API_KEY=sk-1a85...
```

## Errors/Warnings Discovered

The errors.log contained:
> `OPENAI_BASE_URL is set but model.provider is 'deepseek'. Auxiliary clients may route to the wrong endpoint.`

This happens because hermes-agent uses an OpenAI-compatible client internally even when provider is deepseek. Fix: run `hermes model` to reconfigure.

## Dependencies (18 packages)

Core: openai, anthropic, httpx[socks], requests, pydantic, pyyaml, jinja2, prompt_toolkit, rich, fire, tenacity, python-dotenv
Search: exa-py, firecrawl-py, parallel-web
Media: fal-client, edge-tts
Auth: PyJWT[crypto]

## Discovery Sequence Used

1. env vars (HOME, PWD, PATH, HERMES_HOME)
2. ls -la ~/.hermes/
3. Read: config.yaml → .env → auth.json → SOUL.md
4. ls subdirs: bin/, skills/, cron/, memories/, logs/, sessions/
5. pip show hermes-agent → version, location, requires
6. cat /proc/version, /etc/os-release, uname -a
7. Read errors.log → caught routing warning
8. Trace CLI entry point → hermes_cli.main
9. Check pyvenv.cfg, dist-info/METADATA
10. Compile into structured txt file
