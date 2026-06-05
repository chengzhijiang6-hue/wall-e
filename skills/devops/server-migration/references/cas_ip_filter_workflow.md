# CAS IP Filter 数据整合工作流

CAS（网络防火墙）连接表数据的收集、整理和分析流程。

## 数据来源

CAS 防火墙导出的 CSV 文件，使用分号 `;` 分隔。文件命名模式：
```
Connection Table - <IP> - IP as Destination - <timestamp>.csv
Connection Table - <IP> - IP as Source - <timestamp>.csv
```

- **IP as Destination**：入站连接（目标 IP 为该设备）
- **IP as Source**：出站连接（源 IP 为该设备）

## 字段格式（0-based 索引）

| 索引 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 0 | ID | 文本 | 连接唯一标识 |
| 1 | Location Type | 文本 | Central / Remote |
| 2 | Firewall | 文本 | 防火墙名称 |
| 3 | Rule Number | 文本 | 防火墙规则编号 |
| 4 | SrcSubnetType | 文本 | Management / Server / Manufacturing 等 |
| 5 | SrcIP | 文本 | 源 IP 地址 |
| 6 | SrcFQDN | 文本 | 源 FQDN |
| 7 | SrcSL | 文本 | 源安全级别 |
| 8 | SrcSZ | 文本 | 源安全域 |
| 9 | SrcDevice | 文本 | 源设备名 |
| 10 | SrcType | 文本 | 源设备类型 |
| 11 | SrcDeviceDescription | 文本 | 源设备描述 |
| 12 | DestSubnetType | 文本 | 目标子网类型 |
| 13 | DestIP | 文本 | 目标 IP 地址 |
| 14 | DestFQDN | 文本 | 目标 FQDN |
| 15 | DestSL | 文本 | 目标安全级别 |
| 16 | DestSZ | 文本 | 目标安全域 |
| 17 | DestDevice | 文本 | 目标设备名 |
| 18 | DestType | 文本 | 目标设备类型 |
| 19 | DestDeviceDescription | 文本 | 目标设备描述 |
| 20 | Protocol | 文本 | TCP / UDP |
| 21 | DestPort | **数字** | 目标端口号 |
| 22 | ICMP Type | 文本 | ICMP 类型（如有） |
| 23 | Service | 文本 | 服务名称（ssh, ldap 等） |
| 24 | Application | 文本 | 应用名称 |
| 25 | Action | 文本 | Allowed / Blocked / Teardown |
| 26 | Latest Connection | 文本 | 最近连接时间 |
| 27 | Hits | **数字** | 命中次数 |

**注意**：DestPort(21) 和 Hits(27) 是数字列，排序时需确保为数字格式（不是文本），否则会出现 "10" 排在 "2" 后面的问题。

## 目录结构

```
server-migration/
└── <DEVICE_IP>/
    ├── *.csv                          # 用户可能直接放在根目录
    └── CAS IP Filter/
        ├── raw/          # 原始 CSV 文件（规范路径）
        └── merged/       # 整合后的 Excel 报告
```

**文件位置约定**：CSV 可能在 `<DEVICE_IP>/` 根目录或 `<DEVICE_IP>/CAS IP Filter/raw/`。两种都需支持，处理完后建议用户移入 `CAS IP Filter/raw/`。

## 两条工作路径

根据用户请求的深度，选择不同路径：

### 路径 A：快速 Markdown 汇总

用户轻量请求时使用（"整理表格"、"看看有什么连接"、"分析下这个 CSV"）。直接在终端输出，不生成 Excel。

步骤：
1. 读取两个 CSV 文件（Destination + Source）
2. 合并所有记录，标记方向（inbound/outbound）
3. **按功能分类**（见下方分类规则）
4. 输出结构化 Markdown 报告：
   - 功能分类汇总表
   - 各分类详情（按命中次数降序）
   - 高流量 Top10
   - 目标端口汇总（去重）
   - 防火墙规则统计
5. 保存 `.md` 文件到设备目录

### 路径 B：完整 Excel 合并（模式B 多维度汇总）

用户需要正式报告时使用（"合并成 Excel"、"生成报告"）。

