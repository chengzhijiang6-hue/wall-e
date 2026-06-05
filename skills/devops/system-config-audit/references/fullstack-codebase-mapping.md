# Full-Stack Codebase Mapping Methodology

## Purpose
Given a full-stack project (Vue frontend + Java Spring Boot backend + MyBatis ORM), produce a structured mapping: **Frontend Page → API File → API Path → Controller → Mapper XML → Database Table**.

## Applicable Stack
- Frontend: Vue 2/3 (Vue Router, Vuex, Axios, Element UI)
- Backend: Java Spring Boot (MyBatis, Maven)
- Database: Oracle / MySQL / SQL Server
- Deployment: Single-port monolith (frontend static assets served by Spring Boot)

## Step-by-Step Extraction

### Step 1: Extract Frontend Routes
**File**: `src/router.js` or `src/router/index.js`

```python
import re
with open('router.js', 'r') as f:
    content = f.read()
routes = {}
for m in re.finditer(r'path:\s*["\']([^"\']+)["\']', content):
    route = m.group(1)
    # Find component import after this route definition
    pos = m.end()
    comp_match = re.search(r'import\s*\(\s*["\']\.?\.?/?views/([^"\']+)', content[pos:pos+300])
    routes[route] = comp_match.group(1) if comp_match else ''
```

### Step 2: Extract Frontend API Files
**Directory**: `src/api/`

Each API file exports functions that call `fetch()` or `axios`. The base URL is typically `process.env.VUE_APP_BASE_URL` (set to `/api` in `.env.development`).

```python
import re, os
api_dir = "src/api"
api_files = {}
for fname in os.listdir(api_dir):
    if not fname.endswith('.js'): continue
    with open(os.path.join(api_dir, fname)) as f:
        content = f.read()
    apis = set()
    # Pattern: VUE_APP_BASE_URL}/endpoint
    for m in re.finditer(r'VUE_APP_BASE_URL\}/([^"`\s?]+)', content):
        apis.add('/' + m.group(1))
    if apis:
        api_files[fname.replace('.js','')] = sorted(apis)
```

### Step 3: Extract Backend Controller Endpoints
**Directory**: `src/main/java/com/.../controller/`

```python
import re, os
ctrl_dir = "src/main/java/com/.../controller"
ctrl_endpoints = {}

for fname in os.listdir(ctrl_dir):
    if not fname.endswith('.java'): continue
    with open(os.path.join(ctrl_dir, fname)) as f:
        content = f.read()
    
    ctrl_name = fname.replace('.java','')
    
    # Class-level @RequestMapping
    class_path = ""
    m = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', content)
    if m: class_path = m.group(1).rstrip('/')
    
    # Method-level @XxxMapping
    for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']', content):
        path = m.group(2).rstrip('/')
        full_path = (class_path + '/' + path).rstrip('/') if class_path else path
        ctrl_endpoints['/' + full_path.lstrip('/')] = ctrl_name
```

### Step 4: Extract Database Tables from MyBatis Mapper XMLs
**Directory**: `src/main/resources/mapper/`

```python
import re, os
mapper_dir = "src/main/resources/mapper"
mapper_tables = {}

for fname in os.listdir(mapper_dir):
    if not fname.endswith('.xml'): continue
    with open(os.path.join(mapper_dir, fname)) as f:
        content = f.read()
    
    tables = set()
    # Pattern 1: ${schema}.TABLE_NAME (common in multi-schema Oracle setups)
    for m in re.finditer(r'\$\{schema\}\.([A-Za-z_]\w*)', content):
        tables.add(m.group(1).upper())
    
    # Pattern 2: bare table references in SQL keywords
    # Use known table prefixes to filter out column names and aliases
    known_prefixes = ('LOI_', 'LOM_', 'SAP_', 'GR_', 'DK_', 'V_', 'U_', ...)
    for m in re.finditer(r'(?:FROM|JOIN|INTO|UPDATE)\s+([A-Za-z_]\w*)', content, re.IGNORECASE):
        t = m.group(1).upper()
        if any(t.startswith(p) for p in known_prefixes):
            tables.add(t)
    
    if tables:
        mapper_tables[fname.replace('Mapper.xml','').replace('Dao.xml','')] = sorted(tables)
```

### Step 5: Extract Controller → DAO/Service References
```python
for fname in os.listdir(ctrl_dir):
    if not fname.endswith('.java'): continue
    with open(os.path.join(ctrl_dir, fname)) as f:
        content = f.read()
    
    daos = set()
    for m in re.finditer(r'(?:private|@Autowired)[^;]*?(\w+Dao)\b', content):
        daos.add(m.group(1))
    for m in re.finditer(r'(?:private|@Autowired)[^;]*?(\w+Service)\b', content):
        daos.add(m.group(1))
```

### Step 6: Join All Layers
Match API paths to controller endpoints (exact match → prefix match), then controller to mapper via DAO references (heuristic string matching).

### Step 7: Group by Business Module
Group the flat mapping by business domain (收货/GR, 发货/GI, 月台/Dock, 仓库/WH, etc.) for human readability.

## Pitfalls

### MyBatis Mapper Parsing
- `${schema}.TABLE_NAME` is the most reliable pattern — always extract this first
- Bare table names in FROM/JOIN clauses need prefix-based filtering to avoid matching column names
- Column names like `ID`, `BASE`, `IN`, `IS`, `CREATE_TIME` look like table names to naive regex — filter by known table prefixes
- `${}` and `#{}` MyBatis placeholders break simple SQL parsing — use the prefix approach instead

### Frontend API Call Patterns
- Vue 2 projects often use wrapper functions (`tspost`, `tsget`, `fetch`) from utility files, NOT direct `axios` calls
- API paths use `process.env.VUE_APP_BASE_URL` as prefix — read `.env.development` to confirm the value
- Some projects use `this.Text` as a dynamic base URL prefix in components

### Controller Path Resolution
- Class-level `@RequestMapping` must be prepended to method-level paths
- Some controllers have no class-level path (method paths are absolute)
- Handle both `@GetMapping` and `@RequestMapping(method=GET)` patterns

### Output
- Generate two files: a **complete version** (all API endpoints) and a **simplified version** (grouped by business module, unique tables per domain)
- Use tab-separated or fixed-width columns for terminal readability
- Include a summary statistics line (total tables, controllers, API files)
