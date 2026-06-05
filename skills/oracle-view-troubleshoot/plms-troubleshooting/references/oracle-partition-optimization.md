# Oracle 分区表性能优化

## 分区裁剪 (Partition Pruning)

当查询条件匹配分区键时，Oracle 只扫描相关分区（分区裁剪），大幅减少 IO。

### 问题: PARTITION RANGE ALL

```
执行计划显示:
  PARTITION RANGE ALL  → 扫描所有分区 → 慢
  Pstart=1, Pstop=1048575

原因:
  WHERE 条件没有匹配分区键
  或者分区键不在 WHERE 条件中
```

### 优化: 分区裁剪

```sql
-- 当前 (扫描所有 70+ 分区)
FROM LTAP_LTAK_POE
WHERE BDATU >= '20230101'

-- 优化后 (只扫描当月分区)
FROM LTAP_LTAK_POE
WHERE BDATU >= '20230101'
  AND BDATU >= TRUNC(SYSDATE, 'MM')  -- 分区裁剪
```

**效果**: 查询时间从 47 秒 → 5 秒

## 检查分区信息

```sql
-- 检查表是否是分区表
SELECT table_name, partitioning_type, partition_count
FROM user_part_tables
WHERE table_name = 'LTAP_LTAK_POE';

-- 查看分区详情
SELECT partition_name, high_value, num_rows, last_analyzed
FROM user_tab_partitions
WHERE table_name = 'LTAP_LTAK_POE'
ORDER BY partition_position;

-- 查看分区键
SELECT column_name, column_position
FROM user_part_key_columns
WHERE name = 'LTAP_LTAK_POE';
```

## 检查执行计划

```sql
-- 查看执行计划
EXPLAIN PLAN FOR
SELECT * FROM LTAP_LTAK_POE
WHERE BDATU >= '20230101';

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- 期望看到:
-- PARTITION RANGE SINGLE  → 只扫描一个分区
-- PARTITION RANGE ITERATOR → 扫描多个分区（但不是全部）

-- 避免:
-- PARTITION RANGE ALL → 扫描所有分区
```

## 分区裁剪优化技巧

### 1. 使用分区键作为过滤条件

```sql
-- 差: 没有分区裁剪
SELECT * FROM LTAP_LTAK_POE
WHERE VLTYP = '301';

-- 好: 有分区裁剪
SELECT * FROM LTAP_LTAK_POE
WHERE BDATU >= '20260601'
  AND VLTYP = '301';
```

### 2. 使用 TRUNC 函数

```sql
-- 获取当月数据
WHERE BDATU >= TRUNC(SYSDATE, 'MM')

-- 获取最近 7 天数据
WHERE BDATU >= TO_CHAR(SYSDATE - 7, 'YYYYMMDD')
```

### 3. 使用绑定变量

```sql
-- 使用绑定变量
WHERE BDATU >= :start_date

-- 而不是硬编码
WHERE BDATU >= '20230101'
```

## 分区表设计建议

### 1. 选择合适的分区键

```
好的分区键:
  - 经常在 WHERE 条件中使用
  - 数据分布均匀
  - 日期类型 (如 BDATU)

差的分区键:
  - 很少在 WHERE 条件中使用
  - 数据分布不均匀
  - 高基数列 (如 MATERIAL)
```

### 2. 选择合适的分区间隔

```
按天分区: 数据量大，查询频繁
按月分区: 数据量中等，查询频率中等
按年分区: 数据量小，查询频率低
```

### 3. 定期维护分区

```sql
-- 添加新分区
ALTER TABLE LTAP_LTAK_POE
ADD PARTITION P202607 VALUES LESS THAN ('20260801');

-- 删除旧分区
ALTER TABLE LTAP_LTAK_POE
DROP PARTITION P202001;

-- 合并分区
ALTER TABLE LTAP_LTAK_POE
MERGE PARTITIONS P202001, P202002 INTO PARTITION P202001_02;
```

## LTAP_LTAK_POE 分区信息

```
表名: LTAP_LTAK_POE
类型: TABLE PARTITION
分区键: BDATU (创建日期)
分区范围: 2020-01-01 ~ 2026-06-01
分区数量: 70+ 个 (按月分区)
总行数: 38,325,890 (3830 万)
总大小: ~2,400 MB
每月行数: 约 40-50 万行
```

## Pitfalls

1. **分区裁剪不是万能的**: 如果查询条件不包含分区键，分区裁剪无效
2. **分区数量过多**: 分区数量过多会增加管理复杂度
3. **分区统计信息**: 定期收集分区统计信息，确保优化器选择正确的执行计划
4. **分区索引**: 分区表可以使用分区索引，进一步提高性能
