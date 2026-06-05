---
name: oracle-view-troubleshoot
description: Oracle 视图/物化视图失效排查与修复 — LOM Dashboard 系统专用
category: devops
triggers:
  - 下载按钮返回空 Excel（有列名无数据）
  - Oracle ORA-00909 / ORA-00942 错误
  - 视图 VALID 但返回 0 行
  - 物化视图 NEEDS_COMPILE / INVALID
  - 数据库维护后前端数据异常
---

# Oracle 视图/物化视图失效排查与修复

## 适用场景
- 前端下载 Excel 只有列名没有数据
- 视图标记 VALID 但查询返回 0 行
- 物化视图 ORA-00909 / ORA-00942 错误
- Oracle 数据库维护/补丁后系统异常

## ⚠️ 关键陷阱（必须先读）

1. **不要假设下载按钮调用哪个接口** — 前端有多个下载功能，调用不同接口。必须通过前端代码确认实际 API。
2. **视图 VALID 但返回 0 行** — Oracle 维护后常见。`ALTER VIEW COMPILE` 可修复，不改定义。
3. **下载为空不一定是 bug** — 先验证业务数据是否存在。
4. **一次维护可能影响多个视图** — 发现一个有问题后，批量检查所有 INVALID/NEEDS_COMPILE 对象。

## 排查步骤

### 第一步：确认问题接口（关键！）

```bash
# 搜索前端代码中的下载方法
grep -r "handleDownLoad\|exportExcel\|download" src/views/ --include="*.vue"
```

追踪方法：
1. 找到页面 Vue 文件（如 `HomeCapacity.vue`）
2. 找到下载按钮的 `@click` 事件（如 `handleDownLoad(item.name)`）
3. 找到方法定义（如 `window.open('/api/wh/over-2y/export?wh=${name}')`）
4. 确认实际 API 路径

**常见混淆**：`/excel-product` 和 `/wh/over-2y/export` 是不同接口，查询不同表。

### 第二步：定位后端 SQL
找到接口后，追踪到 Controller → Mapper → SQL：

```bash
# 搜索后端代码
grep -r "接口路径" src/main/java/ --include="*.java"
```

### 第三步：检查数据库对象状态

```sql
-- 检查对象状态
SELECT OWNER, OBJECT_NAME, OBJECT_TYPE, STATUS 
FROM ALL_OBJECTS 
WHERE OBJECT_NAME = '目标对象名' 
AND OWNER = 'LOGPOE';

-- 检查是否有同名 TABLE + MATERIALIZED VIEW 冲突
SELECT OWNER, OBJECT_NAME, OBJECT_TYPE, STATUS 
FROM ALL_OBJECTS 
WHERE OBJECT_NAME = '目标对象名';
```

### 第四步：验证数据

```sql
-- 直接查询表
SELECT COUNT(*) FROM LOGPOE.底层表名;

-- 查询视图
SELECT COUNT(*) FROM LOGPOE.视图名;

-- 如果表有数据但视图返回 0，说明视图有问题
```

### 第五步：查看视图/物化视图定义

```sql
-- 查看视图定义
SELECT TEXT FROM ALL_VIEWS WHERE VIEW_NAME = '视图名' AND OWNER = 'LOGPOE';

-- 查看物化视图定义
SELECT QUERY FROM ALL_MVIEWS WHERE MVIEW_NAME = '物化视图名' AND OWNER = 'LOGPOE';

-- 查看依赖关系
SELECT REFERENCED_OWNER, REFERENCED_NAME, REFERENCED_TYPE 
FROM ALL_DEPENDENCIES 
WHERE NAME = '对象名' AND OWNER = 'LOGPOE';
```

## 常见问题与修复

### 问题1：视图 VALID 但返回 0 行
**原因**：Oracle 数据库维护后，视图编译状态异常
**修复**：
```sql
ALTER VIEW LOGPOE.视图名 COMPILE;
```

### 问题2：物化视图 ORA-00909
**原因**：SQL 中 OR 优先级问题
**错误写法**：
```sql
WHERE condition1 AND condition2 OR condition3 OR condition4
```
**正确写法**：
```sql
WHERE condition1 AND condition2 AND (condition3 OR condition4)
```
**修复**：
```sql
-- 刷新物化视图
EXEC DBMS_MVIEW.REFRESH('LOGPOE.物化视图名');
```

### 问题3：同名 TABLE 和 MATERIALIZED VIEW 冲突
**排查**：
```sql
SELECT OWNER, OBJECT_NAME, OBJECT_TYPE, STATUS 
FROM ALL_OBJECTS 
WHERE OBJECT_NAME = '对象名';
```
**处理**：确认哪个是实际使用的，删除冲突的对象

### 问题4：下载为空但不是 bug
**验证**：
```sql
-- 检查是否有符合条件的数据
SELECT COUNT(*) FROM 表名 WHERE 过滤条件;
```
如果返回 0，说明确实没有数据，下载为空是正确行为

## 批量检查脚本

```sql
-- 检查所有 INVALID 对象
SELECT OBJECT_NAME, OBJECT_TYPE, STATUS, LAST_DDL_TIME 
FROM ALL_OBJECTS 
WHERE STATUS = 'INVALID' 
AND OWNER = 'LOGPOE'
ORDER BY LAST_DDL_TIME DESC;

-- 检查 NEEDS_COMPILE 的物化视图
SELECT MVIEW_NAME, LAST_REFRESH_DATE, STALENESS, COMPILE_STATE 
FROM ALL_MVIEWS 
WHERE OWNER = 'LOGPOE' 
AND COMPILE_STATE != 'VALID';
```

