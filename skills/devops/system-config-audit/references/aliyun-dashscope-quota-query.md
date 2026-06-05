# Aliyun DashScope / Bailian 模型配额与用量查询

## 数据源层级

要查询 Aliyun DashScope（百炼）平台上模型的可用模型、配额上限和实际用量，需要从三个层级获取数据：

| 层级 | 认证方式 | 可获取数据 | 局限性 |
|------|---------|-----------|--------|
| **DashScope REST API** | Bearer token (`sk-*`) | 模型列表、价格、配额上限（limits） | **无实际已消耗量** |
| **Aliyun Billing API (BssOpenApi)** | RAM AccessKey (AK/SK) | 资源包用量、账单明细 | 免费额度用量不在此追踪 |
| **百炼控制台 UI** | 浏览器登录 Cookie/STS | 完整数据：配额 + 已用量 + 剩余 | 不可编程调用 |

## 方案1: DashScope REST API (Bearer token)

### 列模型

```bash
curl -s -H "Authorization: Bearer <sk-xxx>" \
  "https://dashscope.aliyuncs.com/api/v1/models?page_size=100&page_no=1"
```

返回：`total`, `models[]` 含 `model`, `name`, `description`, `features`, `prices`, `provider`, `capabilities`, `model_info`

### 查配额上限

```bash
curl -s -H "Authorization: Bearer <sk-xxx>" \
  "https://dashscope.aliyuncs.com/api/v1/quotas?page_size=100"
```

返回：`quotas[]` 含 `model`, `workspace_id`, `model_limit`:
- `request_limit` — 周期内允许的最大请求数
- `request_limit_period` — 周期（天/小时）
- `usage_limit` — 周期内允许的最大 token 数
- `usage_limit_field` — 度量单位（total_tokens）
- `usage_limit_period` — 周期天数
- `async_user_queue_limit` / `async_user_concurrency_limit` — 异步任务限制

**注意**: 此 API 返回的只是配额上限（max allowed），不包含实际已消耗量。

### 探针：所有 `/api/v1/*` 端点均返回 404

已测试不存在的端点（2026-04 验证）：
- `/api/v1/usage`, `/api/v1/usage/statistics`, `/api/v1/usage/monthly`
- `/api/v1/statistics/*`, `/api/v1/dashboard/*`
- `/api/v1/billing/*`
- `/api/v1/user/*`
- `/api/v1/workspace/*`

结论：DashScope REST API 不暴露实际用量统计。

## 方案2: Aliyun Billing API (RAM AK/SK)

### 前置条件

RAM AccessKey 需要 `AliyunBSSReadOnlyAccess` 权限，或至少：
```json
{
  "Action": [
    "bss:QueryResourcePackageInstances",
    "bss:QueryInstanceBill",
    "bss:QueryBillOverview",
    "bss:DescribeInstanceBill"
  ],
  "Resource": "*",
  "Effect": "Allow"
}
```

### 查询资源包用量

```python
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

client = AcsClient(ak_id, ak_secret, region)
request = CommonRequest()
request.set_domain("business.aliyuncs.com")
request.set_version("2017-12-14")
request.set_action_name("QueryResourcePackageInstances")
request.set_method("POST")
request.add_query_param("PageSize", 50)
request.add_query_param("PageNum", 1)

response = client.do_action_with_exception(request)
```

**注意**: 此 API 只返回购买的资源包/节省计划。DashScope 的免费用量不属于资源包，所以即使有免费额度也返回空列表。

### 查询实例账单

```python
request.set_action_name("QueryInstanceBill")
request.add_query_param("BillingCycle", "2026-04")
request.add_query_param("ProductCode", "dashscope")
```

DashScope 的免费额度使用不产生账单，所以账单数据为空（除非已超过免费额度产生后付费）。

### 账户信息

可从 `QueryInstanceBill` 响应中提取：
- `AccountID` — 阿里云账号 ID
- `AccountName` — 注册名（如"橙沚超好撩"）
- `BillingCycle` — 账单周期

### 已知的 DashScope 相关 ProductCode

- `dashscope` — 百炼/DashScope 服务
- 其他可能相关的代码未经验证

## 方案3: 百炼控制台 UI（不可编程）

控制台 URL：`https://bailian.console.aliyun.com/?tab=model#/model-usage`

需要浏览器登录，然后手动复制页面数据。页面数据格式（TSV）：
```
模型Code\t
免费额度剩余量
过期时间
状态
操作
```

每个模型占 5 行：模型名、`剩X,XXX/共X,XXX,XXX`、`YYYY/MM/DD`、`已开启`/`未开启`、操作按钮文本。

## 数据整合方法

完整的用量报告需要将方案1（配额上限）与方案3（实际剩余量）的数据合并：

1. 从 API 获取 `model_limit`（请求数/Token 配额上限）
2. 从控制台获取 `剩余/总量` 字段（免费用量的实际消耗）
3. 计算：已用量 = 总量 - 剩余量
4. 获取模型价格（从 models API 的 prices[] 字段）

## Qwen API Key 的结构

- DashScope API Key: `sk-2fd8a76c640649049bf39842bef0bdf6` 格式
- OpenAI 兼容端点: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 模型名称直接用 API 中的 model code（如 `qwen3.6-flash`）
- 每个 API Key 绑定一个 workspace（如 `ws-qsbffqni4evhxj2h`）

## 本用户环境

- 账户名: 橙沚超好撩
- 账户 ID: 1255619316571427
- 工作空间: ws-qsbffqni4evhxj2h
- AI 模型总数: 481（API 返回），185（控制台页面，仅语言模型）
- 免费用量: 大部分模型 1,000,000 tokens/月
- 已使用模型: qwen3.6-plus (95.3%)、qwen3-235b-a22b (8.7%)
- DeepSeek v4 在百炼中处于"未开启"状态
