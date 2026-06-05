# Multi-User CLI Integration Pattern

## Architecture

```
┌─────────────────────────────────┐
│  Hermes Agent CLI (本地运行)     │
│  hermes user login/logout/whoami│
├─────────────────────────────────┤
│  HTTP API                       │
│  Token: ~/.hermes/multi_user.json│
├─────────────────────────────────┤
│  Multi-User API (Docker)        │
│  Port 59120                     │
├─────────────────────────────────┤
│  PostgreSQL + Redis + Mem0      │
└─────────────────────────────────┘
```

## Files to Create

### 1. multi_user_client.py

Location: `hermes_cli/multi_user_client.py`

Key classes:
- `MultiUserClient` — HTTP client for API
- `is_multi_user_enabled()` — reads config.yaml
- `get_api_url()` — reads config.yaml

Token storage: `~/.hermes/multi_user.json`

### 2. multi_user_cmd.py

Location: `hermes_cli/multi_user_cmd.py`

Commands:
- `cmd_user_login` — interactive login
- `cmd_user_logout` — clear token
- `cmd_user_whoami` — show user + profile
- `cmd_user_profile` — show profile
- `cmd_user_skills` — show skills

### 3. main.py registration

Add before profile commands:
```python
from hermes_cli.multi_user_cmd import register_user_commands
register_user_commands(subparsers)
```

## Config

```yaml
# ~/.hermes/config.yaml
multi_user:
  enabled: true
  api_url: "http://localhost:59120"
  auto_login: true
```

## Pitfalls

- Config reading: Use `yaml.safe_load()` directly, NOT `from hermes_cli.config import get_config`
- Time parsing: Use `datetime.fromisoformat()`, NOT `time.fromisoformat()` (Python 3.12)
- Token expiry: JWT tokens expire in 30 minutes, refresh_token in 7 days
