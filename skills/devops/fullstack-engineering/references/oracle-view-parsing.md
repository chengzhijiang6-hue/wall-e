# Oracle 视图定义文件解析模式

## 文件格式 (LOI.txt)

Oracle DBA 导出的视图/表定义文件，每行一个条目，格式：

```
OBJECT_NAME<TAB>TYPE_OR_SQL
```

### 四种条目类型

1. **基表**: `TABLE_NAME\tTABLE`
2. **视图 (单行SQL)**: `VIEW_NAME\t"SELECT ... FROM ..."`
3. **视图 (多行SQL)**: `VIEW_NAME\tVIEW` 后续行是 SQL 直到下一个 `NAME\t` 开头
4. **物化视图**: `MV_NAME\tMATERIALIZED VIEW`

### 关键解析陷阱

#### 字面量 `\n` vs 换行符
- 文件中的 `\n` 是两个字符: `\` + `n`（不是换行符）
- 视图 SQL 可能同时包含字面量 `\n` 和实际换行
- 解析时需: `sql.replace('\\n', '\n').replace("\\'", "'")`

#### 多行视图边界检测
```python
# 正确：逐行扫描，遇到新的 NAME<TAB> 开头就停止
while i < len(lines):
    nl = lines[i].strip()
    if re.match(r'^[A-Za-z_]\w*\t', nl):  # 新条目开始
        break
    sql_parts.append(lines[i])
    i += 1
```

#### 引号处理
- 单行 SQL 用双引号包裹: `"SELECT ..."` → 去掉首尾 `"`
- 多行 SQL 可能跨多行直到行尾的 `"`

## 视图引用提取

```python
def extract_refs(sql):
    """从 SQL 中提取 FROM/JOIN/INTO/UPDATE 后的表名"""
    refs = set()
    # 需排除大量 Oracle 关键字
    ORACLE_KEYWORDS = {'SELECT','WHERE','SET','AND','OR','NOT','NULL','DUAL',
                       'ON','AS','IN','CASE','WHEN','THEN','ELSE','END',
                       'LEFT','RIGHT','INNER','OUTER','CROSS','WITH',
                       'GROUP','ORDER','HAVING','UNION','MINUS', ...}
    for m in re.finditer(r'(?:FROM|JOIN|INTO|UPDATE)\s+([A-Za-z_]\w*)', sql, re.IGNORECASE):
        ref = m.group(1).upper()
        if len(ref) > 2 and ref not in ORACLE_KEYWORDS:
            refs.add(ref)
    return refs
```

## PLMS 实际数据

| 类型 | 数量 |
|------|------|
| 基表 (TABLE) | 1428 |
| 视图 (VIEW) | 782 |
| 物化视图 (MV) | 64 |
| PLMS引用的视图 | 61 |
| PLMS引用的基表 | 160 |
| PLMS引用的MV | 17 |
| 视图展开后最终基表 | 295 |

## 典型视图展开示例

```
LOI_V_301302 (仓库301/302容量)
  → LQUA_POE, MSEG_POE, SAP_MARC, LOI_MT_WAREHOUSE_DEFINITION

LOI_V_BIN_RATIO (货架占比)
  → LAGP_POE, LQUA_POE, MLGN_POE, MSEG_POE, SAP_MARC, LOI_MT_WAREHOUSE_DEFINITION

LOI_V_TO_WORKINGHOUR (生产力工时)
  → FACT_LTAP_LTAK_POE_HOUR, FACT_MSEG_POE_HOUR, LOI_MT_SHIFT_DEFINITION,
    LOI_BK_WORKHOUR_MANUAL, DIM_DATE, DIM_STAFF

LOI_V_OTD_REAL_TIME (OTD实时)
  → TEMP_MGT_C_OTD_TEST, TEMP_MGT_C_TO_D, TEMP_LINE_I5, SAP_KNA1...
```
