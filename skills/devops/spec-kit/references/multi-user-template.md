# Multi-User Profile System Template

基于 Hermes Agent 多用户系统的规范驱动分析成果。可复用于任何需要用户隔离 + 个性化服务的 Agent 项目。

## 适用场景

- AI Agent 需要支持多用户登录
- 每个用户有独立的记忆空间
- 根据用户 Profile 加载不同技能
- 需要个性化 Agent 行为

## 架构模式

```
┌─────────────────────────────────────────┐
│           Agent CLI / API               │
├─────────────────────────────────────────┤
│  登录认证 → Profile 加载 → 记忆隔离     │
├──────────────┬──────────────────────────┤
│   Profile    │        Memory            │
│   (YAML/DB)  │   (user_id 隔离)         │
│   用户配置   │   用户记忆               │
└──────────────┴──────────────────────────┘
```

## 技术选型参考

| 组件 | 推荐 | 替代方案 |
|------|------|----------|
| Web 框架 | FastAPI | Flask, Django |
| ORM | SQLAlchemy | Tortoise ORM |
| 密码加密 | bcrypt | argon2 |
| Session | PyJWT (JWT) | Session + Redis |
| 记忆服务 | Mem0 (user_id) | Hindsight (bank_id) |
| 数据库 | PostgreSQL | MySQL, SQLite |

## 数据模型参考

### 用户表 (users)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(32) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Profile 表 (profiles)

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    role VARCHAR(50),
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    language VARCHAR(10) DEFAULT 'zh',
    preferences JSONB DEFAULT '{}',
    skills TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Profile YAML 结构

```yaml
# ~/.hermes/profiles/<username>.yaml
user_id: ethan
name: Ethan
role: DevOps Engineer
preferences:
  language: Chinese
  timezone: Asia/Shanghai
  docker_ports: "59000+"
skills:
  - devops
  - docker-management
  - hermes-agent
memory_config:
  provider: mem0
  user_id: ethan
```

## API 端点参考

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| /auth/register | POST | 用户注册 | 否 |
| /auth/login | POST | 用户登录 | 否 |
| /auth/logout | POST | 用户登出 | 是 |
| /auth/me | GET | 获取当前用户 | 是 |
| /profile | GET | 获取 Profile | 是 |
| /profile | PUT | 更新 Profile | 是 |
| /memory/add | POST | 添加记忆 | 是 |
| /memory/search | GET | 搜索记忆 | 是 |
| /memory/list | GET | 列出记忆 | 是 |
| /skills/load | GET | 加载技能 | 是 |

## 认证流程

```
用户登录 → 验证密码 → 生成 JWT Token → 返回 Token
后续请求 → 携带 Token → Middleware 验证 → 提取 user_id → 注入上下文
```

## 记忆隔离模式

```python
# Mem0 原生支持 user_id
mem0_add(messages="...", user_id=current_user)
mem0_search(query="...", user_id=current_user)

# Hindsight 使用 bank_id
client.retain(bank_id=f"{user_id}-bank", content="...")
client.recall(bank_id=f"{user_id}-bank", query="...")
```

## 渐进式迁移路径

1. **阶段一**：Mem0 + 自建 Profile（当前 → 3个月）
2. **阶段二**：Mem0 + Hindsight 双层（6个月后，视需求）
3. **阶段三**：完整多用户平台（1年后）

## 安全检查清单

- [ ] 密码使用 bcrypt/argon2 加密
- [ ] JWT Token 有过期时间（默认 24 小时）
- [ ] 登录失败限制（5 次/分钟）
- [ ] 所有 API 验证 user_id（除登录/注册）
- [ ] 删除用户级联删除所有数据
- [ ] CORS 配置限制来源
- [ ] Rate limiting 防止暴力攻击

## 常见 Pitfalls

- **user_id 不一致**：所有记忆操作必须从请求上下文获取 user_id，不能信任客户端传入
- **Session 泄露**：JWT Token 不能包含敏感信息（如密码哈希）
- **N+1 查询**：Profile 查询时避免逐个查询用户信息，使用 JOIN
- **缓存失效**：Profile 更新后必须清除缓存，否则用户看到旧数据
- **Mem0 user_id 格式**：确保 user_id 是字符串类型，不是整数
