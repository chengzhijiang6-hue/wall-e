# Multi-User Profile System Integration

## Overview

Hermes CLI has multi-user support via `hermes user` commands. The Multi-User API runs as a separate Docker service on port 59120.

## Service Architecture

```
Hermes CLI (local) → HTTP → Multi-User API (Docker :59120) → PostgreSQL (:59102) + Mem0 (:59110)
```

## CLI Commands

```bash
hermes user login      # Login (interactive username/password prompt)
hermes user logout     # Logout (clears local token)
hermes user whoami     # Show current user + Profile info
hermes user profile    # Show user Profile details
hermes user skills     # Show user's configured skills
```

## Configuration (~/.hermes/config.yaml)

```yaml
multi_user:
  enabled: true
  api_url: "http://localhost:59120"
  auto_login: true
```

## Token Storage

JWT tokens stored at `~/.hermes/multi_user.json`. Contains:
- access_token (30 min expiry)
- refresh_token (7 day expiry)
- user_id, username

## Source Code

- Client: `/mnt/c/wsl/hermes_official/venv/lib/python3.12/site-packages/hermes_cli/multi_user_client.py`
- CLI commands: `/mnt/c/wsl/hermes_official/venv/lib/python3.12/site-packages/hermes_cli/multi_user_cmd.py`
- API server: `/mnt/c/wsl/hermes_official/multi_user/`

## Management UI

- URL: http://localhost:59120/admin
- Features: User CRUD, system stats, memory stats, skill overview, health checks, logs
- Brand: WALL-E

## API Endpoints (25 total)

| Module | Endpoints | Auth |
|--------|-----------|------|
| Auth | register, login, logout, refresh, me | Public (login/register) |
| Profile | CRUD (create, get, update, delete) | JWT required |
| Memory | add, search, list, delete | JWT required |
| Skills | available, user, validate | JWT required |
| Agent | context, context/refresh | JWT required |
| Admin | users, stats, health, memory/stats, skills/overview, logs | Admin only |

## Pitfalls

- **Docker container has no host skills by default**: Mount `~/.hermes/skills` as volume in docker-compose.yaml
- **Mem0 health check**: Use `/memories` endpoint, NOT `/health` (doesn't exist)
- **Token auto-refresh**: Not yet implemented — users must re-login after 30 min
- **Admin dashboard served without auth**: The `/admin` page serves static HTML; auth is only on API endpoints
