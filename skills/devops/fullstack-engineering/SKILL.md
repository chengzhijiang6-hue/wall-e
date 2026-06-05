---
name: fullstack-engineering
description: "Full-stack Java/Vue/Oracle engineering — codebase tracing (frontend routes → API → Controller → SQL → tables), runtime debugging (UI issues → API calls → database queries), and Oracle view/materialized-view diagnostics. Built on PLMS/LOM-KPI (Vue 2 + Spring Boot + MyBatis + Oracle) but patterns generalize."
tags: [fullstack, debugging, tracing, java, vue, spring-boot, mybatis, oracle, codebase]
triggers:
  - "用户要求分析前后端代码对应关系"
  - "需要从数据库表反查前端页面，或从前端页面反查数据库"
  - "需要生成 路由→组件→API→Controller→SQL→表 的映射表"
  - "要求追踪某个功能的完整调用链（含SQL）"
  - "用户报告前端功能异常（按钮无响应、数据为空、显示错误）"
  - "需要追踪前端操作到后端API再到数据库"
  - "下载按钮只有列名没有数据"
  - "页面显示空白"
  - "Oracle 视图/物化视图失效排查"
---

# Full-Stack Engineering

Unified skill for understanding and troubleshooting full-stack Java/Vue/Oracle applications. Two complementary workflows:

- **Codebase Tracing** — Map the complete data flow: frontend routes → Vue components → API calls → Controller → Service/DAO → Mapper SQL → database tables
- **Runtime Debugging** — Diagnose issues by tracing user interactions through the same stack

Both workflows share the same tech stack knowledge (Vue 2, Spring Boot, MyBatis, Oracle) and project structure patterns.

---

## Section A: Codebase Tracing

### Core Approach

From 5 dimensions extract data, then cross-match to produce complete chains:

```
Frontend router (router.js) → Vue components (views/*.vue) → API functions (src/api/*.js)
    → Backend Controller (@XxxMapping) → Mapper XML (namespace + SQL)
```

### Steps

#### [1/5] Extract Mapper XML SQL and Table Names

```python
# Key pattern: ${schema}.TABLE_NAME
for m in re.finditer(r'\$\{schema\}\.([A-Za-z_]\w*)', body):
    tables.add(m.group(1).upper())

# namespace is the bridge between DAO and Mapper
ns_m = re.search(r'namespace="([^"]+)"', content)
```

- namespace format: `com.touchspring.lomkpi.dao.QualityDao`
- Extract each `<select|insert|update|delete id="methodName">` SQL
- Clean XML tags: `re.sub(r'<[^>]+>', ' ', body)`

#### [2/5] Match DAO Interface to Mapper Namespace

```python
# Exact match by class name
for ns in mapper_sql:
    if cls in ns or ns.endswith('.' + cls):
        dao_ns[cls] = ns
```

#### [3/5] Extract Controller API Endpoints and Mapper Calls

**Key finding**: Many Controllers inject Mapper directly (bypassing Service layer).

```python
# Find injected Mapper/Dao variables
for m in re.finditer(r'(?:private\s+|final\s+)?(\w+(?:Mapper|Dao|DAO))\s+(\w+)', content):
    mtype, mvar = m.group(1), m.group(2)
```

**Variable type fuzzy match** (important pitfall):
- `IehsSafetyMapper` variable name is `iehsSafetyMapper`
- `QualityDao` variable name is `qualityDao`
- Must strip Mapper/Dao suffix before matching

**Method body extraction**: Use brace counting to find method boundaries:

```python
depth = 1
for ci in range(body_start, min(body_start+5000, len(content))):
    if content[ci] == '{': depth += 1
    elif content[ci] == '}': depth -= 1
    if depth == 0: break
```

**Don't miss JdbcTemplate raw SQL**:
```python
for jm in re.finditer(r'(?:execute|query|queryForRowSet|update)\s*\(\s*[\"\']([^\"\']+)', body):
```

#### [4/5] Extract Frontend API Functions and URLs

```python
for block in re.split(r'export\s+function\s+', content)[1:]:
    func_name = re.match(r'(\w+)', block).group(1)
    url = re.search(r'VUE_APP_BASE_URL\}/([^\"`\s?]+)', block).group(1)
