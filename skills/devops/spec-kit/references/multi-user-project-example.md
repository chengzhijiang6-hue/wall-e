# Multi-User Profile System — Spec-Driven Development 实战案例

**项目**: Hermes Agent 多用户支持系统
**日期**: 2026-05-22 ~ 2026-05-25
**状态**: ✅ 100% 完成（8 个阶段，65 个任务）

## 项目背景

用户需求：多用户账号密码登录，Agent 读取当前登录用户的 Profile，提供个性化服务（记忆隔离 + 技能动态加载）。

## 产出文档

```
specs/001-multi-user-profile/
├── constitution.md          # 项目宪法（5 条核心原则）
├── spec.md                  # 功能规范（6 个用户故事）
├── plan.md                  # 实现计划（8 个阶段）
├── tasks.md                 # 任务列表（65 个任务）
├── research.md              # 技术调研
├── docker-architecture.md   # Docker 架构评估
├── three-agent-architecture.md  # 三 Agent 协作设计
├── task-tracker.md          # 任务跟踪
└── progress-report.md       # 进度报告
```

## 执行记录

| Phase | 任务数 | 状态 | 审查问题 |
|-------|--------|------|----------|
| Setup | 5 | ✅ | 2 个（settings.py 语法错误、端口冲突） |
| Auth | 12 | ✅ | 0 个 |
| Profile | 8 | ✅ | 0 个 |
| Memory | 9 | ✅ | 1 个（Mem0 API 认证格式） |
| Skills | 8 | ✅ | 0 个 |
| Agent | 8 | ✅ | 0 个 |
| Web UI | 8 | ✅ | 0 个 |
| Integration | 7 | ✅ | 0 个 |

## 关键经验

1. **Phase 1 Setup 必须先评估 Docker 架构** — 本次在 Phase 1 完成后才考虑 Docker，导致返工
2. **监督 Agent 代码审查用 read_file 直接做** — delegate_task 容易因 token 过多中断
3. **每个 Phase 完成后用户确认** — 避免方向偏差
4. **进度报告在 Phase 结束时生成** — 保持透明度
5. **Docker 部署需验证所有 API 端点** — 不能只检查健康检查
6. **Mem0 自托管 API 认证用 x-api-key**，不是 Authorization: Bearer
7. **Mem0 v3+ search 用 filters: {user_id: ...}**，不是顶级 user_id
8. **Pydantic v2 UUID 字段必须用 uuid.UUID 类型**，不能用 str
9. **跨 Session 项目保存进度快照** — progress-snapshot.md + memory 记录路径

## 技术栈

- Python 3.12 + FastAPI + SQLAlchemy async
- PostgreSQL + pgvector（已有）
- Mem0（已有，user_id 隔离）
- Redis（新增，缓存）
- bcrypt + PyJWT（认证）

## 端口规划

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 59102 | 已有 |
| Mem0 API | 59110 | 已有 |
| Mem0 Dashboard | 59101 | 已有 |
| LLM Wiki | 18080 | 已有 |
| Multi-User API | 59120 | 新增 |
| Redis | 6379 | 新增 |
