# 跨项目数据库对象管理

## 概述

PLMS 和 I4.0 共用同一个 Oracle 实例 LOGPOE。数据库对象（表/视图/MV/存储过程）是共享资源，不应绑定到单个项目目录。

## 目录结构

```
knowledge/
├── _database/LOGPOE/                     ← 公共资源
│   ├── _index.md                         ← 全库索引 + 关系图
│   ├── LTAP_LTAK_POE_table_definition.sql
│   ├── LOI_V_LTAP_EXPORT_view_definition.sql
│   └── ...
│
├── PLMS数据梳理/
│   ├── 02_数据库/                        ← 文档型（字典/速查/详解）
│   └── 07_数据库代码/
│       └── _plms_objects.md              ← PLMS 引用清单
│
└── I4.0/
    └── 07_数据库代码/
        └── _i4_objects.md                ← I4.0 引用清单
```

## _index.md 模板

```markdown
# LOGPOE 数据库对象索引

## 数据库信息
- 实例: LOGPOE
- 类型: Oracle
- 用途: PLMS/I4.0 共用数据源

---

## 对象清单

| 对象名 | 类型 | 行数 | 刷新频率 | 最后刷新 | 使用项目 | 文件 |
|--------|------|------|----------|----------|----------|------|
| LTAP_LTAK_POE | TABLE | 38,325,890 | 实时 | - | PLMS, I4.0 | LTAP_LTAK_POE_table_definition.sql |
| LOI_V_LTAP_EXPORT | VIEW | 8,875,935 | 每次查询执行 | - | PLMS | LOI_V_LTAP_EXPORT_view_definition.sql |
| LOI_V_LOM_PICK_TO | MV | 5,357 | 每小时 | 2022-12-20 (过期) | PLMS | LOI_V_LOM_PICK_TO_mv_definition.sql |

---

## 依赖关系图

LTAP_LTAK_POE (TABLE, 3830万行)
  └── LOI_V_LTAP_EXPORT (VIEW, 887.6万行)
       └── LOI_V_LOM_PICK_TO (MV, 5357行)

MSEG_POE (TABLE, 3000万行)
  └── LOI_V_MSEG_EXPORT (VIEW)
       └── EXPORT_MSEG (MV)

---

## 按项目使用统计

### PLMS
- 表: 20 个
- 视图: 489 个
- 物化视图: 53 个
- 存储过程: 26 个

### I4.0
- 表: 15 个
- 视图: 252 个
- 物化视图: 20 个
- 存储过程: 10 个

---

## 待补充对象

- [ ] LTAP_LTAK_POE_table_definition.sql
- [ ] MSEG_POE_table_definition.sql
- [ ] LOI_V_LOM_PICK_TO_mv_definition.sql
```

## 单对象详情模板

### 表 (TABLE)
```markdown
## {表名}

- 类型: TABLE
- 行数: (实测)
- 分区: (是否分区表，分区键，分区数量)
- 索引: (索引名 + 列)
- 使用项目: PLMS / I4.0
- 备注:
```

### 视图 (VIEW)
```markdown
## {视图名}

- 类型: VIEW
- 行数: (实测)
- 依赖表: (上游表列表)
- 使用项目: PLMS / I4.0
- 备注: (性能问题、优化方案等)
```

### 物化视图 (MV)
```markdown
## {物化视图名}

- 类型: MATERIALIZED VIEW
- 行数: (实测)
- 刷新频率: 每小时 / 每天 / 每次查询
- 最后刷新: (日期)
- 状态: FRESH / STALE / NEEDS_COMPILE / COMPILATION_ERROR
- 依赖对象: (上游表/视图)
- 使用项目: PLMS / I4.0
- 备注:
```

### 存储过程 (PROCEDURE)
```markdown
## {存储过程名}

- 类型: PROCEDURE
- 参数: (输入/输出参数)
- 调用频率: (定时任务/手动/应用调用)
- 使用项目: PLMS / I4.0
- 备注:
```

## 项目引用文件模板

`PLMS数据梳理/07_数据库代码/_plms_objects.md`:

```markdown
# PLMS 数据库对象引用

> 详细定义见: ../../_database/LOGPOE/

## 核心对象

| 对象名 | 类型 | 用途 | 问题 |
|--------|------|------|------|
| LTAP_LTAK_POE | TABLE | TO主表 | 3830万行 |
| LOI_V_LTAP_EXPORT | VIEW | Export导出 | 504超时 (2分10秒) |

## 依赖关系

LTAP_LTAK_POE
  └── LOI_V_LTAP_EXPORT (504超时)
       └── LOI_V_LOM_PICK_TO

## PLMS 专属对象清单
> 待补充: PLMS 使用的完整对象列表
```

## 关键原则

1. **数据库层与项目层分离** — 对象定义在 `_database/LOGPOE/`，项目只放引用
2. **单对象详情必须包含刷新元数据** — 刷新频率、最后刷新时间、状态
3. **行数必须实测** — `SELECT COUNT(*)` 确认，不能用估算值
4. **依赖关系必须记录** — 表→视图→MV→存储过程的链式依赖
5. **多项目共用时标注使用方** — 便于后续影响分析
