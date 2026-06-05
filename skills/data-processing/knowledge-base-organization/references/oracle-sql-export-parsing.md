# Oracle SQL Developer Export Parsing

## 导出格式

### 1. USER_SOURCE（存储过程/函数源码）

```
NAME\tLINE_NUM\t"SOURCE_CODE\r\n
"\r\n
NAME\tLINE_NUM\t"SOURCE_CODE\r\n
"\r\n
```

每行格式: `PROC_NAME\tLINE_NUMBER\t"CODE_TEXT`
闭合引号在下一行: `"`
CRLF 换行。

Section header（SQL Developer 导出分段）: `数字.` 如 `1.`、`2.`

### 2. USER_VIEWS（视图定义）

```
VIEW_NAME\t"SQL_DEFINITION"
```

**注意**: Section 2 可能为空（查询无结果时）。

### 3. USER_TAB_COLUMNS（表结构）

```
TABLE_NAME\tCOLUMN_NAME\tDATA_TYPE\tDATA_LENGTH\tNULLABLE
```

### 4. COUNT(*)（行数统计）

```
TABLE_NAME\tCOUNT
```

### 5. USER_MVIEWS（物化视图）

```
MVIEW_NAME\tQUERY
```

## Python 解析代码

```python
import re

with open('export.txt', 'r', encoding='utf-8', errors='replace') as f:
    raw = f.read()

lines = raw.split('\n')

# 找 section 边界
boundaries = []
for i, line in enumerate(lines):
    l = line.strip().rstrip('\r')
    if re.match(r'^\d+\.$', l):
        boundaries.append((i, l))

# 解析存储过程
procs = {}
i = 0
while i < len(lines):
    line = lines[i].strip().rstrip('\r')
    if re.match(r'^\d+\.$', line) or line == '"' or not line:
        i += 1; continue
    m = re.match(r'^(\w+)\t(\d+)\t"(.*)$', line)
    if m:
        procs.setdefault(m.group(1), {})[int(m.group(2))] = m.group(3)
    i += 1

# 解析表结构
tables = {}
for line in lines:
    parts = line.strip().rstrip('\r').split('\t')
    if len(parts) >= 5 and parts[0].startswith('LOI_'):
        tables.setdefault(parts[0], []).append({
            'col': parts[1], 'type': parts[2],
            'len': parts[3], 'null': parts[4]
        })

# 解析行数
row_counts = {}
for line in lines:
    parts = line.strip().rstrip('\r').split('\t')
    if len(parts) == 2 and parts[0].startswith('LOI_'):
        try:
            row_counts[parts[0]] = int(parts[1])
        except ValueError:
            pass
```

## ORA- 错误处理

导出文件中可能包含 Oracle 错误行（`ORA-00942`、`ORA-04044` 等），
解析时需要跳过以 `ORA-` 开头的行和 `Error at Line:` 行。

## 查询模板

```sql
-- 存储过程源码
SELECT NAME, LINE, TEXT FROM USER_SOURCE
WHERE NAME IN ('LOI_P_XXX', 'LOI_P_YYY')
ORDER BY NAME, LINE;

-- 视图定义
SELECT VIEW_NAME, TEXT FROM USER_VIEWS
WHERE VIEW_NAME IN ('LOI_V_XXX', 'LOI_V_YYY');

-- 表结构
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME IN ('LOI_MT_XXX', 'LOI_HIS_YYY')
ORDER BY TABLE_NAME, COLUMN_ID;

-- 行数统计
SELECT 'TABLE_NAME' AS TNAME, COUNT(*) AS CNT FROM TABLE_NAME;

-- 物化视图
SELECT MVIEW_NAME, QUERY FROM USER_MVIEWS
WHERE MVIEW_NAME IN ('LOI_MV_XXX');
```

## 模糊查找对象

```sql
-- 查找已改名/删除的对象
SELECT VIEW_NAME FROM USER_VIEWS
WHERE VIEW_NAME LIKE 'LOI_V_DE_AUTO%'
   OR VIEW_NAME LIKE 'LOI_V_FAILURE%';

-- 检查同义词
SELECT 'MV' AS SRC, MVIEW_NAME AS NAME FROM USER_MVIEWS
WHERE MVIEW_NAME LIKE 'LOI_V_LZT%'
UNION ALL
SELECT 'SYN' AS SRC, SYNONYM_NAME AS NAME FROM USER_SYNONYMS
WHERE SYNONYM_NAME LIKE 'LOI_V_LZT%';
```
