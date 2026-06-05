# Service-Down Diagnosis & Recovery Pattern

## Diagnostic Sequence (for "localhost refused to connect")

When user reports a local service unreachable:

1. **Port check**: `ss -tlnp | grep PORT` — confirm nothing listening
2. **Container audit**: `docker ps -a | grep KEYWORD` — find stopped containers
3. **Port mapping verify**: `docker inspect NAME --format '{{json .HostConfig.PortBindings}}'` — confirm the container owns that port
4. **Start**: `docker start NAME`
5. **Wait + verify**: `sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:PORT/`
6. **Check logs if still failing**: `docker logs --tail 30 NAME`

## Common Pitfall

- `netstat` may not be installed on WSL Ubuntu minimal. Use `ss -tlnp` instead.
- After `docker start`, the app inside may need 5-10s to initialize before accepting connections. Don't declare failure immediately.
- Exit code 1 containers that were previously working usually crashed due to SIGTERM (host reboot / Docker Desktop restart). Starting them again typically works.

## User Environment Service Map

| Service | Container | Host Port → Container Port | Purpose |
|---------|-----------|---------------------------|---------|
| quartz-wiki | `quartz-wiki` | 1313 → 8080 | PLMS knowledge base static site (Quartz/Hugo) |
| llm-wiki | `llm-wiki` | 18080 → 18080 | LLM-Wiki MCP server (wiki + vector search) |
| mem0 | `mem0-dev-postgres-1` | — | Mem0 PostgreSQL (pgvector) |
| redis | `multi_user-redis-1` | — | Redis for multi-user system |

**Note**: quartz-wiki and mem0 containers are NOT set to `--restart=unless-stopped`, so they won't auto-recover after Docker Desktop restart. llm-wiki runs as a systemd user service and auto-restarts.
