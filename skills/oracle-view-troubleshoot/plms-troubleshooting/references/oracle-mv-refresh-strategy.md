# Oracle 物化视图刷新策略指南

## COMPLETE vs FAST 刷新对比

```
                    COMPLETE 刷新          FAST 刷新 (增量)
─────────────────────────────────────────────────────────────
刷新时间            长 (扫描全表)          短 (只处理变化)
数据延迟            取决于刷新频率          可以更频繁刷新
数据库负载          高                     低
配置复杂度          低                     高 (需要物化视图日志)
适用场景            数据延迟可接受          数据延迟要求高
─────────────────────────────────────────────────────────────
```

## FAST 刷新限制条件

视图不能包含以下操作（会导致 FAST 刷新失败）：

```
1. DISTINCT
2. GROUP BY
3. 集合操作: UNION ALL, MINUS, INTERSECT (部分情况支持)
4. 子查询 (部分情况支持)
5. 分析函数: OVER, ROW_NUMBER, RANK 等
6. CONNECT BY
7. 外连接 (部分情况支持)
```

## 检查视图是否支持 FAST 刷新

### 方法 1: EXPLAIN_MVIEW

```sql
-- 创建解释表 (首次需要)
@?/rdbms/admin/utlxmv.sql

-- 分析视图
BEGIN
  DBMS_MVIEW.EXPLAIN_MVIEW('视图名');
END;
/

-- 查询结果
SELECT capability_name, possible, msg
FROM MV_CAPABILITIES_TABLE
WHERE MVNAME = '视图名';
```

### 方法 2: 检查视图 SQL

```sql
-- 检查是否包含限制操作
SELECT 'UNION ALL' AS OPERATION, 
       CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END AS HAS_OPERATION
FROM user_views 
WHERE view_name = 'LOI_V_LTAP_EXPORT' 
  AND TEXT LIKE '%UNION ALL%'
UNION ALL
SELECT 'MINUS', 
       CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END
FROM user_views 
WHERE view_name = 'LOI_V_LTAP_EXPORT' 
  AND TEXT LIKE '%MINUS%';
```

**注意**: user_views.TEXT 是 LONG 类型，不能直接用于 LIKE 操作。需要用 DBMS_METADATA.GET_DDL 获取视图定义。

### 方法 3: 尝试创建物化视图

```sql
-- 尝试创建 FAST 刷新物化视图
CREATE MATERIALIZED VIEW LOI_MV_TEST
REFRESH FAST ON DEMAND
AS
SELECT ... FROM 视图名;

-- 如果失败，会报错说明原因
```

## LOI_V_LTAP_EXPORT 刷新策略分析

```
视图特性:
  - 20+ 个 UNION ALL → 不支持 FAST 刷新
  - MINUS 操作 → 不支持 FAST 刷新
  - CTE (WITH 子句) → 可能不支持

结论: 只能使用 COMPLETE 刷新
```

## 数据更新频率检查

```sql
-- 检查表的数据更新频率 (最近 7 天)
SELECT SUBSTR(BDATU, 1, 8) AS DAY,
       COUNT(*) AS ROW_COUNT
FROM LTAP_LTAK_POE
WHERE BDATU >= TO_CHAR(SYSDATE - 7, 'YYYYMMDD')
GROUP BY SUBSTR(BDATU, 1, 8)
ORDER BY DAY DESC;

-- 检查今天按小时分布
SELECT SUBSTR(BDATU, 1, 8) AS DAY,
       SUBSTR(BZEIT, 1, 2) AS HOUR,
       COUNT(*) AS ROW_COUNT
FROM LTAP_LTAK_POE
WHERE BDATU >= TO_CHAR(SYSDATE, 'YYYYMMDD')
GROUP BY SUBSTR(BDATU, 1, 8), SUBSTR(BZEIT, 1, 2)
ORDER BY DAY DESC, HOUR DESC;
```

## 刷新频率选择

```
数据更新频率        建议刷新频率        数据延迟
─────────────────────────────────────────────────
实时 (每小时)       每小时 COMPLETE     最多 1 小时
每天批量           每天凌晨 COMPLETE   最多 24 小时
每周批量           每周日凌晨 COMPLETE 最多 7 天
─────────────────────────────────────────────────
```

## 创建定时刷新任务

```sql
-- 每小时刷新
BEGIN
  DBMS_SCHEDULER.CREATE_JOB (
    job_name        => 'REFRESH_EXPORT_MV',
    job_type        => 'PLSQL_BLOCK',
    job_action      => 'BEGIN DBMS_MVIEW.REFRESH(''LOI_MV_LTAP_EXPORT'', ''C''); END;',
    start_date      => SYSTIMESTAMP,
    repeat_interval => 'FREQ=HOURLY;MINUTE=5',
    enabled         => TRUE
  );
END;
/

-- 每天凌晨 2 点刷新
BEGIN
  DBMS_SCHEDULER.CREATE_JOB (
    job_name        => 'REFRESH_EXPORT_MV',
    job_type        => 'PLSQL_BLOCK',
    job_action      => 'BEGIN DBMS_MVIEW.REFRESH(''LOI_MV_LTAP_EXPORT'', ''C''); END;',
    start_date      => SYSTIMESTAMP,
    repeat_interval => 'FREQ=DAILY;HOUR=2;MINUTE=0',
    enabled         => TRUE
  );
END;
/

-- 检查定时任务
SELECT job_name, enabled, 
       TO_CHAR(last_start_date, 'YYYY-MM-DD HH24:MI:SS') AS last_run,
       TO_CHAR(next_run_date, 'YYYY-MM-DD HH24:MI:SS') AS next_run
FROM user_scheduler_jobs
WHERE job_name = 'REFRESH_EXPORT_MV';
```

## 物化视图状态检查

```sql
SELECT mview_name, staleness, compile_state,
       TO_CHAR(last_refresh_date, 'YYYY-MM-DD HH24:MI:SS') AS last_refresh,
       refresh_method, refresh_mode
FROM user_mviews
WHERE mview_name = 'LOI_MV_LTAP_EXPORT';
```

## Pitfalls

1. **FAST 刷新不一定更快**: 如果物化视图日志很大，FAST 刷新可能比 COMPLETE 更慢
2. **物化视图日志清理**: 定期清理物化视图日志，避免占用过多空间
3. **刷新失败处理**: 设置刷新失败告警，及时处理
4. **数据一致性**: COMPLETE 刷新期间，查询会返回旧数据
