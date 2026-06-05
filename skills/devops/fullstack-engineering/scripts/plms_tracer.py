#!/usr/bin/env python3
"""
Fullstack Codebase Tracer - PLMS/LOM-KPI 专用模板
可适配其他 Spring Boot + MyBatis + Vue 项目

用法: 修改路径常量后直接运行
输出: 控制台统计 + 文件报告
"""

import re, os, sys

# ===== 配置 - 按项目修改 =====
BACKEND_MAIN = "/path/to/src/main"
CTRL_DIR = f"{BACKEND_MAIN}/java/com/xxx/controller"
DAO_DIR = f"{BACKEND_MAIN}/java/com/xxx/dao"
MAPPER_DIR = f"{BACKEND_MAIN}/resources/mapper"
API_DIR = "/path/to/frontend/src/api"
VUE_DIR = "/path/to/frontend/src/views"
ROUTER_FILE = "/path/to/frontend/src/router.js"
OUTPUT_FILE = "PLMS完整调用链.txt"
SCHEMA_VAR = "${schema}"  # MyBatis schema 占位符

# ===== 1. Mapper XML: namespace -> {method -> {sql, tables}} =====
def extract_mapper_sql(mapper_dir):
    mapper_sql = {}
    mapper_ns_list = {}
    for fname in sorted(os.listdir(mapper_dir)):
        if not fname.endswith('.xml'): continue
        with open(os.path.join(mapper_dir, fname), 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        ns_m = re.search(r'namespace="([^"]+)"', content)
        if not ns_m: continue
        ns = ns_m.group(1)
        mapper_ns_list[ns.split('.')[-1]] = ns
        for m in re.finditer(r'<(select|insert|update|delete)\s+id="(\w+)"[^>]*>(.*?)</\1>', content, re.DOTALL):
            tag, mid, body = m.group(1), m.group(2), m.group(3)
            tables = sorted(set(
                tm.group(1).upper()
                for tm in re.finditer(r'\$\{schema\}\.([A-Za-z_]\w*)', body)
            ))
            sql = re.sub(r'<[^>]+>', ' ', body).strip()
            sql = re.sub(r'\s+', ' ', sql).strip()[:1000]
            mapper_sql.setdefault(ns, {})[mid] = {'tag': tag, 'sql': sql, 'tables': tables}
    return mapper_sql, mapper_ns_list

# ===== 2. DAO -> namespace =====
def map_dao_to_ns(dao_dir, mapper_sql):
    dao_ns = {}
    if not os.path.exists(dao_dir): return dao_ns
    for fname in sorted(os.listdir(dao_dir)):
        if not fname.endswith('.java'): continue
        with open(os.path.join(dao_dir, fname), 'r', encoding='utf-8', errors='ignore') as f:
            c = f.read()
        cls_m = re.search(r'public\s+interface\s+(\w+)', c)
        if not cls_m: continue
        cls = cls_m.group(1)
        for ns in mapper_sql:
            if cls in ns or ns.endswith('.' + cls):
                dao_ns[cls] = ns; break
    return dao_ns

# ===== 3. Namespace resolver =====
def make_ns_resolver(dao_ns, mapper_ns_list):
    def find_ns(type_name):
        if type_name in dao_ns: return dao_ns[type_name]
        base = type_name.replace('Mapper','').replace('Dao','')
        for cls, ns in dao_ns.items():
            cls_base = cls.replace('Mapper','').replace('Dao','')
            if cls_base == base or cls_base.lower() == base.lower(): return ns
        for short, ns in mapper_ns_list.items():
            short_base = short.replace('Mapper','').replace('Dao','')
            if short_base == base or short_base.lower() == base.lower(): return ns
        return None
    return find_ns

# ===== 4. Controller analysis =====
def analyze_controllers(ctrl_dir, find_ns, mapper_sql):
    ctrl_methods = {}
    for fname in sorted(os.listdir(ctrl_dir)):
        if not fname.endswith('.java'): continue
        with open(os.path.join(ctrl_dir, fname), 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        ctrl = fname.replace('.java','')
        class_path = ""
        m = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', content)
        if m: class_path = m.group(1).rstrip('/')
        
        # Mapper/Dao variables
        var_ns = {}
        for m in re.finditer(r'(?:private\s+|final\s+)?(\w+(?:Mapper|Dao|DAO))\s+(\w+)', content):
            mtype, mvar = m.group(1), m.group(2)
            ns = find_ns(mtype)
            if ns: var_ns[mvar] = ns
        
        # Endpoint methods
        pat = r'@(Get|Post|Put|Delete|Request)Mapping\s*\(([^)]*)\)\s*(?:@\w+[^)]*\)\s*)*(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(([^)]*)\)\s*\{'
        for m in re.finditer(pat, content):
            mtype, aargs, mname = m.group(1), m.group(2), m.group(3)
            bstart = m.end()
            pm = re.search(r'["\']([^"\']+)["\']', aargs)
            path = pm.group(1).rstrip('/') if pm else ''
            fp = (class_path + '/' + path).rstrip('/') if class_path else path
            if not fp: fp = '/'
            
            depth, bend = 1, bstart
            for ci in range(bstart, min(bstart+5000, len(content))):
                if content[ci] == '{': depth += 1
                elif content[ci] == '}': depth -= 1
                if depth == 0: bend = ci; break
            body = content[bstart:bend]
            
            calls = []
            for cm in re.finditer(r'(\w+)\.(\w+)\s*\(', body):
                var, mid = cm.group(1), cm.group(2)
                if var in var_ns:
                    ns = var_ns[var]
                    if ns in mapper_sql and mid in mapper_sql[ns]:
                        si = mapper_sql[ns][mid]
                        calls.append({'mapper': f"{var}.{mid}", 'sql': si['sql'], 'tables': si['tables'], 'tag': si['tag']})
            
            for jm in re.finditer(r'(?:execute|query|queryForRowSet|update)\s*\(\s*["\']([^"\']+)', body):
                st = jm.group(1)
                tbls = sorted(set(tm.group(1).upper() for tm in re.finditer(r'\$\{schema\}\.([A-Za-z_]\w*)', st)))
                calls.append({'mapper': 'JdbcTemplate', 'sql': st[:500], 'tables': tbls, 'tag': 'raw_sql'})
            
            ctrl_methods.setdefault(ctrl, []).append({
                'path': '/'+fp.lstrip('/'), 'type': mtype, 'method': mname, 'calls': calls
            })
    return ctrl_methods

# ===== 5. Frontend API functions =====
def extract_api_funcs(api_dir):
    api_func_map = {}
    for fname in sorted(os.listdir(api_dir)):
        if not fname.endswith('.js'): continue
        with open(os.path.join(api_dir, fname), 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        for block in re.split(r'export\s+function\s+', content)[1:]:
            fm = re.match(r'(\w+)', block)
            if not fm: continue
            um = re.search(r'VUE_APP_BASE_URL\}/([^"`\s?]+)', block)
            if um: api_func_map[fm.group(1)] = (fname.replace('.js',''), '/' + um.group(1))
    return api_func_map

# ===== 6. Vue component -> API funcs =====
def extract_vue_apis(vue_dir):
    comp_apis = {}
    for root, dirs, files in os.walk(vue_dir):
        for fname in files:
            if not fname.endswith('.vue'): continue
            with open(os.path.join(root, fname), 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            funcs = set()
            for m in re.finditer(r'import\s*\{([^}]+)\}\s*from\s*["\'].*?/api/(\w+)', content):
                for f in m.group(1).split(','):
                    f = f.strip().split(' as ')[0].strip()
                    if f and re.match(r'\w+', f): funcs.add(f)
            if funcs: comp_apis[fname] = funcs
    return comp_apis

# ===== 7. Route -> component =====
def extract_routes(router_file):
    with open(router_file, 'r', encoding='utf-8', errors='ignore') as f:
        rc = f.read()
    route_comp = {}
    for block in re.findall(r'\{(.*?)\}', rc, re.DOTALL):
        pm = re.search(r'path:\s*["\']([^"\']+)', block)
        if not pm: continue
        cm = re.search(r'views/([^"\')+]+)', block)
        if cm: route_comp[pm.group(1)] = cm.group(1)
        elif 'Home' in block: route_comp[pm.group(1)] = 'HomeNew.vue'
    return route_comp

# ===== 8. Match API path -> Controller =====
def make_chain_lookup(ctrl_methods):
    lookup = {}
    for ctrl, methods in ctrl_methods.items():
        for mi in methods: lookup[mi['path']] = (ctrl, mi)
    return lookup

def find_chain(api_path, lookup):
    base = api_path.rstrip('/')
    if base in lookup: return lookup[base]
    best, best_len = None, 0
    for ep, val in lookup.items():
        ep_c = ep.rstrip('/')
        if base.startswith(ep_c) and len(ep_c) > best_len: best = val; best_len = len(ep_c)
        elif ep_c.startswith(base) and len(base) > 3 and len(base) > best_len: best = val; best_len = len(base)
    return best

# ===== MAIN =====
if __name__ == '__main__':
    print("Extracting mapper SQL...")
    mapper_sql, mapper_ns_list = extract_mapper_sql(MAPPER_DIR)
    print(f"  {len(mapper_sql)} namespaces, {sum(len(v) for v in mapper_sql.values())} SQL methods")
    
    print("Mapping DAO -> namespace...")
    dao_ns = map_dao_to_ns(DAO_DIR, mapper_sql)
    find_ns = make_ns_resolver(dao_ns, mapper_ns_list)
    
    print("Analyzing controllers...")
    ctrl_methods = analyze_controllers(CTRL_DIR, find_ns, mapper_sql)
    total_ep = sum(len(v) for v in ctrl_methods.values())
    with_sql = sum(1 for ms in ctrl_methods.values() for mi in ms if mi['calls'])
    print(f"  {len(ctrl_methods)} controllers, {total_ep} endpoints, {with_sql} with SQL chain ({with_sql*100//total_ep}%)")
    
    print("Extracting frontend API functions...")
    api_funcs = extract_api_funcs(API_DIR)
    print(f"  {len(api_funcs)} API functions")
    
    print("Extracting Vue component imports...")
    vue_apis = extract_vue_apis(VUE_DIR)
    print(f"  {len(vue_apis)} Vue components with API imports")
    
    print("Extracting routes...")
    routes = extract_routes(ROUTER_FILE)
    print(f"  {len(routes)} routes")
    
    lookup = make_chain_lookup(ctrl_methods)
    print(f"\nDone. Use find_chain(api_path, lookup) to trace any API call.")
