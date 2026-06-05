# Bosch 代理拦截的域名清单

Bosch 公司代理（`10.197.216.7:3128`）对部分外网域名实施访问限制（Access Restricted），需通过 OneIDM 申请 `Extended Internet Web Access` 相关 IT 角色才能解封。

## 已知被封域名

| 域名 | 用途 | 拦截现象 | 解封所需角色 |
|------|------|---------|------------|
| `ilinkai.weixin.qq.com` | 微信 iLink Bot API（Hermes WeChat 集成） | `Access Restricted` 页面，返回 HTML 含角色缺失列表 | `Extended Internet Web Access File Sharing` 等 |
| 其他待补充 | | | |

## 验证方法

在配置任何外部平台集成前，先测试目标 API 是否可达：

```bash
curl -sk --proxy http://10.197.216.7:3128 "https://<target-domain>/" 2>&1 | grep -i "Access Restricted\|denied\|forbidden"
```

- 若返回 `Access Restricted` — 被代理拦截，需申请 IT 角色
- 若返回正常页面/JSON — 可正常访问

## 申请流程

1. 打开 Bosch OneIDM
2. 申请 `Extended Internet Web Access` 相关角色
3. 参考：https://inside-docupedia.bosch.com/confluence/x/JmwALg

## 重要提示

- 微信 WeChat 集成（iLink Bot API）在解封之前完全不可用
- Teams 集成需要公网 HTTPS 端点，与代理拦截是**不同维度的限制**（网络策略 vs 端口暴露）
- 企业微信（WeCom）使用不同的 API 域名，需单独测试是否被封