必需 Sheet：
1. **连接明细** — 全字段 + Direction 列
2. **按目标IP汇总** — 目标IP、连接数、协议、端口、服务、动作、总命中次数、相关IP
3. **按源IP汇总** — 同上结构
4. **按防火墙汇总** — 同上结构
5. **按协议服务汇总** — 协议/服务组合、连接数、端口、动作、总命中次数、连接示例

汇总 Sheet 按总命中次数降序排列。多值字段用 `\n` 连接，设置 `wrap_text=True`。

### 后处理（路径B必须）

**自动筛选**：所有 Sheet 启用 `auto_filter.ref`。

**数据格式**：
- DestPort、Hits、连接数、总命中次数 → 数字格式（`number_format = '0'`）
- IP 地址、协议、服务、设备名、动作 → 文本格式（`number_format = '@'`）

```python
def is_numeric_column(values):
    non_empty = [v for v in values if v is not None and str(v).strip() != '']
    if not non_empty:
        return False
    numeric_count = sum(1 for v in non_empty if is_numeric_value(v))
    return numeric_count / len(non_empty) > 0.8
```

阈值 80%：如果一列超过 80% 的非空值是数字，则整列设为数字格式。

### 保存（路径B）

输出路径：`<IP>/CAS IP Filter/merged/CAS_Connection_Table_<IP>_<timestamp>.xlsx`

如果原文件被占用（存在 `~$` 临时文件），创建带新时间戳的文件，不覆盖。

## 功能分类规则

按业务功能分类比按 IP/端口分类更有迁移价值。分类按优先级从高到低匹配，一旦命中即停止。

| 优先级 | 分类 | 匹配规则 |
|--------|------|---------|
| 1 | Active Directory | 端口 389/88/3268，或服务含 ldap/kerberos，或应用含 gc |
| 2 | AGV 小车 | 设备名或 FQDN 含 "agv"，或端口 19204/19206/19301 |
| 3 | PLC/工业设备 | 应用含 mbap/rtsserv/ohimsrv/custix，或设备类型 Industrial Equipment，或服务 Modbus |
| 4 | SSH 管理 | 端口 22，或服务 ssh |
| 5 | 邮件 | 端口 25/587，或服务 smtp/submission |
| 6 | 其他 | 以上均不匹配 |

**AD 分类输出要求**：按目标域控制器分组，展示每个域控的 LDAP(389)/Kerberos(88)/GC(3268) 命中数，区分 TCP/UDP。

**AGV 分类输出要求**：按 AGV 设备分组，展示端口和命中数。AGV 端口 19204 通常是主通信端口，流量远高于其他端口。

**PLC 分类输出要求**：按 PLC 设备分组，展示端口、协议（Modbus/rtsserv 等）和命中数。

## 与 csv-to-excel 技能的关系

路径B 使用 csv-to-excel 技能的 **模式B（多维度汇总）**。样式、格式化函数、后处理逻辑均来自 csv-to-excel 技能。

## 典型统计输出示例

```
总连接数: 96
入站连接: 15
出站连接: 81

按功能分类:
  Active Directory:  40 条 (14个域控)
  AGV 小车:          24 条 (6台 AGV)
  PLC/工业设备:      13 条 (10台 PLC)
  SSH 管理:           3 条
  邮件:               2 条
  其他:              14 条

总命中次数: 1,742,502
```

## Pitfalls

### 分号分隔符
CAS 导出的 CSV 使用 `;` 分隔而非 `,`。解析时必须指定 `delimiter=';'`。

### Hits 列非数字
部分行的 Hits 可能为空或含非数字字符。解析时需 `isdigit()` 检查，默认值 0。

### Teardown 行
Action 为 `Teardown` 的记录与 `Allowed` 记录可能是同一连接的不同状态。同一目标IP+端口可能出现两条记录（Allowed + Teardown），统计时两条都应计入。

### DNS 不可解析
部分 SrcFQDN 为 "Not resolvable by DNS"，这是正常的（工业设备通常无 DNS 记录）。FQDN 为 N/A 时显示 "DNS不可解析"。
