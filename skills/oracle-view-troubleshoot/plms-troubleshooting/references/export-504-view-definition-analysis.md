# Export 504 视图定义分析

## 概述

LOI_V_LTAP_EXPORT 视图的完整定义和性能问题分析。

## 文件位置

- 完整定义: `/mnt/c/Users/CZE8WX/Desktop/knowledge/_database/LOGPOE/LOI_V_LTAP_EXPORT_view_definition.sql`
- 诊断报告: `/mnt/c/Users/CZE8WX/Desktop/knowledge/PLMS数据梳理/06_SQL参考/plms_export_504_final_report.md`
- LLM-Wiki: `wiki/concepts/plms-export-504-超时问题：cte-引发索引失效的诊断与修复.md`

## 视图结构

### CTE 定义

```sql
WITH TEMP_LTAP_LTAK_POE_DATA AS(
  SELECT 
    LGNUM AS WAREHOUSE, TANUM AS TO_NUMBER, BWART AS MOVEMENT_TYPE_IM, 
    BWLVS AS MOVEMENT_TYPE_WM, BDATU AS CREATION_DATE, BZEIT AS CREATION_TIME,
    KQUIT AS CONFIRMATION, MBLNR AS MATERIAL_DOC, TAPOS AS TO_ITEM, 
    MATNR AS MATERIAL, WERKS AS PLANT, QDATU AS CONFIRMATION_DATE, 
    QZEIT AS CONFIRMATION_TIME, VLTYP AS SOURCE_STORAGE_TYPE, 
    VLPLA AS SOURCE_STORAGE_BIN, NLTYP AS DESTINATION_STORAGE_TYPE,
    NLPLA AS DESTINATION_STORAGE_BIN, VBELN AS DELIVERY_NUMBER, 
    CHARG AS BATCH, EDATU AS CONFIRMATION_DATE1, EZEIT AS CONFIRMATION_TIME1
  FROM LTAP_LTAK_POE
  WHERE BDATU >= '20230101'  -- 1713万行
)
```

### UNION ALL 结构 (13个)

1. GR304 - 收货304区域
2. GR305B - 收货305B区域
3. GR308 - 收货308区域
4. RP304 - 补货304区域
5. GI304 - 发货304区域 (最大，包含大量OR条件)
6. GI308 - 发货308区域
7. GI305B - 发货305B区域
8. GI310 - 发货310区域 (KLT)
9. GR310 - 收货310区域 (KLT)
10. DE304 - 损耗304区域 (有MINUS操作)
11. DE308 - 损耗308区域
12. GRWX03 - 收货WX03区域
13. DEWX03 - 损耗WX03区域

### MINUS 操作 (DE304)

```sql
-- DE304 正向查询
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T
WHERE (SOURCE_STORAGE_TYPE='COS' AND DESTINATION_STORAGE_TYPE='V02' AND SOURCE_STORAGE_BIN='RBCD_SAM')
OR (DESTINATION_STORAGE_TYPE='V10' AND SOURCE_STORAGE_BIN='RDC-JUNHE')
OR (MOVEMENT_TYPE_IM='601' AND MATERIAL NOT LIKE '2705%' ...)

MINUS

-- DE304 排除条件
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T
WHERE (MOVEMENT_TYPE_IM='601' ... AND SOURCE_STORAGE_TYPE='COS' AND SOURCE_STORAGE_BIN != 'RBCD_DEL')
OR (MOVEMENT_TYPE_IM='601' ... AND SOURCE_STORAGE_TYPE='ENS' AND SOURCE_STORAGE_BIN NOT IN ('WFMS','EXPORT'))
OR (MOVEMENT_TYPE_IM='601' ... AND SOURCE_STORAGE_TYPE='ENT')
```

## 性能问题根因

### 1. CTE 物化无索引

Oracle 优化器将 CTE 物化为临时表，临时表没有索引，导致后续操作无法使用原表索引。

**验证**:
```sql
-- 直接查基表 (有索引，1秒)
SELECT COUNT(*) FROM LTAP_LTAK_POE WHERE BDATU >= '20230101';

-- 通过视图查 (CTE无索引，130秒)
SELECT COUNT(*) FROM LOI_V_LTAP_EXPORT;
```

### 2. 13次重复扫描

每个 UNION ALL 都扫描同一个 CTE 临时表，共扫描 13 次 × 1713万行。

### 3. MINUS 排序

DE304 的 MINUS 操作需要排序去重，执行计划预估 2.19 亿行。

### 4. 无分区裁剪

`BDATU >= '20230101'` 没有上限条件，扫描所有 70+ 个分区。

**执行计划**:
```
PARTITION RANGE ALL → TABLE ACCESS FULL → TEMP TABLE → UNION-ALL → MINUS
```

## 实测数据

| 指标 | 预估值 | 实测值 | 说明 |
|------|--------|--------|------|
| 查询时间 | 47秒 | **2分10秒 (130秒)** | 执行计划预估偏差大 |
| 视图行数 | 886万 | **8,875,935 (887.6万)** | 基本准确 |
| CTE扫描行数 | 1713万 | 1713万 | 准确 |
| 分区数 | 70+ | 70+ | 准确 |

## 优化方案

### 方案 X: 重命名 + 创建同名表 + 存储过程刷新

**原理**: 绕过视图的 CTE 问题，将视图替换为同名表，通过存储过程定时刷新当月数据。

**步骤**:
1. DROP 物化视图 LOI_V_LOM_PICK_TO (依赖对象)
2. RENAME 视图 LOI_V_LTAP_EXPORT → LOI_V_LTAP_EXPORT_BAK
3. CREATE TABLE LOI_V_LTAP_EXPORT (结构同原视图)
4. CREATE INDEX (CREATION_DATE, SOURCE_STORAGE_TYPE)
5. INSERT 当月数据
6. CREATE PROCEDURE SP_REFRESH_EXPORT_LTAP (TRUNCATE + INSERT当月)
7. CREATE JOB 每小时执行
8. 重建物化视图 LOI_V_LOM_PICK_TO

**预期效果**:
- Java端查询: 130秒 → <1秒
- 刷新耗时: 每小时约10-20秒 (只取当月40万行)
- 数据延迟: 最多1小时

**回滚方法**:
```sql
DROP TABLE LOI_V_LTAP_EXPORT;
DROP PROCEDURE SP_REFRESH_EXPORT_LTAP;
DBMS_SCHEDULER.DROP_JOB('JOB_REFRESH_EXPORT_LTAP');
DROP MATERIALIZED VIEW LOI_V_LOM_PICK_TO;
RENAME LOI_V_LTAP_EXPORT_BAK TO LOI_V_LTAP_EXPORT;
-- 重建原物化视图
```

## 关键 Pitfalls

1. **必须使用实测值，不用预估值**: 执行计划预估 47秒，实测 2分10秒。向用户汇报时引用实测值。
2. **CTE 会导致索引失效**: WITH 子句被 Oracle 物化为临时表，临时表没有索引。
3. **重命名视图前检查依赖**: LOI_V_LOM_PICK_TO 依赖 LOI_V_LTAP_EXPORT，需要先处理。
4. **MINUS 操作不支持 FAST 刷新**: 包含 MINUS 的视图只能用 COMPLETE 刷新。

## 采集信息

- 采集时间: 2026-06-02
- 来源: 用户在 SQL Developer 中执行 `SELECT TEXT FROM USER_VIEWS WHERE VIEW_NAME = 'LOI_V_LTAP_EXPORT'`
- 保存位置: `PLMS数据梳理/07_数据库代码/LOI_V_LTAP_EXPORT_view_definition.sql`
