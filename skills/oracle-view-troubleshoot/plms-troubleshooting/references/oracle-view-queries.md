# Oracle 视图检索 SQL 模板

## 物化视图状态查询

```sql
SELECT 
    mview_name,
    TO_CHAR(last_refresh_date, 'YYYY-MM-DD HH24:MI:SS') AS last_refresh,
    staleness,
    compile_state
FROM user_mviews 
ORDER BY mview_name;
```

## 物化视图 DDL（用 DBMS_METADATA 绕过 LONG 限制）

```sql
SET LONG 32767
SET LONGCHUNKSIZE 32767

SELECT mview_name, 
       DBMS_METADATA.GET_DDL('MATERIALIZED_VIEW', mview_name, USER) AS mv_ddl
FROM user_mviews 
WHERE mview_name LIKE 'LOI%'
ORDER BY mview_name;
```

## 普通视图 DDL（分批返回）

```sql
-- 批次1: A-F
SELECT view_name, 
       DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS view_ddl
FROM user_views 
WHERE view_name LIKE 'LOI%' AND view_name <= 'LOI_FZZZZZ'
ORDER BY view_name;

-- 批次2: G-N
SELECT view_name, 
       DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS view_ddl
FROM user_views 
WHERE view_name LIKE 'LOI%' AND view_name > 'LOI_FZZZZZ' AND view_name <= 'LOI_NZZZZZ'
ORDER BY view_name;

-- 批次3: O-Z
SELECT view_name, 
       DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS view_ddl
FROM user_views 
WHERE view_name LIKE 'LOI%' AND view_name > 'LOI_NZZZZZ'
ORDER BY view_name;
```

## 存储过程/函数列表

```sql
SELECT DISTINCT
    name,
    type,
    MAX(line) AS total_lines
FROM user_source 
WHERE type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE', 'PACKAGE BODY')
GROUP BY name, type
ORDER BY type, name;
```

## 存储过程代码

```sql
SELECT name, type, line, text
FROM user_source 
WHERE type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE', 'PACKAGE BODY')
  AND name LIKE 'LOI%'
ORDER BY type, name, line;
```

## 物化视图依赖关系

```sql
SELECT d.name AS mview_name, 
       d.referenced_name, 
       d.referenced_type
FROM user_dependencies d
WHERE d.name IN (
    SELECT mview_name FROM user_mviews WHERE compile_state = 'COMPILATION_ERROR'
)
ORDER BY d.name, d.referenced_name;
```

## Oracle LONG 类型 Pitfall

`USER_VIEWS.TEXT` 列是 LONG 类型，不能用于 ORDER BY/SUBSTR/WHERE/DISTINCT。

报错：`ORA-00997: illegal use of LONG datatype`

解决方案：用 `DBMS_METADATA.GET_DDL()` 替代。
