# Docker Corporate Proxy Deployment

When building Docker images in a corporate network (e.g., Bosch with proxy at `10.197.216.7:3128`), the Dockerfile needs proxy configuration for the **build phase** (apt-get, pip install, npm install). At runtime, the container accesses host services via `host.docker.internal`.

## Dockerfile Pattern

```dockerfile
FROM python:3.12-slim

# Proxy for build phase (apt-get, pip)
ENV HTTP_PROXY=http://10.197.216.7:3128
ENV HTTPS_PROXY=http://10.197.216.7:3128
ENV http_proxy=http://10.197.216.7:3128
ENV https_proxy=http://10.197.216.7:3128

WORKDIR /app

# Install system dependencies (needs proxy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (needs proxy)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clear proxy for runtime (container accesses host via host.docker.internal)
ENV HTTP_PROXY=
ENV HTTPS_PROXY=
ENV http_proxy=
ENV https_proxy=

# Copy application code
COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## docker-compose.yaml Pattern

```yaml
version: "3.9"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "59120:8000"
    environment:
      - DB_HOST=host.docker.internal
      - DB_PORT=59102
      - DB_PASSWORD=${DB_PASSWORD}  # Use env vars, NOT hardcoded
      - MEM0_API_KEY=${MEM0_API_KEY}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ~/.hermes/skills:/root/.hermes/skills:ro  # Mount host skills
    restart: unless-stopped
```

## Key Patterns

### 1. Proxy in Build, Not Runtime
Set proxy env vars BEFORE apt-get/pip, clear them AFTER. The container accesses host services via `host.docker.internal`, not the proxy.

### 2. PYTHONPATH for Subdirectory Modules
When code is copied into a subdirectory (`COPY . ./multi_user/`), set `ENV PYTHONPATH=/app` so Python can find the module.

### 3. host.docker.internal for Host Services
Use `extra_hosts: ["host.docker.internal:host-gateway"]` to let the container access PostgreSQL, Redis, Mem0 on the host.

### 4. Environment Variables for Secrets
Never hardcode passwords in docker-compose.yaml. Use `${VAR}` syntax and provide via `.env` file or shell environment.

### 5. Volume Mount for Skills
Mount `~/.hermes/skills` as read-only to make host skills available in the container:
```yaml
volumes:
  - ~/.hermes/skills:/root/.hermes/skills:ro
```

## Pitfalls

- **Proxy not cleared for runtime**: If proxy env vars persist, the container tries to reach `host.docker.internal` through the proxy, which fails. Always clear after build phase.
- **__pycache__ in git**: Add `__pycache__/` to `.gitignore` before initial commit.
- **Hardcoded passwords in docker-compose.yaml**: Always use `${VAR}` syntax. Check with `grep -r "password\|secret\|key" . --include="*.yaml"` before committing.
