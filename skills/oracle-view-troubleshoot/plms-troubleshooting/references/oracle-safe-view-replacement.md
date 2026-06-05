# Oracle 安全视图替换模式

## 场景

需要将普通视图替换为同名表（用于性能优化），但不能修改依赖该视图的 Java 代码。

## 前提条件检查

### 1. 检查同名对象

```sql
SELECT object_name, object_type FROM user_objects WHERE object_name = 'TARGET_NAME';
SELECT table_name FROM user_tables WHERE table_name = 'TARGET_NAME';
SELECT view_name FROM user_views WHERE view_name = 'TARGET_NAME';
SELECT job_name FROM user_scheduler_jobs WHERE job_name = 'JOB_NAME';
SELECT index_name FROM user_indexes WHERE index_name = 'INDEX_NAME';
```

### 2. 检查依赖关系

```sql
-- 谁依赖了这个视图？
SELECT name, type, referenced_name, referenced_type
FROM user_dependencies
WHERE referenced_name = 'VIEW_NAME';

-- 这个视图依赖谁？
SELECT name, type, referenced_name, referenced_type
FROM user_dependencies
WHERE name = 'VIEW_NAME';
```

**关键**: 如果有物化视图依赖目标视图，重命名后物化视图会失效，需要同时重建。

## 正向操作

```sql
-- 1. 重命名原视图
ALTER VIEW VIEW_NAME RENAME TO VIEW_NAME_OLD;

-- 2. 创建同名表 (从原视图复制结构和数据)
CREATE TABLE VIEW_NAME AS SELECT * FROM VIEW_NAME_OLD;

-- 3. 创建索引
CREATE INDEX IDX_NAME_COL ON VIEW_NAME(COLUMN_NAME);

-- 4. 创建刷新存储过程
CREATE OR REPLACE PROCEDURE P_REFRESH_VIEW_NAME AS
BEGIN
  DELETE FROM VIEW_NAME;
  INSERT INTO VIEW_NAME SELECT * FROM VIEW_NAME_OLD;
  COMMIT;
END;
/

-- 5. 创建定时任务
BEGIN
  DBMS_SCHEDULER.CREATE_JOB (
    job_name => 'REFRESH_VIEW_NAME',
    job_type => 'PLSQL_BLOCK',
    job_action => 'BEGIN P_REFRESH_VIEW_NAME; END;',
    repeat_interval => 'FREQ=HOURLY;MINUTE=5',
    enabled => TRUE
  );
END;
/

-- 6. 如果有依赖物化视图，重建
DROP MATERIALIZED VIEW DEPENDENT_MV;
CREATE MATERIALIZED VIEW DEPENDENT_MV AS
SELECT ... FROM VIEW_NAME;
```

## 回滚操作

```sql
-- 1. 删除定时任务
BEGIN DBMS_SCHEDULER.DROP_JOB('REFRESH_VIEW_NAME'); END;
/

-- 2. 删除存储过程
DROP PROCEDURE P_REFRESH_VIEW_NAME;

-- 3. 删除同名表
DROP TABLE VIEW_NAME;

-- 4. 恢复原视图名称
ALTER VIEW VIEW_NAME_OLD RENAME TO VIEW_NAME;

-- 5. 如果有依赖物化视图，重建 (使用原视图)
DROP MATERIALIZED VIEW DEPENDENT_MV;
CREATE MATERIALIZED VIEW DEPENDENT_MV AS
SELECT ... FROM VIEW_NAME;
```

## 风险点

1. **刷新存储过程仍然慢**: 如果原视图查询本身慢（如 47 秒），存储过程也会慢。但存储过程可以设置超时，且在后台执行不影响用户查询。
2. **数据延迟**: 取决于刷新频率（每小时 = 最多 1 小时延迟）。
3. **依赖物化视图失效**: 必须同时重建。
4. **存储空间**: 新表 + 索引需要额外空间。
5. **事务一致性**: 刷新过程中 DELETE + INSERT 不是原子的，可能出现短暂数据缺失。

## 适用场景

- 普通视图查询慢，无法修改视图定义
- 无法修改 Java 代码（Mapper XML 中的 SQL）
- 有现成的物化视图但 Java 代码没有使用
- 需要快速修复性能问题，不涉及架构变更

## 不适用场景

- 视图查询涉及大量表 JOIN（刷新存储过程也会慢）
- 需要实时数据（不能接受任何延迟）
- 依赖物化视图过多（重建成本高）
