---
name: aliyun-dashscope-api
category: devops
description: Query Aliyun DashScope (百炼) models, quotas, and pricing via REST API and Aliyun OpenAPI SDK. Authentication patterns, endpoint mapping, and permission boundaries.
---

# Aliyun DashScope API 查询指南

查询阿里云百炼（DashScope）的模型列表、配额、定价等信息。

## 认证方式

### 方式 1：DashScope API Key（Bearer Token）

```
Authentication: Bearer sk-xxxxxxxxxxxxxxx
Base URL: https://dashscope.aliyuncs.com
```

- 以 `sk-` 开头
- 用于**推理调用**和**部分管理 API**（模型列表、配额查询）
- 不可用于账单/用量统计 API

### 方式 2：Aliyun RAM AccessKey（OpenAPI Signing）

```
AccessKey ID: LTAI5txxxxxxxxxxxx
AccessKey Secret: xxxxxxxxxxxxxxxxx
```

- 通过 Aliyun OpenAPI SDK（`aliyun-python-sdk-core`）调用
- 需要绑定对应的 RAM 策略权限
- 可用于：Billing API（需 `AliyunBSSReadOnlyAccess`）、Bailian OpenAPI 等

## 可用的 DashScope REST API

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/v1/models` | GET | 模型列表（含定价、能力标签） | Bearer token |
| `/api/v1/models?page_size=100` | GET | 模型列表（分页） | Bearer token |
| `/api/v1/quotas` | GET/POST | 配额上限（请求数、Token 数/时间周期） | Bearer token |
| `/api/v1/quotas?page_size=100` | GET/POST | 配额上限（分页） | Bearer token |

### 模型列表返回示例

每个模型返回：`model`（ID）、`name`（显示名）、`provider`（供应商）、`prices`（定价）、`features`（能力标签）、`model_info`（上下文窗口等）、`capabilities`（TG/Reasoning/VU 等）

`features` 中的 `model-experience` 标签表示该模型有"模型体验"免费额度。

### 配额返回示例

每个模型返回：`model_limit.request_limit`（请求次数上限）、`request_limit_period`（周期天数/小时数）、`usage_limit`（Token 上限）、`usage_limit_field`（计量维度，如 `total_tokens`）、`usage_limit_period`（周期天数）

**注意**：`/api/v1/quotas` 仅返回**配额上限**，不返回**实际已用量**。无 `used` / `consumed` / `remaining` 字段。

## 不可用的端点

以下端点均返回 HTTP 404，DashScope **未公开**用量统计 REST API：

```
GET/POST /api/v1/usage/statistics        → 404
GET/POST /api/v1/usage/detail            → 404
GET/POST /api/v1/usage/monthly           → 404
GET/POST /api/v1/statistics/usage        → 404
GET/POST /api/v1/billing/*               → 404
GET/POST /api/v1/user/*                  → 404
GET/POST /api/v1/dashboard/*             → 404
GET/POST /api/v1/workspace/*             → 404
GET/POST /api/v1/service/*               → 404
```

## Aliyun OpenAPI（SDK 方式）

### 安装

```bash
pip install aliyun-python-sdk-core --proxy http://<proxy>:3128
```

### SDK 调用模板

```python
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import json

client = AcsClient(ak_id, ak_secret, region)

request = CommonRequest()
request.set_domain("business.aliyuncs.com")
request.set_version("2017-12-14")
request.set_action_name("QueryResourcePackageInstances")
request.set_method("POST")
request.set_protocol_type("https")
request.add_query_param("PageSize", 50)
request.add_query_param("PageNum", 1)

response = client.do_action_with_exception(request)
data = json.loads(response)
```

### 已知可用的 Aliyun OpenAPI

| 域 | API 版本 | Action | 说明 | 所需权限 |
|----|----------|--------|------|----------|
| `business.aliyuncs.com` | `2017-12-14` | `QueryResourcePackageInstances` | 查询资源包实例及用量 | `AliyunBSSReadOnlyAccess` |
| `business.aliyuncs.com` | `2017-12-14` | `QueryInstanceBill` | 查询实例账单 | `AliyunBSSReadOnlyAccess` |
| `business.aliyuncs.com` | `2017-12-14` | `QueryBillOverview` | 查询账单总览 | `AliyunBSSReadOnlyAccess` |

### Bailian OpenAPI

`bailian.cn-beijing.aliyuncs.com` 的所有已知 API 版本（`2023-01-01` 至 `2025-06-01`）和 Action 均返回 **InvalidVersion** 或 **InvalidAction.NotFound**。Bailian 产品目前无公开的 OpenAPI。

## 权限模型

```
API Key (sk-*)
  ├── /api/v1/models        ✅ 模型列表
  ├── /api/v1/quotas        ✅ 配额上限
  ├── /api/v1/services/...  ✅ 模型推理
  └── /api/v1/usage/*       ❌ 无权限

RAM AccessKey (LTAI5t...)
  ├── Billing API           ✅ 需 AliyunBSSReadOnlyAccess
  ├── Bailian OpenAPI       ❌ 不支持
  └── RAM/STS API           ✅ 需对应 RAM 权限
```

## 实际用量查询

DashScope 的**实际消耗量**（已用 Token/请求数）目前**仅能通过百炼控制台网页 UI**（`https://bailian.console.aliyun.com/#/model-usage`）查看，需浏览器登录。没有公开的 API 可以程序化查询。

## 模型耗尽信号（关键）

DashScope 在模型额度耗尽时返回 **HTTP 401**（不是 429 限流），错误信息：

```json
HTTP 401: Incorrect API key provided.
Details: {
  'message': 'Incorrect API key provided.',
  'type': 'invalid_request_error',
  'code': 'invalid_api_key'
}
```

同时凭据池（`auth.json`）会缓存 `last_status: exhausted` 状态：

```json
"last_status": "exhausted",
"last_error_code": 403,
"last_error_reason": "AllocationQuota.FreeTierOnly",
"last_error_message": "The free tier of the model has been exhausted..."
```

**后果**：即使切换到同一供应商（dashscope）下的不同模型，缓存的 exhausted 状态会导致 Hermes 跳过该供应商直接走 fallback。

**修复**：切换模型后必须执行：
```bash
hermes auth reset dashscope
```

**注意**：说它是"耗尽"而不是"API Key 错误"的判断依据是：
1. 之前该 API Key 正常工作
2. DashScope 的 free tier 用完会返回 401 作为语义信号
3. 错误信息指向配额相关文档而非认证问题

### ⚠️ 账户欠费信号（HTTP 400 Arrearage）

DashScope 在账户余额不足、处于欠费状态时返回 **HTTP 400**（区别于配额耗尽的 HTTP 401）：

```
HTTP 400: Access denied, please make sure your account is in good standing.
Details: {
  'message': 'Access denied, please make sure your account is in good standing...',
  'type': 'Arrearage',
  'param': None,
  'code': 'Arrearage'
}
```

**与 HTTP 401 配额耗尽的区别**：

| 特征 | HTTP 401 配额耗尽 | HTTP 400 账户欠费 |
|------|------------------|------------------|
| 错误码 | `invalid_api_key` | `Arrearage` |
| 影响范围 | 单个模型 | 整个 provider（所有模型） |
| 恢复方式 | 切换到同 provider 下的其他模型 + auth reset | 阿里云百炼控制台充值 |
| 配置影响 | 删除耗尽的模型，保留 provider | 删除整个 provider，切换到其他提供商 |
| 凭据池缓存 | `AllocationQuota.FreeTierOnly` (403) | 无缓存（400 非重试错误直接触发 fallback） |

**恢复步骤**：
1. 登录阿里云百炼控制台：https://model-studio.aliyun.com/
2. 充值后等待账户状态恢复
3. 执行 `hermes auth reset dashscope` 清除凭据池缓存
4. 重新启用 dashscope provider 的模型配置

### ⚠️ API Key 环境变量命名约定

Hermes Agent 注册表中（`auth.py:271`）DashScope 的标准环境变量名是 **`DASHSCOPE_API_KEY`**，而非 `QIANWEN_API_KEY`。虽然在 `config.yaml` 的 `providers` 段中可以用 `${QIANWEN_API_KEY}` 引用自定义变量名，但以下场景直接读取 `DASHSCOPE_API_KEY`：

- `hermes config check` — 诊断报告
- `hermes doctor` — 环境检查

**最佳实践**：在 `.env` 中同时设置：
```env
DASHSCOPE_API_KEY=sk-xxx     # 标准名称（Hermes 工具识别）
QIANWEN_API_KEY=sk-xxx       # 自定义名称（config.yaml 展开用）
```

### ⚠️ 端点差异：国内站 vs 国际站

| 站点 | base_url |
|------|----------|
| **国内站** | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| **国际站** | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |

Hermes 注册表中的默认端点是国际站。如果通过公司网络在中国大陆使用，国内站的延迟更低。

### ⚠️ DashScope 兼容端点不支持 DeepSeek 模型

DashScope 的 OpenAI 兼容端点（`dashscope.aliyuncs.com/compatible-mode/v1`）**只识别 DashScope 自身的模型 ID**（如 `qwen-turbo`、`qwen-plus`、`qvq-plus`）。

如果在 Hermes 的 `fallback_model` 中配置 `provider: dashscope` 配合 `model: deepseek-v3.2`，当回退执行到该条目时，DashScope 端点会返回 404/400 错误，导致整个回退链中断。

正确做法：DeepSeek 模型必须通过 `deepseek` provider 调用。

在代理环境下通过 Hermes Agent 访问 DashScope 时，代理环境变量必须放入 `~/.hermes/.env`：
```env
HTTP_PROXY=http://10.197.216.7:3128
HTTPS_PROXY=http://10.197.216.7:3128
http_proxy=http://10.197.216.7:3128
https_proxy=http://10.197.216.7:3128
```

Hermes 启动时通过 `python-dotenv` 自动加载 `.env`，`httpx`（Hermes 底层 HTTP 客户端）会识别 `HTTP_PROXY` 环境变量。

**重要**：仅在 `.bashrc` 中设置代理是不够的 — 仅适用于 interactive bash shell。Hermes 从 cron、桌面快捷方式、env-clean 子进程等非 bash 上下文启动时，`.bashrc` 中的代理变量不会被继承。

**验证**：
```bash
# 测试代理到 DashScope 端点连通性
curl -x http://10.197.216.7:3128 -sS -o /dev/null -w "%{http_code}" \
  https://dashscope.aliyuncs.com/compatible-mode/v1
# 期望: 404（说明代理可达，只是 hit 了 base URL）

python3 -c "
import requests
r = requests.get('https://dashscope.aliyuncs.com/compatible-mode/v1',
    proxies={'http': 'http://10.197.216.7:3128', 'https': 'http://10.197.216.7:3128'},
    timeout=10)
print(r.status_code)
"
# 期望: 404
```

## 常用 curl 命令

```bash
# 模型列表
curl -H "Authorization: Bearer sk-xxx" \
  "https://dashscope.aliyuncs.com/api/v1/models?page_size=100"

# 配额上限
curl -H "Authorization: Bearer sk-xxx" \
  "https://dashscope.aliyuncs.com/api/v1/quotas?page_size=200"
```
