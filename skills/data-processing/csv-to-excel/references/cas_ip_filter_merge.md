# CAS IP Filter 流量合并参考

## 场景
从 CAS（网络防火墙设备）查询服务器 IP 流量信息，导出两个 CSV：
- IP as Source（出站流量）— 文件名含 "IP as Source"
- IP as Destination（入站流量）— 文件名含 "IP as Destination"

合并为单一 Excel，增加"Direction"列区分来源。

## 数据特征
- **分号分隔**的 CSV（不是逗号）
- 两个文件字段结构完全相同（28列）
- 关键字段：Firewall, SrcIP, SrcFQDN, DestIP, DestFQDN, Protocol, **DestPort**（不是Port）, Service, Application, **Action**, Latest Connection, **Hits**
- **Action 实际值**：`Allowed` / `Blocked`（不是 Allowed/Timeout/Denied）
- Hits 字段为字符串，需 `try/except` 转 int，非数字值忽略

## 字段参考（完整28列）
```
ID; Location Type; Firewall; Rule Number; SrcSubnetType; SrcIP; SrcFQDN; SrcSL; SrcSZ;
SrcDevice; SrcType; SrcDeviceDescription; DestSubnetType; DestIP; DestFQDN; DestSL;
DestSZ; DestDevice; DestType; DestDeviceDescription; Protocol; DestPort; ICMP Type;
Service; Application; Action; Latest Connection; Hits
```

## 合并策略

### Sheet 1: 连接明细
- 合并两个文件所有记录
- 增加"Direction"列：IP as Source → `Outbound`，IP as Destination → `Inbound`
- 动作颜色：Allowed → 绿色 `C6EFCE`，Blocked → 红色 `FFC7CE`

### Sheet 2: 按目标IP汇总
- 汇总所有数据（入站+出站），不分方向
- 维度：目标IP → 连接数、协议、端口、服务、动作、总命中次数、相关IP示例
- 按总命中次数降序

### Sheet 3: 按源IP汇总
- 汇总所有数据，不分方向
- 维度：源IP → 同上

### Sheet 4: 按防火墙汇总
- 维度：防火墙名 → 连接数、协议、端口、服务、动作、总命中次数

### Sheet 5: 按协议服务汇总
- **复合键**：`f"{protocol}/{service}"` （如 `TCP/ssh`）
- 维度：协议/服务 → 连接数、端口、动作、总命中次数、连接示例

## 汇总Sheet字段模式
```
[维度键, 连接数, 协议, 端口, 服务, 动作, 总命中次数, 相关IP示例]
```
- 多值字段用 `\n` 连接，单元格设置 `wrap_text=True`
- 相关IP示例取 top 5，用 `\n` 分隔
- 按总命中次数降序排列

## 文件命名
- 模式：`CAS_Connection_Table_{IP}_{YYYYMMDD_HHMMSS}.xlsx`
- 带时间戳避免文件被占用时写入失败（Excel打开时无法覆盖）
- 存放：`work\server-migration\{device-ip}\CAS IP Filter\merged\`

## 常见陷阱
1. **分隔符**：CAS 导出用分号 `;`，不是逗号
2. **字段名 DestPort**：不是 "Port"，提取端口时用 `row.get('DestPort', '')`
3. **Action 值**：实际数据是 `Allowed`/`Blocked`，不是 `Allowed`/`Timeout`/`Denied`
4. **Hits 转换**：用 `try/except ValueError` 防护，空值和非数字值跳过
5. **方向列位置**：添加到 headers 末尾，不影响原有字段索引
6. **openpyxl 环境**：WSL 路径 `/mnt/c/wsl/hermes_official/venv/bin/pip install openpyxl`
