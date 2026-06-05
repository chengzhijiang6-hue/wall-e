# Multi-User Admin Panel — Known Pitfalls (Extended)

## user_id Format Mismatch with Mem0 (2026-05-28)

**Symptom**: Admin dashboard memory stats show "暂无记忆数据" or `memory_total: 0`, but Mem0 API `/memories` returns actual data.

**Root Cause**: Memory storage and query use different `user_id` formats.
- Hermes MCP `mem0_add` tool stores with `user_id="ethan"` (username string)
- multi-user-api code queries with `user_id="e3858193-..."` (UUID from DB)
- Mem0 does exact string matching → UUID query returns 0 results

**Fix**: Change all Mem0 operations in `memory/routes.py` and `admin/routes.py` to use `user.username` instead of `str(user.id)`.

**Diagnosis**:
```bash
MEM0_KEY=$(docker exec mem0-dev-mem0-1 printenv ADMIN_API_KEY)
# Check actual user_id format
curl -s http://localhost:59110/memories -H "x-api-key: $MEM0_KEY" | grep '"user_id"' | head -3
# Compare username vs UUID query results
curl -s "http://localhost:59110/memories?user_id=ethan" -H "x-api-key: $MEM0_KEY" | grep -o '"id"' | wc -l
```

## JWT_SECRET Change Invalidates All Tokens

When `.env` is recreated with a new `JWT_SECRET`, all existing tokens in users' localStorage become invalid. The admin page will show "Invalid or expired token" or "Signature verification failed".

**Fix**: Guide user to:
1. Open browser console (F12)
2. Execute `localStorage.clear()`
3. Refresh page
4. Re-login with credentials
