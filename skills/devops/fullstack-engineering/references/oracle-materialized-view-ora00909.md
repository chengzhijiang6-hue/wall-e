# Oracle Materialized View ORA-00909 Debugging

## Symptom
- Materialized view status: `NEEDS_COMPILE` or `INVALID`
- Error: `ORA-00909: invalid number of arguments`
- Java application returns empty data (no error thrown to user)

## Root Cause Pattern: OR Operator Precedence
```sql
-- ❌ WRONG: OR without parentheses
WHERE s.PLANT = 'E682'
  AND s.RECORD_TYPE = 'STOCK_ON_HAND'
  AND s.IS_LATEST = 'Y'
  AND s.STORAGE_TYPE LIKE '8H%' OR s.STORAGE_TYPE LIKE '8F%' OR s.STORAGE_TYPE LIKE '8B%'
  AND s.GOODS_RECEIPT_DATE <> '00000000'

-- Oracle parses as:
-- (s.PLANT='E682' AND s.RECORD_TYPE='STOCK_ON_HAND' AND s.IS_LATEST='Y' AND s.STORAGE_TYPE LIKE '8H%')
-- OR (s.STORAGE_TYPE LIKE '8F%')
-- OR (s.STORAGE_TYPE LIKE '8B%' AND s.GOODS_RECEIPT_DATE<>'00000000')

-- ✅ CORRECT: OR with parentheses
WHERE s.PLANT = 'E682'
  AND s.RECORD_TYPE = 'STOCK_ON_HAND'
  AND s.IS_LATEST = 'Y'
  AND (s.STORAGE_TYPE LIKE '8H%' OR s.STORAGE_TYPE LIKE '8F%' OR s.STORAGE_TYPE LIKE '8B%')
  AND s.GOODS_RECEIPT_DATE <> '00000000'
```

## Diagnostic SQL
```sql
-- 1. Check if TABLE and MATERIALIZED VIEW have same name (conflict)
SELECT OWNER, OBJECT_NAME, OBJECT_TYPE, STATUS
FROM ALL_OBJECTS
WHERE OBJECT_NAME = 'YOUR_MV_NAME' AND OWNER = 'YOUR_SCHEMA';

-- 2. Check materialized view state
SELECT MVIEW_NAME, LAST_REFRESH_DATE, STALENESS, COMPILE_STATE
FROM ALL_MVIEWS
WHERE MVIEW_NAME = 'YOUR_MV_NAME' AND OWNER = 'YOUR_SCHEMA';

-- 3. Get materialized view SQL definition
SELECT QUERY FROM ALL_MVIEWS WHERE MVIEW_NAME = 'YOUR_MV_NAME' AND OWNER = 'YOUR_SCHEMA';

-- 4. Check dependencies
SELECT REFERENCED_OWNER, REFERENCED_NAME, REFERENCED_TYPE
FROM ALL_DEPENDENCIES
WHERE NAME = 'YOUR_MV_NAME' AND OWNER = 'YOUR_SCHEMA';
```

## Fix Without Changing Code
```sql
-- Option A: Recompile (may fail if SQL is invalid)
ALTER MATERIALIZED VIEW LOGPOE.YOUR_MV_NAME COMPILE;

-- Option B: Refresh (re-executes the query)
EXEC DBMS_MVIEW.REFRESH('LOGPOE.YOUR_MV_NAME');

-- Option C: If refresh succeeds, verify data
SELECT COUNT(*) FROM LOGPOE.YOUR_MV_NAME;
```

## Fix With Code Change (if refresh fails)
```sql
-- Drop and recreate with fixed SQL
DROP MATERIALIZED VIEW LOGPOE.YOUR_MV_NAME;

CREATE MATERIALIZED VIEW LOGPOE.YOUR_MV_NAME
REFRESH COMPLETE ON DEMAND START WITH sysdate+0 NEXT SYSDATE + 4/24
AS
-- Fixed SQL here (add parentheses around OR conditions)
SELECT ...;
```

## Why It Happens Without Code Changes
1. Oracle database patch/upgrade made SQL parsing stricter
2. Underlying view/table structure changed (ETL task modified schema)
3. Materialized view refresh failed once, became NEEDS_COMPILE, subsequent refreshes also fail

## Key Insight
- `ALTER MATERIALIZED VIEW ... COMPILE` = recheck syntax, no data change
- `DBMS_MVIEW.REFRESH` = re-execute query, repopulate data
- Neither changes the definition or parameters
- **Refresh 可能成功即使 SQL 有问题**：ORA-00909 在某些 Oracle 版本下只影响编译，不影响刷新。本案例中 `DBMS_MVIEW.REFRESH` 成功执行并返回 82 行数据，但后续查询仍可能失败