```

#### [5/5] Extract Vue Component API Imports

```python
for m in re.finditer(r'import\s*\{([^}]+)\}\s*from\s*[\"\'].*?/api/(\w+)', content):
    imported_funcs = m.group(1).split(',')
```

### Matching Strategy

1. **Exact match**: API path == Controller endpoint
2. **Prefix match**: Controller class_path + method_path combination
3. **Path variable**: `${xxx}` replaced with `[^/]+` regex
4. **Fuzzy match**: Strip `-` and `/` then keyword-match Vue component to route

### Batch Data Lineage Mapping (Large Codebases)

When page count >20, use `execute_code` to build in-memory index for batch cross-matching.

```python
# 1. API file index: parse all src/api/*.js export functions → URL
# 2. Controller index: parse all @XxxMapping → path + injected Mapper
# 3. Mapper index: parse all Mapper XML FROM/JOIN → table names
# 4. Router index: extract path → component mapping from router.js
```

**Mapper name matching pitfall**: Java uses PascalCase (`UExecutionRateMapper`), XML uses camelCase (`uExecutionRateMapper.xml`). Must normalize case:

```python
key = f.replace('.xml', '').replace('Mapper', '').lower()
```

### Output Format

**Per-page format** (default, for <20 pages):
```
Route: /xxx    Component: Xxx.vue
  ▸ API → Controller → Mapper → Table
```

**By business domain** (for >20 pages or manual reference):
```
## Dock / 月台
Entry: /dock

  Dock Lead Time / 月台 Lead Time
    API: grLeadTime.js

  Dock Utilization / 月台占用率
    API: goodsReceiptApi.js
    Controller: DkUtilizationTargetController.java
    Table: DK_UTILIZATION_TARGET, LOI_MV_OPEN_TO_DETAILS
```

**Database view index** (reverse lookup):
```
LOI_V_OVER_2Y_STOCK → Used by: WHLoiOver2yStockController → /ware-house (download)
```

### Sub-component Recursive Tracking

When each sub-page/sub-function needs coverage:

1. Scan main page's sub-component imports
2. Scan sub-components' API imports
3. Merge main + all sub-component API files, trace uniformly
4. Handle path differences: sub-components may be in `views/Xxx/` or `components/`

### Oracle View Dependency Resolution (View → Base Table Expansion)

Mapper SQL references many views (`LOI_V_*`) or materialized views (`LOI_MV_*`). To get true data sources, recursively expand view definitions to base tables.

```python
def get_base_tables(name, visited=None):
    if visited is None: visited = set()
    if name in visited: return set()  # prevent cycles
    visited.add(name)
    base = set()
    for ref in view_deps[name]:
        if ref in tables:      base.add(ref)       # base table
        elif ref in view_deps: base.update(get_base_tables(ref, visited))  # view, recurse
        else:                  base.add(ref)       # unknown, treat as base
    return base
