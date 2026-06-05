# Multi-User System + Mem0 Integration Pitfalls

## user_id Mismatch Bug (2026-05-28)

### Symptom
Admin dashboard shows "暂无记忆数据" or `memory_total: 0` for all users, but Mem0 API `/memories` returns actual data.

### Root Cause
Storage and query use different `user_id` formats:

| Operation | Code | user_id used |
|-----------|------|--------------|
| Store (old) | `service.add_memory(str(current_user.id), ...)` | UUID: `e3858193-72ee-4352-aa24-1225d09bd06d` |
| Store (Hermes MCP) | `mem0_add` tool | String: `"ethan"` |
| Query (admin) | `mem_svc.list_memories(str(user.id))` | UUID |
| Query (user API) | `service.list_memories(str(current_user.id))` | UUID |

Mem0 does exact string matching on `user_id`. UUID query against username-stored data returns 0 results.

### Diagnosis
```bash
MEM0_KEY=$(docker exec mem0-dev-mem0-1 printenv ADMIN_API_KEY)

# Check actual user_id format in Mem0
curl -s http://localhost:59110/memories -H "x-api-key: $MEM0_KEY" | grep '"user_id"' | head -5

# Verify: username query works, UUID doesn't
curl -s "http://localhost:59110/memories?user_id=ethan" -H "x-api-key: $MEM0_KEY" | grep -o '"id"' | wc -l
curl -s "http://localhost:59110/memories?user_id=e3858193-72ee-4352-aa24-1225d09bd06d" -H "x-api-key: $MEM0_KEY" | grep -o '"id"' | wc -l
```

### Fix
Change all Mem0 operations to use `user.username` instead of `str(user.id)`:

**memory/routes.py** — 4 locations:
- `add_memory`: `service.add_memory(current_user.username, body.messages)`
- `search_memory`: `service.search_memory(current_user.username, q, limit)`
- `list_memories`: `service.list_memories(current_user.username)`
- `delete_memory`: ownership check `memory_owner != username`, delete call `service.delete_memory(username, memory_id)`

**admin/routes.py** — 2 locations:
- `get_system_stats`: aggregate memory_total by iterating users with `u.username`
- `get_memory_stats`: `mem_svc.list_memories(user.username)` in the per-user loop

### Prevention
When integrating Mem0 with any user system, decide ONE canonical user_id format upfront and use it everywhere. Username (string) is recommended over UUID for Mem0 compatibility.

## .env File Missing (2026-05-28)

### Symptom
multi-user-api container crashes on startup with `password authentication failed for user "postgres"`.

### Root Cause
`.env` file doesn't exist at `/mnt/c/wsl/hermes_official/multi_user/.env`. Docker-compose uses `${DB_PASSWORD}` which resolves to empty string.

### Fix
Create `.env` with correct values (password must match Mem0's Postgres):
```bash
# Get actual password from Mem0 container
docker exec mem0-dev-postgres-1 printenv POSTGRES_PASSWORD
```

## JWT_SECRET Change Invalidates All Tokens

When `.env` is recreated with a new `JWT_SECRET`, all existing tokens in users' localStorage become invalid. Users must:
1. `localStorage.clear()` in browser console
2. Refresh page
3. Re-login with credentials
