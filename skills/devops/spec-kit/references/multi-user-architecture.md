# 多用户系统架构模式

## 架构设计

```
┌─────────────────────────────────────────┐
│         用户终端（本地）                 │
│  ┌─────────────────────────────────┐    │
│  │    Hermes Agent CLI             │    │
│  │    - 用户交互                   │    │
│  │    - 技能加载（本地文件）         │    │
│  │    - 调用 Docker API            │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
                    │
                    │ HTTP (localhost:59120)
                    ▼
┌─────────────────────────────────────────┐
│         Docker 环境                      │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Multi-User   │  │    Redis     │     │
│  │ API (FastAPI)│  │   (缓存)     │     │
│  │   :59120     │  │   :6379      │     │
│  └──────────────┘  └──────────────┘     │
│         │                │              │
│  ┌──────────────┐  ┌──────────────┐     │
│  │   Mem0 API   │  │  PostgreSQL  │     │
│  │   :59110     │  │   :59102     │     │
│  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────┘
```

## 核心设计决策

1. **CLI 本地运行** — 用户直接交互，不放入 Docker
2. **API 容器化** — 所有业务逻辑在 Docker 中
3. **HTTP 通信** — CLI 通过 localhost 调用 Docker API
4. **技能本地存储** — 技能文件在 CLI 本地，Profile 绑定从 API 获取

## 模块划分

| 模块 | 职责 | API 前缀 |
|------|------|----------|
| auth | 认证（注册、登录、JWT） | /api/v1/auth |
| profile | 用户 Profile CRUD | /api/v1/profile |
| memory | 记忆隔离（封装 Mem0） | /api/v1/memory |
| skills | 技能动态加载 | /api/v1/skills |
| agent | 个性化上下文生成 | /api/v1/agent |
| admin | 管理后台 | /api/v1/admin |

## 认证流程

```
用户登录 → 验证密码 → 生成 JWT Token → 保存到 ~/.hermes/multi_user.json
后续请求 → 从文件读取 Token → Authorization: Bearer <token>
```

## 记忆隔离

所有 Mem0 操作必须带 user_id：
```python
# 添加记忆
mem0_add(messages="...", user_id=current_user.id)

# 搜索记忆（注意 filters 格式）
mem0_search(query="...", filters={"user_id": current_user.id})
```

## 技能加载

```
用户登录 → 获取 Profile → 获取 skills 列表 → 加载本地 ~/.hermes/skills/ 目录
```

Docker 容器需要挂载技能目录：
```yaml
volumes:
  - ~/.hermes/skills:/root/.hermes/skills:ro
```

## 端口规划

| 服务 | 端口 | 说明 |
|------|------|------|
| Multi-User API | 59120 | 主服务 |
| Redis | 6379 | 缓存 |
| Mem0 | 59110 | 记忆服务 |
| PostgreSQL | 59102 | 数据库 |

## CLI 命令设计

```bash
hermes user login      # 登录（交互式输入密码）
hermes user logout     # 登出（清除本地 Token）
hermes user whoami     # 查看当前用户 + Profile
hermes user profile    # 查看 Profile 详情
hermes user skills     # 查看已配置技能
```
