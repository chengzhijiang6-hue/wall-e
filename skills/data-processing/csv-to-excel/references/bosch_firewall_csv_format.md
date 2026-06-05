# Bosch 防火墙连接表 CSV 格式参考

## 文件来源
从 Bosch 防火墙管理界面导出，文件名格式：
`Connection Table - <IP> - IP as Source|Destination - <timestamp>.csv`

## 字段结构（分号分隔）
| 字段 | 含义 | 示例 |
|------|------|------|
| ID | 连接标识 | 10.177.104.122-10.187.224.200-445-TCP |
| Location Type | 部署类型 | Central |
| Firewall | 防火墙名称 | SGP-CCS1-02-ESZ |
| Rule Number | 规则编号 | - |
| SrcSubnetType | 源子网类型 | Server |
| SrcIP | 源IP | 10.177.104.122 |
| SrcFQDN | 源FQDN | wx0vm0lop0app01.apac.bosch.com |
| SrcSL | 源安全级别 | BCN-SL3 / Undefined |
| SrcSZ | 源安全区 | BCN-SL3 / Undefined |
| DestIP | 目的IP | 10.187.224.200 |
| DestFQDN | 目的FQDN | sgpbcd63.apac.bosch.com |
| DestSZ | 目的安全区 | RSZ-SL4-0073_AD-BCD_SGP |
| Protocol | 协议 | TCP / UDP |
| DestPort | 目的端口 | 445 |
| Application | 服务/应用名 | microsoft-ds / ldap / kerberos / https |
| Action | 动作 | Allowed / Timeout / Denied |
| Latest Connection | 最新连接时间 | 2026-05-05 14:18:48.578 |
| Hits | 命中次数 | 1 |

## 常见服务/端口映射
- 88: kerberos
- 123: ntp
- 135: epmap (RPC)
- 383: hp-alarm-mgr (CEMS)
- 389: ldap
- 443: https
- 445: microsoft-ds (SMB)
- 30001: pago-services1 (reporting)

## 数据特点
- "Service" 字段通常全为 "-"，实际服务名在 "Application" 字段
- 大部分连接为 "Allowed"，少量 "Timeout" 或 "Denied"
- 同一源IP到同一目的IP可能有多个端口/协议的连接
- 建议提取关键列：防火墙、源IP、源FQDN、目的IP、目的FQDN、目的安全区、协议、端口、应用、动作、时间、命中次数
