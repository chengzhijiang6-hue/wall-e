# Model Ladder History

Current as of 2026-05-08. Records the progression of exhausted models and provider failures.

## Current Ladder

| # | Model | Provider | Role | Status |
|---|-------|----------|------|--------|
| 1 | mimo-v2.5-pro | xiaomi (MIMO) | 主力 | ✅ Active |
| 2 | deepseek-v4-flash | deepseek | 兜底 | ✅ Active |

## Provider Failures

| Provider | Reason | Date | Models Affected | Recovery Path |
|----------|--------|------|----------------|---------------|
| DashScope | Account arrears (Arrearage) | 2026-05-08 | ALL (qvq-plus, qwen-turbo, deepseek-v3.2, etc.) | Recharge at Aliyun console |

## Exhausted Models (Deleted from config)

| # | Model | Provider | Exhausted At | Replaced By |
|---|-------|----------|-------------|-------------|
| 1 | qwen3.6-flash | dashscope | 2026-04-30 16:40 UTC | qwq-plus |
| 2 | qwq-plus | dashscope | 2026-04-30 17:20 UTC | qwen3.5-flash |
| 3 | qwen3.5-flash | dashscope | 2026-04-30 17:25 UTC | qwen-flash |

## DashScope Failure Signal Patterns

### Pattern 1: Quota Exhaustion (HTTP 401)

Individual model's free tier exhausted:

```
⚠️  API call failed (attempt 1/3): AuthenticationError [HTTP 401]
   🔌 Provider: alibaba  Model: <model-name>
   🌐 Endpoint: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
   📝 Error: HTTP 401: Incorrect API key provided.
   📋 Details: {'message': 'Incorrect API key provided...', 'type': 'invalid_request_error',
         'code': 'invalid_api_key'}
```

Cached in auth.json as:
```json
"last_error_reason": "AllocationQuota.FreeTierOnly",
"last_error_code": 403
```

### Pattern 2: Account Arrears (HTTP 400)

Entire account overdue — ALL models fail:

```
⚠️  API call failed (attempt 1/3): BadRequestError [HTTP 400]
   🔌 Provider: custom  Model: deepseek-v4-flash
   🌐 Endpoint: https://dashscope.aliyuncs.com/compatible-mode/v1
   📝 Error: HTTP 400: Access denied, please make sure your account is in good standing.
   📋 Details: {'message': 'Access denied...', 'type': 'Arrearage', 'code': 'Arrearage'}
```

### How to distinguish

- **Real API key misconfiguration**: persistent 401 on ALL models through the same provider
- **Quota exhaustion**: 401 on one model, same API key works for a different model
- **Account arrears**: 400 Arrearage on ALL models, same error every time

## Switching Protocol (Verified by User)

When the user reports a model is exhausted or a provider is down:

1. **Identify signal type**:
   - HTTP 401 + `invalid_api_key` → individual model exhaustion
   - HTTP 400 + `Arrearage` → provider-wide failure

2. **For individual exhaustion**:
   - Update config.yaml ALL THREE locations: `model.default`, `fallback_model`, `providers.<provider>.model`
   - Reset credential pool: `hermes auth reset <provider>`

3. **For provider-wide failure**:
   - Remove ALL the provider's models from fallback chain
   - Switch `model.provider` to an alternative (e.g. xiaomi, deepseek)
   - Mark provider as "欠费停用" in report file (not "已耗尽")

4. **Always**:
   - Update memory with new ladder state
   - Update SOUL.md
   - Verify config: `hermes config` + `hermes fallback list`
   - Clean-env verification before telling user
   - Tell user to start a new session
