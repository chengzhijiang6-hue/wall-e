## Pitfall 11: Dockerfile COPY Context Path Mismatch

**Symptom**: `docker build` fails with `"/requirements.txt": not found` or similar.

**Cause**: When `docker-compose.yaml` has `context: ..` (parent directory), the `COPY` paths in Dockerfile are relative to the parent, not the project directory.

**Fix options**:
1. Change context to `.` and Dockerfile path accordingly
2. Adjust COPY paths to match the context directory structure

```yaml
# Option A: context = project dir (recommended)
build:
  context: .
  dockerfile: Dockerfile

# Option B: context = parent, adjust COPY paths
build:
  context: ..
  dockerfile: multi_user/Dockerfile
# Dockerfile: COPY multi_user/requirements.txt .
```

## Pitfall 12: Python Module Not Found in Docker (ModuleNotFoundError)

**Symptom**: Container starts but immediately crashes with `ModuleNotFoundError: No module named 'multi_user'` (or similar).

**Cause**: The application code is copied to a subdirectory (e.g., `/app/multi_user/`) but Python can't find it because `/app` is not in `sys.path`.

**Fix**: Set `PYTHONPATH` in Dockerfile:
```dockerfile
COPY . ./multi_user/
ENV PYTHONPATH=/app
CMD ["uvicorn", "multi_user.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Alternative**: If code is copied to `/app/` directly, adjust the module import path:
```dockerfile
COPY . .
# CMD uses top-level module name
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Pitfall 13: PostgreSQL Password Discovery for Co-located Services

**Symptom**: New Docker service fails to connect to existing PostgreSQL with `password authentication failed`.

**Cause**: The existing PostgreSQL was deployed with a password from `.env` file, but the new service uses a different default password.

**Fix**: Discover the actual password from the running container:
```bash
docker exec <postgres-container> printenv POSTGRES_PASSWORD
```

Then use the discovered password in the new service's `docker-compose.yaml`.

## Pitfall 14: UUID Serialization in FastAPI Response Models

**Symptom**: FastAPI returns `ResponseValidationError: Input should be a valid string` for UUID fields.

**Cause**: SQLAlchemy returns `uuid.UUID` objects, but Pydantic response model expects `str` for ID fields.

**Fix**: Use `uuid.UUID` type in Pydantic models (not `str`):
```python
import uuid

class UserResponse(BaseModel):
    id: uuid.UUID  # Not: id: str
    username: str
    ...
    model_config = {"from_attributes": True}
```

## Pitfall 15: Mem0 Search Requires `filters` Parameter

**Symptom**: Mem0 search returns 502 with `"Top-level entity parameters frozenset({'user_id'}) are not supported in search()`.

**Cause**: Mem0 v3+ changed the search API. `user_id` must be passed inside `filters`, not as a top-level parameter.

**Fix**:
```python
# ❌ Old format (v2)
payload = {"query": "...", "user_id": "..."}

# ✅ New format (v3+)
payload = {"query": "...", "filters": {"user_id": "..."}}
```

## Pitfall 16: Mem0 Uses `x-api-key` Header, Not Bearer Token

**Symptom**: Mem0 returns 401 `"Invalid or expired token"` when using `Authorization: Bearer <key>`.

**Cause**: Mem0 uses `x-api-key` header for authentication, not standard Bearer token.

**Fix**:
```python
headers = {"x-api-key": api_key}  # Not: {"Authorization": f"Bearer {api_key}"}
```

## Pitfall 17: Mem0 Has No `/health` Endpoint

**Symptom**: Health check to `http://mem0:port/health` returns 404 `{"detail":"Not Found"}`.

**Cause**: Mem0 does not expose a `/health` endpoint. The available endpoints are `/memories`, `/search`, `/auth/*`, etc.

**Fix**: Use `/memories` with a dummy query to check if Mem0 is responding:
```python
async with httpx.AsyncClient(timeout=5.0) as client:
    resp = await client.get(
        f"{settings.MEM0_URL}/memories",
        headers={"x-api-key": settings.MEM0_API_KEY} if settings.MEM0_API_KEY else {},
        params={"user_id": "health_check"},
    )
# Mem0 returns 200 for valid requests
status = "ok" if resp.status_code in (200, 401, 403) else "error"
```

**Note**: 401/403 also indicates the service is running (just rejecting the request), so treat those as "ok" for health check purposes.