## LOM Dashboard 物化视图清单 (14个)

| 物化视图名 | 刷新方式 | 用途 | 关键源表 |
|-----------|---------|------|---------|
| `LOI_MV_AUTOGR_PPU` | DEMAND/COMPLETE | GR 有/无摄像头 TO 数量 | LTAP_LTAK_POE |
| `LOI_MV_AUTORACK_PPU` | DEMAND/COMPLETE | AutoRack TO 数量 | LTAP_LTAK_POE_AR1 |
| `LOI_MV_DE_MATERIAL_FLOW` | DEMAND/COMPLETE | DE 物料流分类 | LTAP_LTAK_POE |
| `LOI_MV_OPEN_TO_DETAILS` | DEMAND/FORCE | Open TO 详情 (20+ UNION ALL) | LTAP_LTAK_POE, LTAP_LTAK_POE_OPEN_TO |
| `LOI_MV_TO_HOUR_HISTORY` | DEMAND/COMPLETE | TO 每小时历史 | FACT_MSEG_POE_HOUR, FACT_LTAP_LTAK_POE_HOUR |
| `LOI_MV_WH_CAPACITY_DETAIL_SD` | DEMAND/COMPLETE | 仓库容量明细 (AR1×2逻辑) | FACT_WH_PRODUCT_DW |
| `LOI_V_DEAD_STOCK` | - | 死库存 | LOI_MT_BLOCKED_STOCK_MEASURES |
| `LOI_V_OCCUPATION_RATE` | - | 占用率 | LOI_MT_WAREHOUSE_DEFINITION |
| `LOI_V_OVER_SHELF_LIFE` | - | 超保质期 | FACT_WH_PRODUCT_DW |
| `LOI_V_PKG_CON` | - | 包装消耗 | LOI_MAST_STPO_MARC_POE |
| `LOI_V_PKG_FG_PN_VS` | - | FG-PN 对应 | - |
| `LOI_V_PKG_REC_DEL` | - | 包装收发存 | - |
| `LOI_V_WH_CAPACITY_DETAIL` | - | 仓库容量明细 | FACT_WH_PRODUCT_DW |
| `LOI_V_WH_OVERVIEW` | - | 仓库概览 | FACT_WH_PRODUCT_DW |

## 关键源表

| 表名 | 行数 | 用途 |
|------|------|------|
| `LTAP_LTAK_POE_GI_TO` | 1,810,314 | GI Transfer Order (SAP WM) |
| `DIQ_SU_COUNT_RP_SUMMARY` | 2,517,276 | 翻包 SU 计数汇总 |
| `GR_AUTOMATION_RATE_DATA` | 554,278 | GR 自动化率源数据 |
| `LOI_MAST_STPO_MARC_POE` | 318,115 | BOM 展开 (FG→RM) |
| `LOI_V_MILKRUN_TIME_WINDOW` | 494,565 | MilkRun 时间窗 |
| `LOI_MT_WAREHOUSE_DEFINITION` | 20 | 仓库定义维度表 |

## Open TO 交通灯阈值 (LOI_V_OPEN_TO / LOI_MV_OPEN_TO_DETAILS)

排错时需了解不同业务类型的阈值差异：

| 业务类型 | OK | REMINDER | FAIL | 区域 |
|----------|-----|----------|------|------|
| DE 成品发货 | < 3h | 3-4h | > 4h | WX03 |
| DE 成品发货 | < 5h | 5-6h | > 6h | B304 |
| DE 成品发货 | < 3h | 3-4h | > 4h | B308 |
| DE 体移库 | < 5h | 5-6h | > 6h | B304 |
| GI 超市直送 | < 3h | 3-4h | > 4h | B308 |
| GI 立库下架 | < 3h | 5-6h | > 6h | B304 |
| GR 直收上架 | < 3h | 5-6h | > 6h | B304 |
| GR 翻包上架 | < 3h | 5-6h | > 6h | B304 |
| GR 包材直送 | < 3h | 5-6h | > 6h | B304 |
| GR 超市直送 | < 3h | 3-4h | > 4h | B308 |
| GR 超市直送 | < 12h | 12-14h | > 14h | B308(FCI) |
| RP 二级拉动 | < 7h | 7-8h | > 8h | B304 |
| DE 样品 | < 8h | 8-14h | > 14h | B308 |

**阈值在 2026-05-22 有变更**: DE-B304 的 FAIL 从 4h 改为 6h (REMINDER 从 3-4h 改为 5-6h)。

## 子技能

- `plms-troubleshooting` — PLMS 排错知识库（数据血缘、视图逻辑、排错手册），包含 179 个数据库对象、30+ 物化视图定义、130+ 存储过程

## 注意事项
- **`ALTER VIEW COMPILE` 不是修改**：只是让 Oracle 重新检查现有定义，不改任何内容。用户可能认为这是"修改"，需要明确解释
- `DBMS_MVIEW.REFRESH` 会重新执行查询刷新数据
- 修改物化视图定义需要 DROP + CREATE
- 修改前建议备份：`CREATE TABLE xxx_bak AS SELECT * FROM xxx`
- **一次维护可能影响多个视图**：发现一个 NEEDS_COMPILE 后，用批量检查脚本扫描所有对象
- **用户偏好**：优先使用 `ALTER ... COMPILE` 等非破坏性命令，避免 `CREATE OR REPLACE`（用户视为"修改"）
- **Oracle LONG 类型限制**：`USER_VIEWS.TEXT` 是 LONG 类型，不能用于 ORDER BY/SUBSTR/WHERE。用 `DBMS_METADATA.GET_DDL()` 替代。详见 `references/oracle-long-datatype-pitfall.md`
