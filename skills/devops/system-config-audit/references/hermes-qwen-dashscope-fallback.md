# Hermes Agent 配置 Qwen/DashScope 作为备用 Provider

## 配置总览

Hermes Agent 使用 `config.yaml` + `.env` 存储 provider 配置。Qwen/DashScope 支持 OpenAI 兼容接口，可以作为主 provider 的 fallback。

## .env 文件

```env
# 主 provider (DeepSeek)
DEEPSEEK_API_KEY=sk-xxx

# 备用 provider (Qwen/DashScope)
QIANWEN_API_KEY=sk-xxx
```

## config.yaml

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
providers:
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-v4-flash
    base_url: https://api.deepseek.com/v1
  dashscope:
    api_key: ${QIANWEN_API_KEY}
    model: qwen3.6-flash
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
fallback_model:
  - provider: dashscope
    model: qwen3.6-flash
  - provider: dashscope
    model: qwq-plus
```

## 关键配置说明

### DashScope OpenAI 兼容接口

- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 认证: Bearer token 方式，与 OpenAI SDK 完全兼容
- 模型名: 直接用 DashScope 的 model code（如 `qwen3.6-flash`、`qwq-plus`）

### 模型选择优先级

根据本用户环境的免费用量剩余情况：

| 优先级 | 模型 | 用途 | 剩余额度 | 有效至 |
|--------|------|------|---------|--------|
| 1 | qwen3.6-flash | 日常通用 | 1,000,000 tokens ✅ | 2026/07/17 |
| 2 | qwq-plus | 推理思考 | 1,000,000 tokens ✅ | 2026/06/07 |
| 3 | qwen3.5-flash | 轻量快速 | 1,000,000 tokens ✅ | 2026/06/07 |
| 4 | qwen3.5-plus | 高质量 | 1,000,000 tokens ✅ | 2026/06/07 |
| ⚠️ | qwen3.6-plus | 高质量但快用完了 | 仅 47,323 tokens | 2026/07/02 |

### fallback_model 格式

`fallback_model` 可以是：
- 单个 dict: `{provider: x, model: y}`
- 列表（链式回退）: `[{provider: x, model: y}, {provider: z, model: w}]`

链式回退的 fallback 会从上到下依次尝试。仅当当前 provider 不可用时才切换到下一个。

### auth.json 的作用

`auth.json` 中的 `credential_pool` 管理 provider 的凭证池。如果 provider 在 `config.yaml` 中用 `${ENV_VAR}` 引用环境变量，启动时自动读取，无需手动修改 auth.json。

## 验证方法

### 测试 DashScope API 连通性

```bash
curl -s --max-time 10 \
  -H "Authorization: Bearer <sk-xxx>" \
  "https://dashscope.aliyuncs.com/compatible-mode/v1/models" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print([m['id'] for m in d.get('data',[])][:5])"
```

### 测试特定模型推理

```bash
curl -s --max-time 30 \
  -H "Authorization: Bearer <sk-xxx>" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-flash","messages":[{"role":"user","content":"你好"}]}' \
  "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
```

### 验证 Hermes 配置

```bash
# hermes model 需要交互式终端，不能用管道
# 直接检查配置文件
cat ~/.hermes/config.yaml
cat ~/.hermes/.env
```
