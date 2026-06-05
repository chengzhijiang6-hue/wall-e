# Hermes Agent Config Dependency Chain

**Session Date**: 2026-04-29
**Source**: User asked WALL-E (Hermes Agent v0.11.0) to explain why each config file is necessary for it to run.

## Architecture Overview

Hermes Agent (WALL-E) is a Python-based AI agent running inside WSL2 (Ubuntu 24.04). It connects to DeepSeek API for LLM inference. The config files under `~/.hermes/` form a dependency chain — each one is loaded at a specific stage in the startup sequence.

## Config Dependency Chain (Startup Order)

```
    venv/bin/hermes (Python entry script)
            │
            ▼
    hermes_cli.main.main()
            │
            ▼
    hermes_constants.get_hermes_home()
            │  Reads $HERMES_HOME env var, default: ~/.hermes
            ▼
    config.ensure_hermes_home()
            │  Creates ~/.hermes/ subdirs (logs, sessions, skills, etc.)
            ▼
    config.load_config()
            │  1. Reads ~/.hermes/config.yaml (user settings)
            │  2. Merges with DEFAULT_CONFIG (~500 lines of defaults from
            │     hermes_cli/config.py — model, agent, terminal, security, etc.)
            │  3. Expands ${ENV_VAR} references (e.g., ${DEEPSEEK_API_KEY})
            ▼
    config.load_dotenv()
            │  Reads ~/.hermes/.env → injects API keys into os.environ
            ▼
    config.seed_soul()
            │  If ~/.hermes/SOUL.md doesn't exist, writes DEFAULT_SOUL_MD
            │  This defines the agent's persona/system prompt
            ▼
    auth.json credential pool init
            │  Reads ~/.hermes/auth.json (credential pool)
            │  Registers API keys from .env into the pool
            │  Handles key rotation, priority, failover across providers
            ▼
    state.db SQLite connection
            │  Opens ~/.hermes/state.db
            │  Tables: sessions, messages (with FTS5 full-text search), state_meta
            ▼
    tirith sandbox loader
            │  Loads ~/.hermes/bin/tirith (ELF 64-bit security scanner)
            │  Default: tirith_enabled=true, timeout=5s, fail_open=true
            ▼
    Skills loaded from ~/.hermes/skills/
            ▼
    Ready to chat 🔵
```

## Why Each File Must Exist

| File | Missing Consequence | Role in Lifecycle |
|------|--------------------|-------------------|
| `config.yaml` | Agent has no model/provider config — cannot make API calls | Core routing |
| `.env` | API key missing — DeepSeek API returns 401 Unauthorized | Authentication |
| `SOUL.md` | No system prompt — agent has no identity or behavioral constraints | Personality |
| `auth.json` | No credential management — multi-provider failover/rotation breaks | Credential pool |
| `state.db` | No session/message persistence — agent loses all conversational memory | Persistence |
| `bin/tirith` | Security scanning disabled — tool execution sandbox missing | Security |
| `venv/` (Python venv) | All 18+ package dependencies unavailable — entry point can't import | Runtime |

## Key Finding from This Session

The default `~/.hermes/completion.sh` (shell completion script) is generated at install time but the current environment lacks Node.js (previously at `/home/ethan/.hermes/node/bin/node`, now deleted). Shell completions for `hermes` CLI are unavailable as a result. This doesn't block basic chat functionality but affects CLI discoverability.

## Related Skills

- `response-standards` — the communication protocol that governs ALL agent output
