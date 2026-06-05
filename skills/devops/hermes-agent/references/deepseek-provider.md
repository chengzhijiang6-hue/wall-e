# DeepSeek Provider 详情

## 端点信息

| 项目 | 值 |
|------|-----|
| Provider ID | `deepseek` |
| Base URL | `https://api.deepseek.com/v1` |
| 标准 API Key 变量 | `DEEPSEEK_API_KEY` |
| Hermes 注册方式 | 自定义 provider（config.yaml providers 段） |

## 可用模型列表（2026-05-29 验证）

通过 DeepSeek 官方 API 查询：
```
GET https://api.deepseek.com/v1/models
Authorization: Bearer <DEEPSEEK_API_KEY>
```

| 模型 ID | 类型 | Hermes 模型目录收录 |
|---------|------|---------------------|
| `deepseek-v4-flash` | 快速推理 | ❌ 不在目录中 |
| `deepseek-v4-pro` | 专业推理 | ❌ 不在目录中（仅 openrouter 有 `deepseek/deepseek-v4-pro`） |

**关键发现**：DeepSeek 官方 API 同时提供 flash 和 pro 两个模型，但 Hermes 官方模型目录（model catalog）中**没有 `deepseek` 直连 provider**。目录中只有 `openrouter` 和 `nous` 两个 provider，`deepseek-v4-pro` 仅挂在 openrouter 下。

这导致用户通过 `/model` 交互式选择界面切换时，只能看到 OpenRouter 选项，误以为 DeepSeek API Key 无法使用 pro 模型。

## config.yaml 配置示例

```yaml
providers:
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-v4-pro    # 改为 pro 模型
    base_url: https://api.deepseek.com/v1
```

## 切换使用方式

因为不在模型目录中，`/model` 交互式界面看不到，必须手动指定：

```
/m deepseek-v4-pro --provider deepseek
```

或启动新会话：
```bash
hermes -m deepseek-v4-pro --provider deepseek
```

## 代理兼容性

DeepSeek API 可通过公司代理正常访问（已验证）：
```bash
curl -s https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer <key>" \
  --proxy http://10.197.216.7:3128
# 返回 HTTP 200 + 模型列表
```

## 认证失败特征

| 错误 | HTTP 码 | 含义 | 处理 |
|------|---------|------|------|
| `Provider resolver returned an empty API key. Set OPENROUTER_API_KEY` | — | 模型目录将 deepseek-v4-pro 解析到 openrouter | 用 `/m deepseek-v4-pro --provider deepseek` 手动指定直连 |
| `Invalid API Key` | 401 | API 密钥无效 | 更新 `.env` 中 `DEEPSEEK_API_KEY` |
