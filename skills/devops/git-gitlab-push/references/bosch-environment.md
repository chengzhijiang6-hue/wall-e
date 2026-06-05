# Bosch 内网环境模式

## GitLab

- 地址: `code.exaas.bosch.com`
- 用户名: `cze8wx`
- 邮箱: `cze8wx@bosch.com`
- 仓库格式: `https://code.exaas.bosch.com/cze8wx/<repo-name>.git`

## 网络代理

- 代理地址: `http://10.197.216.7:3128`
- SSL 解密: 是（企业代理会解密 HTTPS）
- 必须配置: `git config http.proxy http://10.197.216.7:3128`

## 常见敏感信息

| 类型 | 示例 | 处理方式 |
|------|------|----------|
| 代理 IP | `10.197.216.7:3128` | 删除或替换为占位符 |
| 内网 IP | `10.x.x.x`, `192.168.x.x` | 删除或替换 |
| 公司域名 | `bosch.com`, `apac.bosch.com`, `exaas.bosch.com` | 删除或替换 |
| API 密钥 | `sk-xxx`, `tp-xxx` | 使用环境变量 |
| 数据库密码 | `mem0_secure_2026` 等 | 使用环境变量 |

## Docker 部署注意事项

- Dockerfile 中的代理配置只在构建时需要，提交前必须删除
- docker-compose.yaml 中的密码使用 `${环境变量}` 格式
- 提供 `.env.example` 文件说明配置方式
