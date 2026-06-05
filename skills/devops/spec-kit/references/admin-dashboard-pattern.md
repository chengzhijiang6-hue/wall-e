# 管理面板增强模式

## 分阶段增强系统概览页面

当管理员需要更详细的信息时，按此顺序分阶段增强：

| Phase | 内容 | 后端 API | 前端组件 |
|-------|------|----------|----------|
| 1 | 服务器信息 + 当前用户 | 扩展 GET /admin/stats | 服务器信息卡片 + sidebar 用户信息 |
| 2 | 按用户记忆统计 | GET /admin/memory/stats | 记忆统计卡片 + 用户表格 |
| 3 | 技能总览 + 用户技能 | GET /admin/skills/overview | 技能总览卡片 + 用户技能表格 |
| 4 | 动态健康检查 | GET /admin/health-detailed | 健康状态网格（绿/红 + 延迟） |
| 5 | 记忆归属详情 | 增强 memory/stats | 最近记忆列 |

## Phase 1: 服务器信息 + 当前用户

扩展 SystemStatsResponse：
```python
class SystemStatsResponse(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    online_users: int
    memory_total: int
    api_calls_total: int
    uptime_seconds: float
    version: str
    server_host: str          # 新增
    server_port: int          # 新增
    current_user: dict        # 新增 {id, username, email, is_admin}
```

## Phase 2: 记忆统计（带缓存）

```python
# 5 分钟 TTL 缓存
_memory_stats_cache = None
_memory_stats_cache_ts = 0
_MEMORY_STATS_CACHE_TTL = 300

@router.get("/memory/stats")
async def get_memory_stats(admin, db):
    if _memory_stats_cache and time.time() - _memory_stats_cache_ts < _MEMORY_STATS_CACHE_TTL:
        return _memory_stats_cache
    
    # 遍历所有活跃用户，调用 MemoryService.list_memories(user_id)
    # 按记忆数降序排列
    # 单用户失败不影响其他用户
```

## Phase 3: 技能总览

```python
@router.get("/skills/overview")
async def get_skills_overview(admin, db):
    loader = SkillLoader()
    available = loader.list_available_skills()
    
    # 查询所有用户 + Profile（outer join）
    users = await db.execute(
        select(User, UserProfile)
        .outerjoin(UserProfile, User.id == UserProfile.user_id)
        .where(User.is_active == True)
    )
    
    return {
        "available_skills": available,
        "user_skills": [{"user_id": ..., "username": ..., "skills": [...]}]
    }
```

## Phase 4: 动态健康检查

实际 ping 各服务，记录延迟：

```python
@router.get("/health-detailed")
async def health_detailed(admin):
    result = {}
    
    # API - 总是 ok
    result["api"] = {"status": "ok", "latency_ms": 0.1}
    
    # Database - SELECT 1
    start = time.perf_counter()
    await session.execute(text("SELECT 1"))
    result["database"] = {"status": "ok", "latency_ms": (time.perf_counter() - start) * 1000}
    
    # Redis - PING
    r = aioredis.from_url(settings.REDIS_URL)
    await r.ping()
    
    # Mem0 - 用实际端点测试（不是 /health）
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.MEM0_URL}/memories", headers={"x-api-key": ...})
```

## 关键 Pitfall

1. **Mem0 没有 /health 端点**：用 `/memories` 或 `/openapi.json` 代替
2. **记忆统计需要缓存**：遍历所有用户查 Mem0 很慢，用 5 分钟 TTL 缓存
3. **技能目录在 Docker 中不存在**：需要挂载 `~/.hermes/skills` 到容器
4. **健康检查延迟**：每个服务独立 try/catch，单个失败不影响其他
