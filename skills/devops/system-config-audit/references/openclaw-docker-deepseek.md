# OpenClaw Gateway Docker + DeepSeek 配置手册

## 环境前提

- WSL2 + Ubuntu 24.04
- Docker Engine 29+ (含 Docker Compose v2)
- 公司网络代理: `HTTP_PROXY=http://10.197.216.7:3128`
- Node.js 基础镜像: `node:24-bookworm`

## 项目路径

```
/mnt/c/wsl/openclaw/
```

## Docker 构建

### 代理参数必须显式传入 build

Docker daemon 的 `/etc/docker/daemon.json` 代理配置只作用于容器运行时，**不传递给 build 阶段的 RUN 指令**。

```bash
DOCKER_BUILDKIT=1 docker build \
  --build-arg HTTP_PROXY="http://<proxy>:3128" \
  --build-arg HTTPS_PROXY="http://<proxy>:3128" \
  --build-arg NO_PROXY="localhost,127.0.0.1,::1" \
  -t openclaw:local -f Dockerfile .
```

### 监控构建进度

```bash
docker build --progress=plain ... > /tmp/build.log 2>&1
# 另开终端: tail -f /tmp/build.log
# 轮询: wc -l /tmp/build.log
```

## docker-compose.yml

```yaml
version: '3.8'
services:
  openclaw-gateway:
    image: openclaw:local
    container_name: openclaw-gateway
    restart: unless-stopped
    ports:
      - "18789:18789"
    env_file:
      - .env
    volumes:
      - ./.openclaw:/home/node/.openclaw
      - ./config:/app/config
      - ./workspace:/app/workspace
```

**关键原则**: 使用 `env_file: .env` 而非硬编码 `environment:`。修改 .env 后必须 `docker compose down && up -d`（restart 不够）。

## .env 必备变量

```env
OPENCLAW_GATEWAY_TOKEN=<token>
DEEPSEEK_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
HTTP_PROXY=http://<proxy>:3128
HTTPS_PROXY=http://<proxy>:3128
NO_PROXY=localhost,127.0.0.1,::1
NODE_TLS_REJECT_UNAUTHORIZED=0
```

## DeepSeek 供应商配置

### 自动发现机制

Gateway 通过 `OPENAI_API_KEY` + `OPENAI_BASE_URL` 环境变量自动发现 `deepseek` 供应商，注册 `deepseek-chat` 和 `deepseek-reasoner` 两个模型。`auth-profiles.json` 和 `models.json` 由 Gateway 自动管理，手动修改可能被覆盖。

### 设置默认模型

```bash
docker exec openclaw-gateway \
  node dist/index.js config set agents.defaults.model "deepseek/deepseek-chat"
```

**注意**: 模型名必须是 Gateway 已注册的名称（`deepseek-chat` 而非 `deepseek-v4-flash`）。

## 网络测试

容器内需要通过代理访问外部 API：

```bash
# 测试连通性
docker exec openclaw-gateway curl -sI --max-time 10 https://api.deepseek.com

# 健康检查
curl --noproxy "*" http://127.0.0.1:18789/healthz
# → {"ok":true,"status":"live"}
```

## 测试 API

```bash
docker exec openclaw-gateway \
  node dist/index.js agent \
  -m "你好，请用一句话介绍你自己" \
  --agent main --json
```

## 常见错误

| 错误 | 原因 | 修复 |
|------|------|------|
| `No API key found for provider "deepseek"` | Gateway 自动管理 auth-profiles.json | 改用 OPENAI_API_KEY 环境变量 |
| `Unknown model: openai/deepseek-v4-flash` | 模型名未在 Gateway 注册 | 使用已发现的 deepseek-chat |
| `LLM request failed: network connection error` | 容器内无代理 | .env 添加 HTTP_PROXY 并重建容器 |
| `Gateway token missing` | Control UI 未配对 | Settings 输入令牌 |
| `chat.history unavailable during gateway startup` | 正常现象 | 等待几秒自动恢复 |
