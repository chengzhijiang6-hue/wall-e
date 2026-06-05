# Spec-Driven Development: Multi-User Profile System

Real-world example of using spec-kit workflow for a full-stack project.

## Project: Multi-User Profile System

**Goal**: Multi-user authentication, profile management, memory isolation, skill loading for Hermes Agent.

## Workflow Executed

### 1. Constitution (constitution.md)
- 5 core principles: user isolation, progressive enhancement, security first, config-driven, observability
- Technical constraints: WSL2, PostgreSQL+pgvector, DashScope API, Docker
- Quality gates: 80%+ test coverage, security audit, performance <200ms

### 2. Specification (spec.md)
- 6 user stories (P1-P3)
- Given/When/Then acceptance scenarios
- Edge cases and constraints documented

### 3. Plan (plan.md)
- 8 phases: Setup → Auth → Profile → Memory → Skills → Agent → Web UI → Integration
- Tech stack: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL, Redis, Mem0
- Docker deployment architecture

### 4. Tasks (tasks.md)
- 65 tasks total
- Parallel task markers [P]
- Dependencies graph

### 5. Implementation
- Used 3-agent collaboration: Coordinator + Supervisor + Implementer
- Each phase: Implementer codes → Supervisor reviews → Coordinator tracks

## Results

- 25 API endpoints across 6 modules
- 132 test cases (unit + integration + e2e + performance)
- Full admin dashboard with user management, stats, health checks
- CLI integration (hermes user login/logout/whoami)
- Docker Compose deployment on port 59120
- Pushed to GitLab: https://code.exaas.bosch.com/cze8wx/multi-user-system

## Lessons Learned

1. **Phase 1 (Setup) is critical**: Getting Docker, database, and proxy right upfront saves hours later
2. **3-agent pattern works well**: Supervisor catches bugs early (UUID serialization, Mem0 API format)
3. **Real API testing is essential**: Unit tests pass but Mem0 integration needed actual API calls to discover quirks (x-api-key, filters format, no /health)
4. **Docker proxy must be in build phase only**: Clear proxy env vars after apt-get/pip, keep for runtime causes 502 errors
