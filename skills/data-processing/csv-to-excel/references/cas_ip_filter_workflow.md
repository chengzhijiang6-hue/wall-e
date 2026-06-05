# CAS IP Filter 合并工作流

## 场景
从 CAS（网络防火墙设备，非 Central Authentication Service）查询 server IP 流量信息，导出为 CSV，合并为多 Sheet Excel。

## 文件格式
- **分号分隔**的 CSV，28列
- 字段：ID; Location Type; Firewall; Rule Number; SrcSubnetType; SrcIP; SrcFQDN; SrcSL; SrcSZ; SrcDevice; SrcType; SrcDeviceDescription; DestSubnetType; DestIP; DestFQDN; DestSL; DestSZ; DestDevice; DestType; DestDeviceDescription; Protocol; DestPort; ICMP Type; Service; Application; Action; Latest Connection; Hits
- **DestPort**（不是Port）、**Action 值：Allowed/Blocked**

## 合并逻辑
1. 读取两个 CSV（IP as Source + IP as Destination）
2. 增加 "Direction" 列：Source → `Outbound`，Destination → `Inbound`
3. 合并连接明细到 Sheet 1
4. 按目标IP汇总（Sheet 2，汇总全部数据）
5. 按源IP汇总（Sheet 3，汇总全部数据）
6. 按防火墙汇总（Sheet 4）
7. 按协议服务汇总（Sheet 5，复合键 `protocol/service`）

## 输出
- 文件名：`CAS_Connection_Table_{IP}_{YYYYMMDD_HHMMSS}.xlsx`（带时间戳防覆盖失败）
- 存放：`work\server-migration\{device-ip}\CAS IP Filter\merged\`

## 样式
- 表头：蓝底白字加粗（`4472C4`）
- Allowed：绿色标记（`C6EFCE`）
- Blocked：红色标记（`FFC7CE`）
- 隔行着色（`D9E2F3`）、自动列宽、冻结首行
- 多值字段自动换行 + 行高自适应

## 汇总Sheet字段规范
| 列 | 说明 |
|----|------|
| 维度键 | 目标IP/源IP/防火墙/协议服务 |
| 连接数 | 该分组记录数 |
| 协议 | 去重，`\n`分隔 |
| 端口 | 去重，`\n`分隔 |
| 服务 | 去重，`\n`分隔 |
| 动作 | 去重，`\n`分隔 |
| 总命中次数 | Hits 求和，int转换 |
| 相关IP示例 | top 5，`\n`分隔 |

排序：按总命中次数降序
