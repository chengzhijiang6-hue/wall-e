# Docker FastAPI Deployment Patterns

## Pitfalls Discovered (Multi-User Profile System)

### 1. Proxy Configuration in Dockerfile

Corporate proxy must be set in Dockerfile for `apt-get` and `pip install`:

```dockerfile
ENV HTTP_PROXY=http://10.197.216.7:3128
ENV HTTPS_PROXY=http://10.197.216.7:3128

RUN apt-get update && apt-get install -y gcc libpq-dev
RUN pip install --no-cache-dir -r requirements.txt

# Clear proxy for runtime (use docker-compose environment instead)
ENV HTTP_PROXY=
ENV HTTPS_PROXY=
```

### 2. Module Path Issues

When code is in a subdirectory:

```dockerfile
# Copy to subdirectory
COPY . ./multi_user/

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Use qualified module path
CMD ["uvicorn", "multi_user.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. UUID Serialization

Pydantic models must use `uuid.UUID`, not `str`:

```python
import uuid

class UserResponse(BaseModel):
    id: uuid.UUID  # Not: id: str
    username: str
    model_config = {"from_attributes": True}
```

### 4. Mem0 Health Check

Mem0 has no `/health` endpoint. Use `/memories` with `x-api-key` header:

```python
async with httpx.AsyncClient(timeout=5.0) as client:
    resp = await client.get(
        f"{settings.MEM0_URL}/memories",
        headers={"x-api-key": settings.MEM0_API_KEY} if settings.MEM0_API_KEY else {},
        params={"user_id": "health_check"},
    )
# Status 200/401/403 = service is alive
```

### 5. Mem0 Search API

Mem0 v3+ uses `filters` parameter:

```python
# ❌ Old format
payload = {"query": "...", "user_id": "..."}

# ✅ New format
payload = {"query": "...", "filters": {"user_id": "..."}}
```

### 6. Mem0 Authentication

Mem0 uses `x-api-key` header, not Bearer token:

```python
headers = {"x-api-key": api_key}  # Not: {"Authorization": f"Bearer {api_key}"}
```

### 7. PostgreSQL Password Discovery

For co-located services, discover password from running container:

```bash
docker exec <postgres-container> printenv POSTGRES_PASSWORD
```

### 8. Skills Directory Mounting

Mount host skills directory into container:

```yaml
volumes:
  - ~/.hermes/skills:/root/.hermes/skills:ro
```

### 9. Docker Compose Port Mapping

Use high ports to avoid conflicts:

```yaml
ports:
  - "59120:8000"  # Not: "8000:8000"
```
