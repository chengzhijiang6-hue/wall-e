# 工作空间 ws-qsbffqni4evhxj2h 的 DashScope 查询记录

查询日期: 2026-04-30

## 凭证

- DashScope API Key: `sk-2fd8a76c640649049bf39842bef0bdf6`（推理+配额查询权限）
- Aliyun RAM AccessKey ID: `LTAI5t99pcJcPmqx7yyDwPyn`（无 Billing 权限）
- Aliyun RAM AccessKey Secret: 已脱敏

## 查询结果

### 可用模型总数

通过 `/api/v1/models` 查询到 **481 个可用模型**。

### 核心语言模型配额

| 模型 | 请求配额 | Token 配额 |
|------|---------|-----------|
| qwen3.6-plus | 500次/天 | 2,500,000 tokens/30天 |
| qwen3.6-flash | 3,000次/6小时 | 10,000,000 tokens/60天 |
| qwen3.5-plus | 500次/天 | 2,500,000 tokens/30天 |
| qwen3.5-flash | 500次/天 | 10,000,000 tokens/60天 |
| deepseek-v4-flash | 750次/3天 | 600,000 tokens/30天 |
| deepseek-v4-pro | 750次/3天 | 200,000 tokens/10天 |
| qwen-plus | 15,000次/30天 | 2,500,000 tokens/30天 |
| qwen-turbo | 300次/15天 | 1,000,000 tokens/12天 |
| qwen-flash | 15,000次/30天 | 5,000,000 tokens/30天 |
| qwen-max | 300次/15天 | 100,000 tokens/6天 |

### 失败的查询尝试

- DashScope `/api/v1/usage/*` 等 10+ 个端点 → 全部 404
- Aliyun Billing API `QueryResourcePackageInstances` → NotAuthorized
- Aliyun Billing API `QueryInstanceBill` → NotAuthorized
- Bailian OpenAPI 全部已知版本/Action → InvalidVersion 或 InvalidAction.NotFound
