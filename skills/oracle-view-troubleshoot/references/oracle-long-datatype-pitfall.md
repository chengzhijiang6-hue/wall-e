# Oracle LONG 类型 Pitfall

`USER_VIEWS.TEXT` 列是 LONG 类型，不支持 ORDER BY、SUBSTR、WHERE 比较、DISTINCT、UNION、GROUP BY。

报错：`ORA-00997: illegal use of LONG datatype`

## 解决方案

```sql
-- 错误: SUBSTR + ORDER BY
SELECT view_name, SUBSTR(text, 4000, 1) FROM user_views ORDER BY view_name;

-- 正确: DBMS_METADATA.GET_DDL
SELECT view_name, DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS view_ddl
FROM user_views WHERE view_name LIKE 'LOI%' ORDER BY view_name;
```

物化视图同理：
```sql
SELECT mview_name, DBMS_METADATA.GET_DDL('MATERIALIZED_VIEW', mview_name, USER) AS mv_ddl
FROM user_mviews WHERE mview_name LIKE 'LOI%' ORDER BY mview_name;
```

## 权限

`DBMS_METADATA.GET_DDL` 需要 `SELECT_CATALOG_ROLE` 或对象所有者权限。
LOGPOE 用户有此权限（2026-05-27 验证）。

## 替代方案（权限不足时）

用 PL/SQL 块逐行读取：
```sql
DECLARE v_text LONG;
BEGIN
  FOR rec IN (SELECT view_name, text FROM user_views WHERE view_name = 'XXX') LOOP
    v_text := rec.text;
    DBMS_OUTPUT.PUT_LINE(SUBSTR(v_text, 1, 4000));
  END LOOP;
END;
/
```
