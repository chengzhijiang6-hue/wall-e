# Oracle LONG 类型 Pitfall

## 问题

`USER_VIEWS.TEXT` 和 `USER_TAB_COLUMNS` 等系统视图中的某些列是 LONG 类型（Oracle 遗留类型），不支持以下操作：

- `ORDER BY`
- `SUBSTR()`
- `WHERE` 条件比较
- `DISTINCT`
- `UNION`
- `GROUP BY`

报错：`ORA-00997: illegal use of LONG datatype`

## 解决方案

### 方案 1: DBMS_METADATA.GET_DDL（推荐）

```sql
SELECT view_name, 
       DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS view_ddl
FROM user_views 
WHERE view_name LIKE 'LOI%'
ORDER BY view_name;
```

物化视图：
```sql
SELECT mview_name, 
       DBMS_METADATA.GET_DDL('MATERIALIZED_VIEW', mview_name, USER) AS mv_ddl
FROM user_mviews 
WHERE mview_name LIKE 'LOI%'
ORDER BY mview_name;
```

### 方案 2: TO_LOB() 转换（仅适用于 INSERT..SELECT）

```sql
CREATE TABLE temp_views AS
SELECT view_name, TO_LOB(text) AS view_text
FROM user_views;
```

### 方案 3: PL/SQL 块逐行读取

```sql
DECLARE
    v_text LONG;
BEGIN
    FOR rec IN (SELECT view_name, text FROM user_views WHERE view_name = 'XXX') LOOP
        v_text := rec.text;
        DBMS_OUTPUT.PUT_LINE(rec.view_name || ': ' || SUBSTR(v_text, 1, 4000));
    END LOOP;
END;
/
```

## 权限要求

- `DBMS_METADATA.GET_DDL` 需要 `SELECT_CATALOG_ROLE` 或对象的所有者权限
- 如果报 `ORA-03160` 或 `ORA-31603`，说明权限不足，改用方案 2 或 3

## 经验

LOGPOE 用户有 `DBMS_METADATA` 权限（2026-05-27 验证通过）。
