# Microsoft Teams Integration — Quick Reference

Official docs: https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/messaging/teams

## Architecture

```
Teams 消息 → Microsoft 服务器 → HTTPS Webhook → Hermes Gateway (端口 3978) → Agent 处理
```

Teams 通过 **公开 HTTPS webhook** 投递消息（不同于 Slack 的 Socket Mode），实例需要可公开访问的端点。

## 机器人响应行为

| 场景 | 行为 |
|------|------|
| 个人聊天（私信） | 响应每一条消息，无需 @提及 |
| 群聊 | 仅在被 @提及时响应 |
| 频道 | 仅在被 @提及时响应 |

Teams 将 @提及作为普通消息投递（含 `<at>BotName</at>` 标签），Hermes 自动去除。

## 6 步配置流程

### Step 1: 安装 Teams CLI

```bash
npm install -g @microsoft/teams.cli@preview
teams login
teams status --verbose  # 获取 AAD 对象 ID（TEAMS_ALLOWED_USERS 需要用到）
```

### Step 2: 暴露 Webhook 端口

Teams 无法向 localhost 投递消息。默认端口 `3978`（可通过 `TEAMS_PORT` 设置）。

```bash
# devtunnel（Microsoft 官方，URL 持久）
devtunnel create hermes-bot --allow-anonymous
devtunnel port create hermes-bot -p 3978 --protocol https
devtunnel host hermes-bot

# ngrok（每次运行生成新 URL，除非付费）
ngrok http 3978

# cloudflared（每次运行生成新 URL）
cloudflared tunnel --url http://localhost:3978
```

生产环境使用真实域名 + 有效 TLS 证书（Teams 拒绝自签名证书）。

### Step 3: 创建机器人

```bash
teams app create \
  --name "Hermes" \
  --endpoint "https://<your-tunnel-url>/api/messages"
```

CLI 输出 `CLIENT_ID`、`CLIENT_SECRET`、`TENANT_ID` 和安装链接。客户端密钥只显示一次。

### Step 4: 配置环境变量

`~/.hermes/.env`：
```env
# 必填
TEAMS_CLIENT_ID=<your-client-id>
TEAMS_CLIENT_SECRET=<your-client-secret>
TEAMS_TENANT_ID=<your-tenant-id>

# 限制特定用户访问（推荐）
TEAMS_ALLOWED_USERS=<your-aad-object-id>

# 可选
TEAMS_ALLOW_ALL_USERS=true          # 跳过白名单，允许所有人
TEAMS_PORT=3978                      # webhook 端口（默认 3978）
TEAMS_HOME_CHANNEL=<chat-id>         # cron/主动消息投递的会话 ID
TEAMS_HOME_CHANNEL_NAME=<name>       # 主频道显示名称
```

### Step 5: 启动 Gateway

```bash
HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d gateway
```

验证：
```bash
curl http://localhost:3978/health  # 应返回 ok
docker logs -f hermes              # 查找 [teams] Webhook server listening on 0.0.0.0:3978
```

### Step 6: 在 Teams 中安装应用

```bash
teams app get <teamsAppId> --install-link
# 浏览器打开输出链接 → Teams 客户端安装 → 发送私信开始使用
```

## config.yaml 配置

```yaml
platforms:
  teams:
    enabled: true
    extra:
      client_id: "your-client-id"
      client_secret: "your-secret"
      tenant_id: "your-tenant-id"
      port: 3978
```

## 交互式审批卡片

Agent 需要执行风险命令时，发送 Adaptive Card（4 个按钮）：
- **Allow Once** — 仅批准此次
- **Allow Session** — 本次会期间批准
- **Always Allow** — 永久批准
- **Deny** — 拒绝

## 会议摘要投递（Teams Pipeline）

`teams_pipeline` 插件启用后，会议摘要可投递到 Teams。两种模式：

| 模式 | 适用场景 | 权衡 |
|------|---------|------|
| `incoming_webhook` | 静态 URL 发布到频道 | 不支持回复线程，显示为 webhook 身份 |
| `graph` | 以机器人身份发布 | 需要 Graph 应用注册 + `ChannelMessage.Send` 权限 |

```yaml
platforms:
  teams:
    delivery_mode: "graph"  # 或 "incoming_webhook"
    chat_id: "19:meeting_..."
```

## 生产部署

```bash
# 创建时指定真实域名
teams app create --name "Hermes" --endpoint "https://your-domain.com/api/messages"

# 已有机器人更新端点
teams app update --id <teamsAppId> --endpoint "https://your-domain.com/api/messages"
```

确保 `TEAMS_PORT`（默认 3978）可从互联网访问，TLS 证书有效。

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| health 正常但机器人不响应 | 检查隧道是否运行，消息端点是否匹配隧道 URL |
| `KeyError: 'teams'` | 重启容器（已在当前版本修复） |
| 认证错误 | 验证 `TEAMS_CLIENT_ID`、`TEAMS_CLIENT_SECRET`、`TEAMS_TENANT_ID` |
| `No inference provider configured` | 检查 `.env` 中是否有推理模型 API Key |
| 收到消息但忽略 | AAD 对象 ID 不在 `TEAMS_ALLOWED_USERS` 中 |
| 隧道 URL 变更 | ngrok/cloudflared 每次运行生成新 URL → `teams app update` 更新端点 |
| "此机器人未响应" | Webhook 返回错误，检查 `docker logs hermes` |
| `[teams] Failed to connect` | SDK 认证失败，检查凭据和租户 ID |

## 安全性

**务必设置 `TEAMS_ALLOWED_USERS`**，填入授权用户的 AAD 对象 ID。`TEAMS_ALLOW_ALL_USERS=true` 仅用于开发测试。
