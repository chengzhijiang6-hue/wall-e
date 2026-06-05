# Oracle 数据库元数据检索 SQL

用于从 Oracle 数据库中提取表/视图/物化视图的结构信息，补充代码分析无法覆盖的数据库层细节。

## 连接信息（PLMS 实例）

```
Host:    wx0orarac02.apac.bosch.com
Port:    38000
Service: bcdlog_app.apac.bosch.com
User:    LOGPOE
```

## SQL 1: 对象基本信息 + 注释

```sql
SELECT o.object_name, o.object_type, c.comments
FROM all_objects o
LEFT JOIN all_tab_comments c ON c.owner=o.owner AND c.table_name=o.object_name
WHERE o.owner='LOGPOE'
  AND o.object_type IN ('TABLE','VIEW','MATERIALIZED VIEW')
  AND o.object_name IN (/* 170+ 表名列表 */)
ORDER BY o.object_type, o.object_name;
```

## SQL 2: 列信息（列名、类型、NULL、注释）

```sql
SELECT t.table_name, t.column_id, t.column_name,
       t.data_type || CASE WHEN t.data_type IN ('VARCHAR2','CHAR')
       THEN '('||t.data_length||')' WHEN t.data_type='NUMBER' AND t.data_precision IS NOT NULL
       THEN '('||t.data_precision||','||NVL(t.data_scale,0)||')' ELSE '' END AS dtype,
       t.nullable, c.comments
FROM all_tab_columns t
LEFT JOIN all_col_comments c ON c.owner=t.owner AND c.table_name=t.table_name AND c.column_name=t.column_name
WHERE t.owner='LOGPOE' AND t.table_name IN (/* ... */)
ORDER BY t.table_name, t.column_id;
```

## SQL 3: 视图/物化视图 SQL 定义

```sql
SELECT view_name, 'VIEW' AS obj_type, text FROM all_views
WHERE owner='LOGPOE' AND view_name IN (/* ... */)
UNION ALL
SELECT mview_name, 'MV' AS obj_type, query FROM all_mviews
WHERE owner='LOGPOE' AND mview_name IN (/* ... */)
ORDER BY 1;
```

## SQL 4: 物化视图刷新策略

```sql
SELECT mview_name, refresh_mode, refresh_method,
       TO_CHAR(last_refresh_date,'YYYY-MM-DD HH24:MI:SS'), staleness
FROM all_mviews WHERE owner='LOGPOE' AND mview_name IN (/* ... */);
```

## SQL 5: 索引信息

```sql
SELECT a.table_name, a.index_name, b.uniqueness, a.column_name
FROM all_ind_columns a JOIN all_indexes b ON a.index_name=b.index_name AND a.table_owner=b.owner
WHERE a.table_owner='LOGPOE' AND a.table_name IN (/* ... */)
ORDER BY a.table_name, a.index_name, a.column_position;
```

## 使用方式

1. 用户在数据库客户端（SQL Developer / DBeaver）中执行
2. 导出结果（CSV 或文本）发给 Agent
3. Agent 合并到操作手册知识库

## Pitfalls

- `all_tables.num_rows` 是统计值，不是精确行数（需要 ANALYZE 后才准确）
- 视图定义 `all_views.text` 可能被截断（LONG 类型限制），用 `all_mviews.query` 替代
- 物化视图的 `staleness` 字段：FRESH=最新，STALE=过期，NEEDS_COMPILE=需要编译
- Python 3.14 可能没有 `oracledb` 包（PyPI 尚未适配），回退到 `cx_Oracle` 或直接给用户 SQL 文件让用户在客户端执行
- 物化视图刷新: `EXEC DBMS_MVIEW.REFRESH('LOGPOE.视图名', 'C');` (C=全量, F=增量)
- 编码问题: 中文 PDF 提取时 print() 可能报 UnicodeEncodeError，需 `$env:PYTHONIOENCODING='utf-8'`

## 交叉比对方法

拿到数据库元数据后，与代码分析/PDF手册结果做集合运算：
```python
in_db_not_doc = db_tables - doc_tables    # 数据库有但文档未记录 → 补充到文档
in_doc_not_db = doc_tables - db_tables    # 文档有但数据库未查到 → 标注待确认
common = db_tables & doc_tables           # 共同验证 → 可信度最高
```

误报过滤: `CB$C`, `GR_DATE`, `MACHINE_TYPE`, `RP_HOUR` 等正则误匹配需人工排除。