```

### Multi-Source Cross-Reference

When 2+ data sources exist (code scan, PDF manual, DB direct query), cross-reference to find blind spots:

```python
in_db_not_doc = db_tables - doc_tables
in_doc_not_db = doc_tables - db_tables
common = db_tables & doc_tables  # highest confidence
```

### Role Boundary

For data lineage/manual tasks, agent's role is **knowledge organizer**, not **ops advisor**:
- ✅ Organize data lineage, cross-reference, find gaps
- ✅ Output structured mapping relationships
- ❌ Proactively suggest refresh SQL, fix recommendations, ops actions
- ❌ Infer "next steps" when not asked

---

## Section B: Runtime Debugging

### Core Principle

**Start tracing from the user interaction end, don't spin in backend code.**

When user reports "frontend button/function has issues", must check both frontend and backend.

### Phase 1: Locate Frontend Trigger [Priority]

1. Find frontend page component (search by page title, button text, route path)
2. Find button's event handler
3. Determine API endpoint path and parameters
4. Confirm data flow: how frontend processes API response

**Search tips**:
- Vue: search `@click`, `export`, `download`, `window.open`
- API files: search under `api/` directory
- Routes: search `router/` directory for page-component mapping

### Phase 2: Trace Backend Interface

1. Find Controller from frontend API path
2. Trace Controller → Service → DAO → Mapper XML
3. Find actual SQL query
4. Check query conditions, parameter passing

### Phase 3: Data Verification

1. Check if DB view/table has data
2. Verify schema config (dev vs prod)
3. Check if scheduled tasks have refreshed data

### Common Debug Patterns

#### Download Excel — Headers Only, No Data

**Root cause chain**: Frontend `window.open('/api/excel-xxx')` → Controller queries DAO → SQL returns empty list → Excel writes only headers

**Investigation order**:
1. Frontend: confirm API path (`grep -r "window.open" src/views/`)
2. Backend: find Controller's query method and Mapper XML
3. SQL: confirm table/view has data (`SELECT COUNT(*)`)
4. Object type: use `ALL_OBJECTS` to confirm table vs view
5. ETL dependency: if no INSERT in Java code, data comes from external ETL
6. Config: confirm prod schema config
7. Logs: check app logs for ORA errors

**Easy-to-miss pitfalls**:
- Frontend download may depend on page-loaded data (e.g. `/wh-overview`), not the download endpoint itself
- Table names starting with `V_` aren't necessarily views — verify with `ALL_OBJECTS`
- Manual querying INVALID views triggers Oracle auto-recompile, causing "tests pass but app fails"

#### Page Shows Blank

**Root cause chain**: Frontend mounted → API call → returns empty data → renders empty

1. Frontend: which API does mounted/created lifecycle call
2. Backend: API's ResultData structure
3. Frontend: data binding key mismatch

### Oracle Database Common Issues

#### Oracle View Returns 0 Rows (VALID but empty)

**Symptom**: Java app query returns empty, but manual SQL has data.
**Root cause**: View is VALID but internally needs recompilation.

```sql
-- Check view status
SELECT OBJECT_NAME, STATUS FROM ALL_OBJECTS WHERE OBJECT_NAME = 'VIEW_NAME' AND OWNER = 'SCHEMA';

-- Compare row counts
SELECT COUNT(*) FROM SCHEMA.VIEW_NAME;          -- App sees this
SELECT COUNT(*) FROM (view_definition_SQL);     -- Manual sees this

-- If step2=0 but step3>0, recompile
ALTER VIEW SCHEMA.VIEW_NAME COMPILE;
```

#### Oracle View INVALID State

**Symptom**: Java app returns empty, manual SQL has data.
**Root cause**: Base table structure change made view INVALID.

```sql
-- Check status
SELECT OBJECT_NAME, STATUS FROM ALL_OBJECTS WHERE OBJECT_NAME = 'VIEW_NAME' AND OWNER = 'SCHEMA';

-- Trigger auto-recompile
SELECT * FROM SCHEMA.VIEW_NAME WHERE ROWNUM <= 1;

