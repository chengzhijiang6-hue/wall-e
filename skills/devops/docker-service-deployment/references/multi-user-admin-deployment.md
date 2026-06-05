# Multi-User Admin Panel Deployment & Troubleshooting

## Service Composition

| Service | Internal Port | Host Port | Type | Dependency |
|---------|--------------|-----------|------|------------|
| multi-user-api | 8000 | 59120 | FastAPI (admin dashboard) | Postgres, Mem0, Redis |
| Postgres | 5432 | 59102 | pgvector (shared with Mem0) | — |
| Mem0 API | 8000 | 59110 | Memory service | Postgres |
| Redis | 6379 | 6379 | Cache/session | — |
| Mem0 Dashboard | 3000 | 59101 | Web UI (optional) | Mem0 API |

## Startup

```bash
# Start in dependency order
cd /mnt/c/wsl/mem0/server && docker compose up -d postgres mem0
cd /mnt/c/wsl/hermes_official/multi_user && docker compose up -d redis multi-user-api
```

## .env 配置

Multi-user-api 的 `.env` 文件（`/mnt/c/wsl/hermes_official/multi_user/.env`）必须配置以下值：

```env
DB_HOST=host.docker.internal
DB_PORT=59102
DB_USER=postgres
DB_PASSWORD=***    # 与 Mem0 的 POSTGRES_PASSWORD 一致
DB_NAME=postgres
MEM0_HOST=host.docker.internal
MEM0_PORT=59110
MEM0_API_KEY=***   # 与 Mem0 的 ADMIN_API_KEY 一致
SECRET_KEY=***     # 任意随机字符串
JWT_SECRET=***     # 任意随机字符串
DEBUG=true
LOG_LEVEL=DEBUG
```

**关键**：DB_PASSWORD 和 MEM0_API_KEY 必须与 Mem0 的 `.env` 保持一致，PostgreSQL 是 Mem0 和 multi-user-api 共享的。

## 调试流程

### 症状：Admin 页面加载但记忆统计显示"不可用" / "暂无数据"

```
[1/4] 检查 Mem0（端口 59110）
  $ curl -s -o /dev/null -w "%{http_code}" http://localhost:59110/memories
  # 200/401 → 运行正常；000 → 未启动

[2/4] 检查 multi-user-api（端口 59120）
  $ curl -s http://localhost:59120/health
  # 200 → 运行正常；000 → 容器崩了

[3/4] 如果 59120 无响应，检查容器日志
  $ docker logs multi_user-multi-user-api-1 --tail 30
  # 常见错误："password authentication failed" → .env 中 DB_PASSWORD 错误或缺失

[4/4] 修复后验证
  $ docker compose up -d multi-user-api
  $ curl -s http://localhost:59120/health
  # 然后打开浏览器确认记忆统计正常显示
```

### 症状：容器日志显示 "Application startup failed"

```
1. 检查容器日志定位错误类型
2. 常见根因：
   — "password authentication failed" → .env 中 DB_PASSWORD 为空
   — Mem0 相关错误 → MEM0_API_KEY 缺失或 Mem0 未启动
3. 创建/修复 .env 文件后重启容器
```

## 已知 Pitfalls

- **PostgreSQL 共享**：multi-user-api 和 Mem0 共用同一个 Postgres 实例（端口 59102）。密码在 Mem0 的 `.env` 中定义（POSTGRES_PASSWORD），multi-user-api 必须使用相同密码。
- **`.env` 文件缺失**：.env 被 .gitignore 排除，git clone 后不会自动存在。首次部署必须手动创建。
- **Docker 重启后需要手动启动服务**：这些容器可能因 Docker Desktop 重启而停止，需手动 up -d。
- **Mem0 先于 Postgres 启动**：如果 Mem0 在 Postgres 就绪前启动，会重试连接（自动恢复），但可能需要等待 10-20 秒。
