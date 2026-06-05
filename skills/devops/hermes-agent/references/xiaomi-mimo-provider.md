# Xiaomi MIMO Provider (小米) 详情

## 端点信息

| 项目 | 值 |
|------|-----|
| Provider ID | `xiaomi` |
| Base URL (标准) | `https://api.xiaomimimo.com/v1` |
| Base URL (token-plan 专属) | `https://token-plan-cn.xiaomimimo.com/v1` |
| Base URL (Anthropic 专属) | `https://token-plan-cn.xiaomimimo.com/anthropic` |
| 标准 API Key 变量 | `XIAOMI_API_KEY` |
| Base URL 环境变量 | `XIAOMI_BASE_URL` (在 `.env` 中设置) |
| Hermes 注册位置 | `auth.py:358-365` |
| API 密钥格式 | `sk-...` 前缀 (标准) / `tp-...` 前缀 (token-plan) |

## 可用模型列表（2026-05-08 验证）

通过 token-plan 专属端点查询：
```
GET https://token-plan-cn.xiaomimimo.com/v1/models
Authorization: Bearer tp-...
```

| 模型 ID | 类型 |
|---------|------|
| `mimo-v2-omni` | 多模态 |
| `mimo-v2-pro` | 文本主力 |
| `mimo-v2-tts` | 语音合成 |
| `mimo-v2.5` | 新一代文本 |
| `mimo-v2.5-pro` | **新一代文本主力（当前主力）** |
| `mimo-v2.5-tts` | 新一代语音合成 |
| `mimo-v2.5-tts-voiceclone` | 语音克隆 |
| `mimo-v2.5-tts-voicedesign` | 语音设计 |

## Base URL 覆盖机制（关键）

Hermes 将 Xiaomi 作为**内置 provider** 注册在 `auth.py:358-365`。运行时 base_url 的优先级：

1. **最高**: `XIAOMI_BASE_URL` 环境变量（在 `.env` 中设置）
2. **中等**: `auth.json` 凭据池缓存的值
3. **最低**: `auth.py` 中的硬编码默认值 `https://api.xiaomimimo.com/v1`

**⚠️ 关键**：仅修改 `config.yaml` 的 `providers.xiaomi.base_url` 不会生效。
内置 provider 的运行时 base_url 来自**凭据池**，而凭据池在启动时从 `auth.py` 默认值 + 环境变量 `XIAOMI_BASE_URL` 初始化。
`config.yaml` 的 `providers.xiaomi.base_url` 创建的是 `custom:xiaomi` 条目，该条目不会被使用。

**正确的修改方式**：
```bash
# 1. 在 .env 中设置 XIAOMI_BASE_URL
echo "XIAOMI_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1" >> ~/.hermes/.env

# 2. 同步更新 config.yaml（用于文档一致性）
# 3. 手动更新 auth.json 中的缓存 base_url
```

## 代理兼容性

Mimo API 可通过公司代理正常访问（已验证）：
```bash
curl -s https://token-plan-cn.xiaomimimo.com/v1/models \
  -H "Authorization: Bearer tp-xxx" \
  --proxy http://10.197.216.7:3128
# 返回 HTTP 200 + 模型列表
```

## config.yaml 配置示例

```yaml
model:
  default: mimo-v2.5-pro
  provider: xiaomi
providers:
  xiaomi:
    api_key: ${XIAOMI_API_KEY}
    model: mimo-v2.5-pro
    base_url: https://token-plan-cn.xiaomimimo.com/v1
```

注意：config.yaml 配置仅用于展示和文档一致性，实际运行时 base_url 来自 `XIAOMI_BASE_URL` 环境变量。

## Token-Plan 专属端点

当使用小米 Token Plan 套餐时：
- **OpenAI 兼容**: `https://token-plan-cn.xiaomimimo.com/v1`
- **Anthropic 兼容**: `https://token-plan-cn.xiaomimimo.com/anthropic`
- **API Key 格式**: `tp-...` 前缀（不同于常规的 `sk-...`）
- **模型列表**: 与标准端点相同（mimo-v2.5-pro, mimo-v2-pro 等）
- **Base URL 设置**: 必须在 `.env` 中添加 `XIAOMI_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1`

## mimo-v2.5-pro 推理模型特性（2026-05-14 验证）

mimo-v2.5-pro 是**推理模型**，与普通聊天模型有关键区别：

| 特性 | 说明 |
|------|------|
| reasoning_tokens | 模型在输出内容前会消耗 token 进行内部推理 |
| max_tokens 预算 | reasoning_tokens 和 content_tokens 共享 max_tokens 预算 |
| 低 max_tokens 风险 | max_tokens=20 时，19 个用于推理，内容为空 |

**实测数据**（2026-05-14，通过代理调用 token-plan 端点）：
- prompt "你好" + max_tokens=20 → Content: 空, reasoning_tokens=19, finish=length
- prompt "你好" + max_tokens=512 → Content: "你好！😊", reasoning_tokens=23, finish=stop

**规则**：所有 mimo-v2.5-pro 调用必须使用 `max_tokens >= 512`，否则推理消耗完预算导致空输出。

---

## 认证失败特征

| 错误 | HTTP 码 | 含义 | 处理 |
|------|---------|------|------|
| `Invalid API Key` | 401 | API 密钥过期/无效 | 更新 `.env` 中 `XIAOMI_API_KEY` |
| `Insufficient account balance` | 402 | 账户余额不足 | 充值或获取新 token-plan key |
| token-plan 旧端点 | 401 | 使用了标准端点而非专属端点 | 确保 `XIAOMI_BASE_URL` 设置为 `token-plan-cn.xiaomimimo.com` |