-- If error, check base table
DESC SCHEMA.BASE_TABLE;
```

#### ORA-00942: table or view does not exist

**Symptom**: Page data load fails, nginx shows `upstream timed out`.
**Root cause**: View doesn't exist or no permission.

```sql
SELECT OBJECT_NAME, STATUS FROM ALL_OBJECTS WHERE OBJECT_NAME = 'VIEW_NAME' AND OWNER = 'SCHEMA';
SELECT GRANTEE, PRIVILEGE FROM ALL_TAB_PRIVS WHERE TABLE_NAME = 'VIEW_NAME';
```

### Nginx Diagnostic Signals

#### upstream timed out

**Meaning**: nginx can't connect to backend Java app.

```bash
# Check if Java app is running
netstat -ano | findstr :9071
# Check Java process
tasklist | findstr java
# Check app logs
tail -50 /path/to/app.out.log
```

### Log Analysis Workflow

```
D:/lom/lom-dashboard-serve-1.0-RELEASE/logs/
├── app.out.log          # Application stdout
├── app.err.log          # Application stderr
├── app.0.out.log        # Rotated log
└── app.wrapper.log      # Wrapper log
```

```bash
grep -i "ORA-\|error\|exception" app.out.log | tail -20
grep -i "excel-product\|FACT_V_WH" app.out.log
grep -i "table or view does not exist\|ORA-00942" app.out.log
```

### API Testing Tips

- **WSL environment**: When browser can't access internal addresses, use `curl -k`
- **Test download**: `curl -k -o /tmp/test.xls "https://host:port/api/excel-xxx"` then `file` and `strings`
- **Check API response**: `curl -k "https://host:port/api/xxx"` (may need token)

---

## Section C: Project Structure Patterns

### Java Spring Boot + MyBatis
```
controller/XXXController.java  → API entry point
dao/XXXDao.java                → Data access interface
resources/mapper/XXXMapper.xml → SQL definitions
domain/entity/XXX.java         → Entity classes
```

### Vue.js
```
views/XXX/XXX.vue              → Page components
api/xxxApi.js                  → API definitions
components/XXX.vue             → Shared components
```

---

## Section D: User Preferences (PLMS/LOM-KPI)

- **Don't want code changes**: Prefer DB-level fixes (refresh MVs, compile objects, rebuild indexes)
- **Don't want Java restart**: Try browser cache clear, force refresh, check API response first
- **"Retry" signal**: User is impatient — speed up, reduce analysis rounds, give most likely solution immediately
- **CREATE OR REPLACE = code change**: User considers it "modifying code" — prefer `ALTER ... COMPILE`
- **Avoid wide tables**: Use hierarchical indented lists, not multi-column tables. API → Controller → Table in 3 indented levels.

---

## Pitfalls (Combined)

### Tracing Pitfalls
- **50%+ API functions can't auto-match to Controller** — cause: multi-level `@RequestMapping`, path variables, JdbcTemplate dynamic SQL. Manual supplement needed.
- **Service layer indirect calls** — some Controllers call DAO via Service, need extra Service file reading
- **schema parameter**: Uses `@Value("${lom-kpi.schema}")`, all table names have `${schema}` prefix
- **Vue CLI 3 history mode**: All non-API requests fallback to index.html, Swagger/Actuator paths unavailable
- **Download button tracking trap**: Same page may have multiple download buttons calling different interfaces. Must trace `@click` → method → `window.open()` or API call
- **Download empty ≠ Bug**: Verify DB has matching data first
- **Mapper case mismatch**: Java PascalCase vs XML camelCase — must normalize

### Debug Pitfalls
- **Locate Vue component by page title, not filename**: Same project may have similar components
- **Confirm API path before analyzing backend**: Don't assume first reasonable endpoint is correct
- **Table names starting with V_ aren't always views**: Need `ALL_OBJECTS` to confirm
- **ETL dependency tables empty is common root cause**: No INSERT in Java code = external ETL
- **Oracle auto-recompile trap**: Manual query of INVALID view triggers recompile, causing "tests pass but app fails"
- **Same-name TABLE and MATERIALIZED VIEW conflict**: Oracle allows both; `ALL_OBJECTS` shows two rows
- **ORA-00909 hidden root cause**: OR precedence issues — `AND a = 1 OR b = 2 AND c = 3` parsed unexpectedly
- **MV refresh may succeed even with SQL issues**: ORA-00909 only affects compilation in some Oracle versions

### General Pitfalls
- Don't search backend code aimlessly — start from frontend to determine API path
- Check both .out.log and .err.log when reviewing logs
- nginx upstream timeout could be Java crash or DB connection issue
- MyBatis `${schema}` is string substitution, not parameter binding

---

## Reference Files

### Codebase Tracing References
- `references/oracle-view-parsing.md` — View/MV recursive expansion to base tables
- `references/plms-project-structure.md` — PLMS project directory structure
- `references/plms-data-lineage.md` — Complete data lineage mapping (77 routes → Controller → Mapper → Table)
- `references/plms-database-dictionary.md` — Database dictionary: 14 MV refresh strategies, key view SQL logic, source table dependencies
- `references/open-to-traffic-lights.md` — Open TO traffic light thresholds (14 business types)
- `references/oracle-metadata-sql.md` — Oracle metadata retrieval SQL

### Debug References
- `references/oracle-materialized-view-ora00909.md` — MV ORA-00909 diagnosis and no-code fix
- `references/oracle-invalid-view-debugging.md` — Oracle view INVALID state diagnosis and fix
- `references/java-oracle-excel-download-debug.md` — Excel download headers-only complete debug flow
- `references/lom-dashboard-debug-notes.md` — LOM Dashboard project debug notes (architecture, tables, known issues)
- `references/lom-warehouse-download-debug-flow.md` — Bonded WH download button no-data debug flow

### Scripts
- `scripts/plms_tracer.py` — PLMS codebase tracing automation script
