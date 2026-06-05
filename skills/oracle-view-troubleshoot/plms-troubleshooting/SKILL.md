---
name: plms-troubleshooting
description: PLMS 排错知识库构建与维护 — 数据血缘、视图逻辑、排错手册
tags: [plms, oracle, troubleshooting, data-lineage]
triggers:
  - PLMS 排错
  - PLMS 知识库
  - PLMS 视图问题
  - 数据异常排查
---

# PLMS 排错知识库

## 概述

PLMS (Production Logistics Management System) 排错知识库，用于快速定位页面数据异常的根因。

## 知识库位置

```
/mnt/c/Users/CZE8WX/Desktop/knowledge/
├── _database/                            ← 跨项目共享数据库资源
│   └── LOGPOE/
│       ├── _index.md                     ← 全库对象清单 + 关系图
│       └── *.sql                         ← 对象定义文件（表/视图/MV/存储过程）
│
├── PLMS数据梳理/
│   ├── 01_概述/
│   ├── 02_数据库/
│   ├── 07_数据库代码/
│   │   └── _plms_objects.md              ← PLMS 引用清单
│   └── PLMS-LLM-WIKI/
│
├── I4.0/
│   └── 07_数据库代码/
│       └── _i4_objects.md
│
└── llm-wiki/                             ← LLM-Wiki 数据目录（~/llm-wiki）
    ├── raw/docs/
    ├── wiki/
    └── var/chroma/
```

## 已完成工作

### 第一阶段：基础构建 (已完成)

- 179 个数据库对象覆盖
  - SAP 源表 (7)
  - ETL 事实表 (6)
  - 物化视图 (14)
  - 视图 (37)
  - 维度表 (4)
  - 配置表 (8)
  - 业务表 (5)
  
- 数据血缘图谱
  ```
  SAP 源表 (7)         →  ETL 事实表 (6)  →  物化视图 (14)  →  视图 (37)
  SAP WM 表 (4)        →  中间表 (8)      →  配置表 (8)
  维度表 (4)           →  业务表 (5)      →  目标表 (2)
  ```

- PDF 操作手册 (147页, 程志江, 2026-05-27)
  - 已转为图片: `/mnt/c/Users/CZE8WX/Desktop/pdf_pages/page_*.png`
  - 全文提取: `/mnt/c/Users/CZE8WX/Desktop/pdf_pages/all_text.txt` (267KB)

- 前后端代码扫描 (615 组件)
  - Vue2 + SpringBoot2.5 + Oracle

### 第二阶段：SQL 深度整合 (已完成)

目标：页面数据异常时，能从前端一路追到 SQL 层定位根因

用户提供的素材 → 整合后的输出：
```
1. 视图 SQL 定义            → 数据血缘图 (源表→视图→API→页面)
2. 物化视图刷新日志          → 刷新状态监控 + NEEDS_COMPILE 告警
3. 实际查询结果样本          → 数据质量基线 (正常值范围)
4. 排错案例 (你遇到的问题)    → 排错手册 (症状→原因→修复)
5. 存储过程/函数代码          → 业务逻辑文档化
```

**已完成:**
- [✓] 物化视图状态 (86个)
- [✓] 物化视图定义 (30+ 个 LOI_*) → PLMS物化视图定义.md
- [✓] 存储过程/函数列表 (130+ 个)
- [✓] 普通视图 + 物化视图完整定义 (489个对象) → PLMS视图完整定义.md
  - 来源: PLMS血缘.txt (LOGPOE 用户全量导出, 1.4MB)
  - 分类: 31个功能域 (仓库容量/库存/OTD/产出/LZT/AWT/成本/LOP/LIS...)
  - 每个视图: 类型标签 + 源表 + 刷新策略(MV) + SQL定义
- [✓] 存储过程定义 (26个 LOI_P_*) → PLMS存储过程定义.md
  - 来源: SQL Developer USER_SOURCE 导出
  - 包含: LOI_P_INVENTORY_ALL_W_CATEGORY(506行), LOI_P_MATERIAL_CATEGORY(714行), LOI_P_INV_ALL_W_CATEGORY_H(927行)
- [✓] 补充表结构 (20张) → PLMS补充表结构.md
  - 来源: SQL Developer USER_TAB_COLUMNS 导出
  - 包含: LOI_MT_MATERIAL_CATEGORY(212K行), LOI_INVENTORY_ALL_W_CATEGORY(91K行)
- [✓] 补充视图定义 (3个) → PLMS补充视图定义.md
  - LOI_V_LZT_GAP_BACKUP, LOI_V_LZT_GAP_BK, LOI_V_SSC_PVB_STOCK_V1
- [✓] LLM-Wiki 联动 (81 wiki页面 + 483向量块)
- [✓] I4.0 Confluence 交叉关联 (486 PLMS ↔ 252 I4.0, 62个缺失对象已生成补充查询)
- [✓] 排错记录正文提取 (33个 HTML → md → 独立 wiki 页面)
- [✓] 排错记录 frontmatter 元数据 (31个页面)
- [✓] Common-Table_View 提取 (22KB 完整表/视图清单)
- [✓] Redundant-DB-Items 提取 (8KB 冗余对象清单)
- [✓] 自动化更新脚本 (update_plms_kb.py)
- [✓] 物化视图详情文档 (CB$CUBE + EXPORT 物化视图定义、刷新耗时、日志)
- [✓] 数据库深度诊断 (表行数修正、分区信息、执行计划、数据分布)
- [✓] Export 504 完整诊断报告 (plms_export_504_diagnosis.md)
- [ ] 分析 COMPILATION_ERROR 根因 → 修复建议
- [ ] 建立数据质量基线（正常值范围）
- [ ] 积累更多排错案例（症状→原因→修复）

## 关键视图速查

### 物化视图 (14个)

| 视图名 | 刷新周期 | 用途 |
|--------|---------|------|
| LOI_V_WH_OVERVIEW | 4h | 仓库概览 |
| LOI_MV_OPEN_TO_DETAILS | - | Open TO 详情 |
| LOI_MV_DE_MATERIAL_FLOW | - | DE 物料流 |
| LOI_MV_WH_CAPACITY_DETAIL_SD | - | 仓库容量明细 |

### 视图逻辑要点

**交通灯阈值 (LOI_V_OPEN_TO)**
- DE(WX03): OK<3h, REMINDER 3-4h, FAIL>4h
- DE(B304): OK<5h, REMINDER 5-6h, FAIL>6h
- GR直收/翻包/包材: OK<3h, REMINDER 5-6h, FAIL>6h
- RP二级拉动: OK<7h, REMINDER 7-8h, FAIL>8h
- DE样品(RBHP): OK<8h, REMINDER 8-14h, FAIL>14h
- GR超市直送(FCI/R03): OK<12h, REMINDER 12-14h, FAIL>14h

**库位计数规则 (LOI_MV_WH_CAPACITY_DETAIL_SD)**
- AR1 + SU IN (K3,K4,K5): COUNT(HU)*2
- AR1 + SU NOT IN (K3,K4,K5): COUNT(HU)
- 非AR1: COUNT(HU)

**存储天数分段**
0-30, 31-90, 91-180, 181-365, 366-730, >730

## SQL 检索工作流

### 执行方式

在 SQL Developer 中连接 LOGPOE 用户，执行检索脚本，**导出结果为文件**（右键结果 → Export → Text File），保存到 `C:\Users\CZE8WX\Desktop\`，然后告诉 Agent 文件路径。

**禁止逐段返回 SQL 结果** — 效率极低，应一次性导出文件。

### 关键 Pitfall

**ORA-00997: illegal use of LONG datatype**

`user_views.text` 列是 LONG 类型，不能用于 `ORDER BY`、`SUBSTR`、`WHERE` 子句。

```sql
-- 错误写法（报 ORA-00997）
SELECT view_name, SUBSTR(text, 1, 100) FROM user_views ORDER BY view_name;

-- 正确写法（用 DBMS_METADATA）
SELECT view_name, DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS view_ddl
FROM user_views WHERE view_name LIKE 'LOI%' ORDER BY view_name;
```

同理，物化视图定义也用 `DBMS_METADATA.GET_DDL('MATERIALIZED_VIEW', ...)`。

### 检索脚本

已保存到：`/mnt/c/Users/CZE8WX/Desktop/knowledge/PLMS数据梳理/`
- `plms_query.sql` — 基础检索（物化视图状态、视图列表、存储过程）
- `plms_query2.sql` — 高级检索（用 DBMS_METADATA 获取定义）

## 诊断工作流（性能问题专用）

当遇到页面数据加载慢、API 超时等性能问题时，使用以下流程：

```
1. 症状确认
   └─ 哪个页面、什么操作、错误码（504/500/超时）

2. 链路定位
   └─ 前端按钮 → API 路径 → Controller → Mapper → 视图/表

3. 收集诊断数据
   └─ 执行 plms-export-diagnosis.sql（表大小、索引、执行计划、数据分布）

4. 三人小组讨论（正方/反方/架构师）
   └─ 正方: 数据库优化派（索引、物化视图、SQL 优化）
   └─ 反方: 中间件配置派（nginx 超时、连接池、缓存）
   └─ 架构师: 系统设计派（同步改异步、架构重构）

5. 根因定位
   └─ 结合执行计划、数据量、超时配置综合判断

6. 更新知识库
   └─ 更新 PLMS-LLM-WIKI/ 下的对应文件
   └─ 同步到 LLM-Wiki（覆盖已有文件，新增诊断报告）
   └─ rebuild index
```

**Pitfall**：
- 用户拒绝"治标不治本"的方案（如仅改 nginx 超时），必须深入数据库层分析
- 诊断脚本应包含：表行数、索引、分区、列统计、数据分布、执行计划、内存配置
- 三人讨论法适合复杂技术决策，用户喜欢这种分析方式

## 排错流程 (推荐)

```
1. 症状确认
   └─ 页面显示异常数据 / 504 超时 / 数据错误

2. 定位视图
   └─ 查 PLMS逐页面精确映射.txt → 找到对应视图

3. 分阶段诊断 (先收集数据，再分析)

   阶段 1 — 数据量诊断:
     └─ 表行数: SELECT COUNT(*) FROM <基表>
     └─ 视图行数: SELECT COUNT(*) FROM <视图>
     └─ 分区信息: SELECT partition_name, num_rows FROM user_tab_partitions

   阶段 2 — 执行计划诊断:
     └─ EXPLAIN PLAN FOR SELECT ... FROM <视图>
     └─ 检查: PARTITION RANGE ALL? → 未分区裁剪
     └─ 检查: TABLE ACCESS FULL? → 未用索引
     └─ 检查: TEMP TABLE TRANSFORMATION? → CTE 物化导致索引失效

   阶段 3 — 索引诊断:
     └─ SELECT index_name, column_name FROM user_ind_columns WHERE table_name='<基表>'
     └─ 直接查询基表测试: SELECT COUNT(*) FROM <基表> WHERE <条件>
     └─ 对比视图查询时间 vs 基表查询时间

   阶段 4 — 依赖关系诊断:
     └─ SELECT name, type, referenced_name FROM user_dependencies WHERE name='<视图>'
     └─ 确认重命名/删除视图是否影响其他对象

4. 收集所有数据 → 更新知识库 .md 文件 → 同步 LLM-Wiki

5. 方案评估 (三人讨论法):
   └─ 列出所有可行方案
   └─ 标注约束条件 (不修改代码/配置等)
   └─ 评估每个方案的风险和可行性
   └─ 选出最优方案

6. 修复
   └─ 物化视图: DBMS_MVIEW.REFRESH('XXX', 'C');
   └─ 编译失效对象: ALTER ... COMPILE;
   └─ 重命名+新建表+存储过程 (非侵入方案)
```

## Oracle 连接信息

```
服务器: wx0orarac02.apac.bosch.com:38000/bcdlog_app.apac.bosch.com
用户: LOGPOE
```

## SQL 检索脚本

检索脚本存放在知识库目录：
```
/mnt/c/Users/CZE8WX/Desktop/knowledge/PLMS数据梳理/
├── plms_query.sql   — 第一轮（物化视图状态+存储过程列表）
└── plms_query2.sql  — 第二轮（视图DDL用DBMS_METADATA）
```

### 已产出的知识库文件

```
/mnt/c/Users/CZE8WX/Desktop/knowledge/
├── _database/LOGPOE/                     ← 跨项目共享数据库对象
│   ├── _index.md                         ← 全库索引 + 关系图
│   ├── LOI_V_LTAP_EXPORT_view_definition.sql
│   └── ... (待补充)
│
├── PLMS数据梳理/
│   ├── 01_概述/
│   ├── 02_数据库/
│   ├── 07_数据库代码/
│   │   └── _plms_objects.md              ← PLMS 引用清单
│   ├── 06_SQL参考/                       ← 诊断脚本
│   └── PLMS-LLM-WIKI/                   ← LLM-Wiki 素材
```

### Oracle LONG 类型 Pitfall

`USER_VIEWS.TEXT` 列是 LONG 类型，不能用于：
- `ORDER BY`
- `SUBSTR()`
- `WHERE` 条件比较
- `DISTINCT`

报错：`ORA-00997: illegal use of LONG datatype`

**解决方案：** 用 `DBMS_METADATA.GET_DDL('VIEW', view_name, USER)` 替代：
```sql
-- 错误写法
SELECT view_name, SUBSTR(text, 4000, 1) FROM user_views ORDER BY view_name;
-- 正确写法
SELECT view_name, DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS view_ddl
FROM user_views WHERE view_name LIKE 'LOI%' ORDER BY view_name;
```

### 给用户脚本的交付规范

用户说"重试"= 对进度不满，应直接给可执行文件。
- 写 `.sql` 文件到知识库目录，不要内联 SQL 文本
- 用户在 SQL Developer 中按 F5 执行，复制结果返回
- 结果中的 LONG 报错需要立即修复并生成新版脚本
- **不要解释为什么这样做** — 直接给代码，用户会自己理解
- **不要分步骤说明** — 一个文件包含所有需要的查询

### 大量 Oracle 数据收集模式

当需要从 Oracle 收集大量 DDL/数据时：
1. 写一个 `.sql` 文件包含所有查询，用 `PROMPT` 分隔各段
2. 用户执行后复制"脚本输出"窗口内容返回
3. 如果数据量太大（视图 DDL 可能几百个），分批返回：
   - 第一批：物化视图状态 + 物化视图定义（LOI_* 开头）
   - 第二批：普通视图定义（LOI_V_* 开头，按首字母分段）
   - 第三批：存储过程/函数代码
4. 每批结果我整合到知识库后，再给下一批的 SQL

### ⚠️ 用户逐段粘贴的处理（高频陷阱）

如果用户开始逐段粘贴 SQL 结果（每轮只发一行代码），**最多重定向 2 次**。第 2 次后仍继续粘贴，**立即停止请求导出**，直接整合已有数据并跳到下一步。不要无限循环请求导出 — 用户可能无法或不愿导出，继续请求只会浪费轮次。

**识别信号**：用户连续 3+ 轮发送单行 SQL 代码 = 逐段粘贴模式。立即切换策略：
- 承认收到数据
- 告诉用户"已收到，继续返回"
- 等用户返回完毕或主动停止
- 不要重复请求导出 — 用户已经选择了粘贴方式，尊重他的选择

**为什么用户不愿导出**：可能是因为 SQL Developer 导出操作复杂、用户不熟悉、或用户认为逐段返回更方便。无论原因，不要对抗用户的工作方式。

**数据整合时机**：当用户逐段返回了足够多的数据（比如一个完整的视图定义），可以主动整合到知识库，然后询问用户是否继续。

## 表行数修正 (2026-05-29)

⚠️ 之前的估计严重低估，以下为实测数据:

| 表名 | 之前估计 | 实际行数 | 说明 |
|------|---------|---------|------|
| LTAP_LTAK_POE | 1.8M | **38,325,890 (3830万)** | 分区表，按月分区，70+ 分区 |
| MSEG_POE | - | **29,998,205 (3000万)** | 分区表 |
| LTAP_LTAK_POE_GI_TO | 1.8M | 1,818,996 (181万) | 普通表 |
| LTAP_LTAK_POE_OPEN_TO | 729 | 540 | 小表 |

**教训**: 不能用 LTAP_LTAK_POE_GI_TO 的行数推断 LTAP_LTAK_POE，它们是不同的表。

## 物化视图状态快照 (2026-05-27)

```
状态汇总 (86 个物化视图):
├─ FRESH (正常)      :  5 个
├─ UNKNOWN (待确认)  : 17 个
├─ NEEDS_COMPILE     : 53 个 ⚠️
├─ STALE (过期)      :  3 个 ⚠️
└─ COMPILATION_ERROR :  8 个 🔴
```

### COMPILATION_ERROR 物化视图
- CB$CUBE_ACTUAL_BLOCK_STOCK
- CB$CUBE_ACTUAL_STOCK
- CB$PRODUCT_H_PRODUCT
- LOI_V_ASN_REWORK
- LOI_V_AWT_KWT_INV_SUM_UPDATE
- LOP3_ASN_DATA
- MVIEW_MASTER_TEST
- M_V_INVENTORY_KPITREE_LOP3BASE

### STALE 物化视图
- CB$CUBE_LZT — 最后刷新 2024-12-30 (18个月前)
- CB$CUBE_OUTPUT — 最后刷新 2021-07-13 (5年前)
- CB$LOCATION_PROCESS_AREA — 最后刷新 2022-09-02

### 关键业务物化视图状态
- LOI_V_WH_OVERVIEW — FRESH ✓ (4h刷新)
- LOI_MV_WH_CAPACITY_DETAIL_SD — FRESH ✓
- CB$CUBE_TARGET — FRESH ✓
- CB$CUBE_PRODUCT — FRESH ✓
- LOI_MV_OPEN_TO_DETAILS — NEEDS_COMPILE ⚠️
- LOI_MV_DE_MATERIAL_FLOW — NEEDS_COMPILE ⚠️

## 存储过程/函数清单 (已获取)

共 130+ 个存储过程/函数，关键业务对象：
- LOI_DATA_PROCESS (1382行) — 主数据处理
- LOI_P_INVENTORY_ALL_W_CATEGORY (507行) — 库存分类
- LOI_P_MATERIAL_CATEGORY (715行) — 物料分类
- P_GENERAL_FACT_LTAP_LTAK_POE (432行) — TO事实表
- SP_PRODUCTIVITY (370行) — 生产率
- LOI_P_SP_PRODUCTIVITY (329行) — 生产率
- LOI_P_DEMAND_REPORT (275行) — 需求报告
- P_FACT_WH_PRODUCT_DW (228行) — 仓库产品事实表

## 下一步工作

1. [x] 物化视图状态 (86个) — 已获取
2. [x] 物化视图定义 (30+ 个 LOI_*) — 已整合到 PLMS物化视图定义.md
3. [x] 普通视图定义 (489个对象) — 已整合到 PLMS视图完整定义.md
4. [x] 存储过程定义 (26个 LOI_P_*) — 已整合到 PLMS存储过程定义.md
5. [x] 补充表结构 (20张) — 已整合到 PLMS补充表结构.md
6. [x] 补充视图定义 (3个) — 已整合到 PLMS补充视图定义.md
7. [x] I4.0 Confluence 交叉关联 — 已生成 PLMS与I4.0交叉关联.md
8. [x] 排错记录提取 (33个) — HTML → md → 独立 wiki 页面
9. [x] 排错记录 frontmatter (31个) — 结构化元数据提升检索质量
10. [x] LLM-Wiki 联动 — 81 wiki 页面 + 483 向量块
11. [x] 自动化脚本 — update_plms_kb.py
12. [ ] 分析 COMPILATION_ERROR 根因 → 修复建议
13. [ ] 建立数据质量基线（正常值范围）
14. [ ] 积累更多排错案例（症状→原因→修复）

## Pitfalls

1. **Oracle LONG 类型限制**: `user_views.text` 是 LONG 类型，不能用于 ORDER BY/SUBSTR/WHERE。必须用 `DBMS_METADATA.GET_DDL()` 获取视图定义。
2. **数据导出方式**: 禁止逐段返回 SQL 结果。应导出为文件（SQL Developer → Export → Text File），然后告诉 Agent 文件路径。
3. **⚠️ 用户逐段粘贴的处理 (高频陷阱)**：如果用户开始逐段粘贴 SQL 结果（每轮只发一行代码），**最多重定向 2 次**。第 2 次后仍继续粘贴，**立即停止请求导出**，直接整合已有数据并跳到下一步。不要无限循环请求导出 — 用户可能无法或不愿导出，继续请求只会浪费轮次。宁可跳过该数据，也不要陷入 20+ 轮的无效循环。
   
   **识别信号**：用户连续 3+ 轮发送单行 SQL 代码 = 逐段粘贴模式。立即切换策略：
   - 承认收到数据
   - 告诉用户"已收到，继续返回"
   - 等用户返回完毕或主动停止
   - 不要重复请求导出 — 用户已经选择了粘贴方式，尊重他的选择
   
   **为什么用户不愿导出**：可能是因为 SQL Developer 导出操作复杂、用户不熟悉、或用户认为逐段返回更方便。无论原因，不要对抗用户的工作方式。
4. **物化视图刷新顺序**：先刷新基础表的物化视图，再刷新依赖它们的视图。否则会出现编译错误。
5. **权限检查**：`DBMS_METADATA` 需要 `SELECT_CATALOG_ROLE` 或相应权限。如果报权限错误，需要 DBA 授权。
6. **execute_code 中 read_file 返回值不同**：在 `execute_code` 内调用 `from hermes_tools import read_file`，返回的 dict key 不含 `content`，而是 `{'status', 'message', 'path', 'dedup', 'content_returned'}`（content_returned 是 bool）。要读取文件内容，直接用 Python 的 `open()` 而不是 hermes_tools 的 read_file。或者用 `terminal("cat ...")` 获取内容。
7. **PLMS 血缘导出文件解析**：PLMS 血缘.txt 的格式是 `NUMBER.VIEWNAME\t"SQL定义"`，每条记录跨多行，SQL 用双引号包裹。解析时按 `\d+\.\w+\t"` 作为条目分隔符。条目内的 SQL 行以空白开头。文件可能含 BOM 和 CRLF。建议用 execute_code 写 Python 脚本解析后存为 JSON 中间文件，再生成最终 Markdown。
8. **Oracle 索引查询语法**: `USER_IND_COLUMNS` 没有 `UNIQUENESS` 列，需要 JOIN `USER_INDEXES`:
    ```sql
    SELECT i.index_name, i.uniqueness, c.column_name, c.column_position
    FROM user_indexes i
    JOIN user_ind_columns c ON i.index_name = c.index_name
    WHERE i.table_name = 'XXX'
    ORDER BY i.index_name, c.column_position;
    ```
9. **表行数不能跨表推断**: LTAP_LTAK_POE (3830万) ≠ LTAP_LTAK_POE_GI_TO (181万)，虽然名字相似但是完全不同的表。查询前必须 `SELECT COUNT(*) FROM 表名` 确认实际行数。
10. **分区表必须检查分区裁剪**: 执行计划中 `PARTITION RANGE ALL` = 扫描所有分区 = 慢。优化方向是让 WHERE 条件匹配分区键，实现分区裁剪。
11. **增量刷新 (FAST refresh) 限制**: 视图包含 UNION ALL、MINUS、DISTINCT、GROUP BY、分析函数等操作时不支持 FAST 刷新。需要用 `DBMS_MVIEW.EXPLAIN_MVIEW` 或尝试创建来验证。
12. **物化视图刷新频率必须匹配数据更新频率**: 如果源表每小时更新一次，物化视图也应该每小时刷新一次，否则用户拿到的数据会滞后。需要先检查源表的数据更新频率，再决定刷新频率。
13. **用户拒绝"治标不治本"的方案**: 用户明确表示不接受仅改 nginx 超时的方案，要求深入数据库层分析。遇到性能问题时，必须提供数据库层优化方案（分区裁剪、物化视图、SQL 优化），不能只给中间件配置方案。
    → wiki/concepts/*.md (LLM 生成的 wiki 页面)
      → 向量索引 (283 块, 语义检索)
```

### 当前知识库结构

```
/mnt/c/Users/CZE8WX/Desktop/knowledge/
├── _database/                            ← 跨项目共享数据库资源
│   └── LOGPOE/
│       ├── _index.md                     ← 全库对象清单 + 关系图
│       └── *.sql                         ← 对象定义文件
│
├── PLMS数据梳理/
│   ├── 01_概述/
│   ├── 02_数据库/                        ← 文档型（字典/速查/详解）
│   ├── 03_数据映射/
│   ├── 04_调用链/
│   ├── 05_操作手册/
│   ├── 06_SQL参考/                       ← 诊断脚本（plms_query.sql 等）
│   ├── 07_数据库代码/
│   │   └── _plms_objects.md              ← PLMS 引用清单
│   └── PLMS-LLM-WIKI/                   ← 精简版，用于 LLM-Wiki ingest
│
├── I4.0/
│   └── 07_数据库代码/
│       └── _i4_objects.md
│
└── llm-wiki/                             ← LLM-Wiki 数据目录（~/llm-wiki）
    ├── raw/docs/                         ← 素材
    ├── wiki/                             ← 生成的 wiki 页面
    └── var/chroma/                       ← 向量索引
```

### Quartz Wiki (localhost:1313)

PLMS 知识库的可视化站点，使用 Quartz 静态站点生成器，运行在 Docker 容器 `quartz-wiki` 中。

```
容器名:    quartz-wiki
镜像:      quartz-wiki (本地构建)
端口映射:  0.0.0.0:1313 → 8080
状态:      Exited (需要手动启动)
```

**启动命令**: `docker start quartz-wiki`

**Pitfall**:
- quartz-wiki 容器可能因 SIGTERM 或系统重启进入 Exited 状态
- 启动后需等待 ~5 秒让 Quartz 重建页面，然后验证 `curl -s -o /dev/null -w "%{http_code}" http://localhost:1313/`
- 如果返回 200 但页面 404，可能是目录名含点号或 frontmatter YAML 解析失败

### Ingest 工作流

```python
# 1. 准备精简版文件到 PLMS-LLM-WIKI/
# 2. 复制到 raw 目录
cp PLMS-LLM-WIKI/*.md /home/ethan/llm-wiki/raw/docs/

# 3. 逐个 ingest（不要用 ingest_all，大文件会超时）
# MCP: ingest_file("docs/文件名.md")

# 4. 审核
# MCP: review_diffs() → approve_all_diffs(dry_run=False)

# 5. 重建索引
# MCP: build_index()
```

### Frontmatter 元数据模式（提升检索质量的关键）

为 wiki 页面添加 YAML frontmatter 可显著提升 ask_wiki 检索质量。

**格式**：
```yaml
---
views: ["LOI_V_OUTPUT_FULL"]
root_cause: "to_char占位符不足导致版本号乱码"
affected_tables: ["LOI_V_OUTPUT_FULL"]
severity: high
tags: ["oracle","to_char","output","monthly"]
---
```

**效果对比**：
- 无 frontmatter: ask_wiki 只找到标题，给出通用推测
- 有 frontmatter: ask_wiki 找到具体根因和解决方案

**适用场景**：排错记录、故障案例、问题排查指南

**批量添加方法**：
```python
# 在 execute_code 中读取 wiki 页面，检查是否已有 frontmatter
# 如果没有，根据内容分析生成 frontmatter 并 prepend
# 注意：不要改正文内容，只加 frontmatter
```

### Ingest 质量优化

1. **不要合并多个文件为一个**: 合并后 LLM ingest 只生成 1 个 wiki 页面，检索时 chunk 混杂多条记录，质量极差
2. **每个排错记录单独 ingest**: 33 个文件 → 33 个独立 wiki 页面，每个页面有独立的 frontmatter
3. **大文件拆分**: >100KB 的文件拆分为 <50KB 的子文件，按功能域分组
4. **ingest 后必须重建索引**: `build_index()` 才能让新页面被向量检索命中
5. **ingest 后必须审核**: `review_diffs()` → `approve_all_diffs(dry_run=False)` 才会写入 wiki 目录

### Ingest 策略: 覆盖 vs 新增 (2026-05-29 新增)

⚠️ 用户要求确认 ingest 策略，避免数据滞后和杂糅:

```
场景 1: 更新已有文件 (如 10_TO_收发货.md)
  → 覆盖策略: 直接替换 raw/ 下的文件，重新 ingest
  → 原因: 避免数据滞后，确保 wiki 页面是最新的

场景 2: 新增文件 (如 34_export_504_diagnosis.md)
  → 添加策略: 新文件放到 raw/ 下，单独 ingest
  → 原因: 不影响现有内容，新增独立 wiki 页面

场景 3: 更新知识库主文件 (如 PLMS数据库字典.md)
  → 覆盖策略: 更新 PLMS-LLM-WIKI/ 下的对应文件
  → 然后: 复制到 raw/ 并重新 ingest
```

**执行顺序**:
1. 先更新 PLMS-LLM-WIKI/ 下的源文件
2. 复制到 /home/ethan/llm-wiki/raw/docs/
3. ingest_file (覆盖已有文件) 或 ingest_file (新增文件)
4. review_diffs() → approve_all_diffs(dry_run=False)
5. build_index()

### Pitfalls (LLM-Wiki)

1. **ingest 超时**: 单文件 >100KB 可能超时（180s limit）。解决：拆分为 <50KB 的文件。
2. **MCP 断连**: ingest_all 超时后 MCP server 断开，需等 ~60s 自动恢复。
3. **docker-compose v1 不兼容**: `ContainerConfig` KeyError。解决：用 `docker run --env-file .env` 替代。
4. **env 变更不生效**: 修改 .env 后必须 `docker run` 重建容器，`docker restart` 不会重读 env。
5. **search_wiki vs ask_wiki**: search_wiki 是精确文本匹配（英文关键词 OK，中文多词查询常失败）；ask_wiki 是向量检索 + LLM 合成（适合语义查询）。
9. **嵌入模型可独立切换**: LLM 用 mimo，embedding 可用 DashScope text-embedding-v3。需在 providers.py 新增 DashScopeProvider 类。
10. **mimo-embedding 502 错误**: mimo 的 embedding 端点不稳定，返回 502 Bad Gateway。解决方案：切换到 DashScope text-embedding-v3。
11. **MCP 稳定性**: ask_wiki 超时（180s）后 MCP server 可能断连。恢复：`docker restart llm-wiki` + 等 30s。大量 ingest 后建议手动重启容器再 build_index。
14. **llm-wiki .env 变更不生效**: docker-compose 使用 `env_file: .env`，修改 .env 后必须 `docker stop llm-wiki && docker rm llm-wiki && docker run --env-file .env ...` 重建容器。`docker restart` 不会重读 env 文件。`docker-compose up -d` 在 v1 版本可能报 `ContainerConfig` KeyError，直接用 `docker run` 替代。
15. **Frontmatter schema for troubleshooting records**: 排错记录的标准 frontmatter 字段为 `views`（关联视图列表）、`root_cause`（一句话根因）、`affected_tables`（受影响表）、`severity`（high/medium/low）、`tags`（关键词列表）。添加 frontmatter 后 ask_wiki 检索质量显著提升（从通用推测 → 具体根因+方案）。
12. **Quartz Wiki 崩溃/404**: 常见三种故障 — ① LLM 生成重复 frontmatter key 导致 YAML 解析失败（已通过 `_sanitize_frontmatter()` 自动修复）；② 删除目录后 public/ 缓存残留；③ 目录名含点号导致 404。详见 `references/llm-wiki-integration.md` → "Quartz Wiki 可视化" → "Quartz Pitfalls"。
13. **三人小组讨论**: 复杂技术决策时，用户喜欢 3 个不同立场的 Agent 辩论。用 `delegate_task` 并行派发 3 个子 Agent（正方/反方/架构师）。
8. **LLM ingest 摘要过短**: ingest pipeline 的 max_tokens=2048 且 prompt 要求"提炼关键知识"，导致排错记录的 root cause/solution 细节丢失。解决方案：添加 frontmatter 元数据，不改正文。
9. **ask_wiki 合成质量取决于输入结构**: 向量检索能找到正确的 wiki 页面，但 LLM 合成回答时倾向于给出通用表述而非具体事实。frontmatter 元数据能显著改善这一点。
16. **Oracle 索引查询语法**: `USER_IND_COLUMNS` 没有 `UNIQUENESS` 列，需要 JOIN `USER_INDEXES`:
    ```sql
    SELECT i.index_name, i.uniqueness, c.column_name, c.column_position
    FROM user_indexes i
    JOIN user_ind_columns c ON i.index_name = c.index_name
    WHERE i.table_name = 'XXX'
    ORDER BY i.index_name, c.column_position;
    ```
17. **表行数不能跨表推断**: LTAP_LTAK_POE (3830万) ≠ LTAP_LTAK_POE_GI_TO (181万)，虽然名字相似但是完全不同的表。查询前必须 `SELECT COUNT(*) FROM 表名` 确认实际行数。
18. **分区表必须检查分区裁剪**: 执行计划中 `PARTITION RANGE ALL` = 扫描所有分区 = 慢。优化方向是让 WHERE 条件匹配分区键，实现分区裁剪。
19. **CB$CUBE vs EXPORT 物化视图不能混淆**: CB$CUBE_LTAP_LTAK_POE 是汇总 Cube（含 GROUP BY + ROLLUP，只有 WORKLOAD/COUNT_WORKLOAD 统计列），**不能用于导出明细数据**。EXPORT_LTAP 才是明细表（含 TO_ITEM, TO_NUMBER, CREATION_DATE, PROCESS, LOCATION），可以替代 LOI_V_LTAP_EXPORT。但 EXPORT_LTAP 已过期 3 年（最后刷新 2022-12-20），需要手动刷新后才能使用。
20. **物化视图刷新耗时不能低估**: CB$CUBE_LTAP_LTAK_POE 刷新耗时 58.63 分钟，CB$CUBE_MSEG 耗时 55.48 分钟。每小时 COMPLETE 刷新方案需要评估是否可行——如果刷新本身就需要 1 小时，则每小时刷新不可行，应改为每天凌晨刷新。
21. **用户无法修改 Java 代码**: 用户表示"没有办法更改java代码"时，意味着：
    - 不能修改 Mapper XML 中的 SQL
    - 不能修改 Controller 中的 API 路径
    - 可选方案: ①数据库层面操作（重命名视图+创建同名表+同义词、物化视图+同义词）②修改 nginx 配置
    - 用户接受"重命名原视图 → 创建同名表 → 回滚策略"的安全替换方案
    - 用户会提出创造性方案（如同名表+存储过程），先评估可行性，不要直接否定

22. **必须使用已验证数据，不用估算值**: 当记忆中同时存在估算值和实测值时，必须使用实测值。例如 Export 504 的查询时间：执行计划预估 47 秒，但 2026-06-01 实测 2 分 10 秒 (130 秒)。向用户汇报时引用实测值，不要引用预估值。**识别信号**: 如果记忆中有"预估"和"实测"两组数据，永远用"实测"。

23. **CTE 导致索引失效**: WITH 子句（CTE）会被 Oracle 优化器物化为临时表，临时表没有索引，导致后续 UNION ALL 全表扫描。症状：直接查询基表 1 秒，通过 CTE 视图查询 48 秒。诊断：EXPLAIN PLAN 中出现 TEMP TABLE TRANSFORMATION 操作。解决方案：不修改视图定义的替代方案是重命名视图+创建同名表+存储过程刷新+定时任务。

23. **安全视图替换模式 (rename + rollback)**: 
    ```sql
    -- 正向操作
    ALTER VIEW XXX RENAME TO XXX_OLD;           -- 重命名原视图
    CREATE TABLE XXX AS SELECT * FROM XXX_OLD;  -- 创建同名表
    CREATE INDEX ... ON XXX(...);               -- 创建索引
    CREATE PROCEDURE P_REFRESH_XXX AS ...       -- 创建刷新存储过程
    DBMS_SCHEDULER.CREATE_JOB(...);             -- 创建定时任务
    -- 回滚操作 (如果出问题)
    DBMS_SCHEDULER.DROP_JOB('JOB_NAME');
    DROP PROCEDURE P_REFRESH_XXX;
    DROP TABLE XXX;
    ALTER VIEW XXX_OLD RENAME TO XXX;
    ```
    执行前必须检查: 同名对象(user_objects/user_tables/user_scheduler_jobs/user_views)、依赖对象(user_dependencies)、表空间。
22. **增量更新知识库，不要等任务结束**: 用户要求"及时的 update 到 llm-wiki 中，及时的维护原数据和 md 后的相关数据文件"。每收集一批 SQL 结果，应立即更新对应的 .md 文件并同步到 LLM-Wiki，不要等到任务全部完成。
23. **物化视图刷新前必须检查能否替代原视图**: 刷新 EXPORT_LTAP 前，先确认 Java 代码是否使用了这个视图。如果 Java 代码使用的是 LOI_V_LTAP_EXPORT（普通视图），刷新 EXPORT_LTAP 不会解决 504 问题——还需要修改 Java 代码。必须两步都完成才能修复。
24. **知识库增量更新，不要等任务结束**: 用户要求"及时的 update 到 llm-wiki 中，及时的维护原数据和 md 后的相关数据文件"。每收集一批 SQL 结果，应立即：①更新对应的 .md 文件 ②复制到 raw/ 目录 ③ingest + approve + build_index。不要等到任务全部完成才同步。
26. **用户提供 PLMS 对象数据时直接更新，不分析不建议**: 当用户给出具体的行数、耗时等数据（如"LOI_V_LTAP_EXPORT 行数是8875935，耗时2分10秒"），用户期望的是直接更新知识库和 wiki，而不是分析优化方案。用户说"重试"意味着"别分析了，直接做"。正确流程：①更新 wiki 页面（concepts + decisions）②更新 raw 源文件 ③更新知识库源文件 ④re-ingest + approve + build_index。不要主动提优化建议，除非用户明确要求。

27. **重命名视图前必须检查依赖对象**: 重命名视图会导致依赖它的物化视图、其他视图失效。必须先查询 `USER_DEPENDENCIES WHERE referenced_name = 'VIEW_NAME'`。如果存在依赖，需要同时重建依赖对象。
    ```sql
    -- 检查谁依赖了这个视图
    SELECT name, type, referenced_name, referenced_type
    FROM user_dependencies
    WHERE referenced_name = 'LOI_V_LTAP_EXPORT';
    -- 结果: LOI_V_LOM_PICK_TO (MATERIALIZED VIEW) 依赖 LOI_V_LTAP_EXPORT (VIEW)
    -- → 重命名 LOI_V_LTAP_EXPORT 会导致 LOI_V_LOM_PICK_TO 失效
    ```

24. **安全视图替换模式 (rename + rollback)**: 当需要将普通视图替换为同名表（用于性能优化）时：
    ```sql
    -- 正向操作
    ALTER VIEW XXX RENAME TO XXX_OLD;           -- 重命名原视图
    CREATE TABLE XXX AS SELECT * FROM XXX_OLD;  -- 创建同名表
    CREATE INDEX ... ON XXX(...);               -- 创建索引
    CREATE PROCEDURE P_REFRESH_XXX AS ...       -- 创建刷新存储过程
    DBMS_SCHEDULER.CREATE_JOB(...);             -- 创建定时任务

    -- 回滚操作 (如果出问题)
    DBMS_SCHEDULER.DROP_JOB('JOB_NAME');
    DROP PROCEDURE P_REFRESH_XXX;
    DROP TABLE XXX;
    ALTER VIEW XXX_OLD RENAME TO XXX;
    ```
    **Pitfall**:
    - 执行前必须检查同名对象（表、存储过程、定时任务、索引）
    - 执行前必须检查依赖对象（USER_DEPENDENCIES）
    - 建议在业务低峰期执行
    - 备份原视图定义（DBMS_METADATA.GET_DDL）

25. **新创建的同名表不能直接被 Java 代码识别**: 如果将视图重命名为 XXX_OLD，创建同名表 XXX，Java 代码（MyBatis Mapper）仍然可以查询 XXX 表。但存储过程刷新 XXX 表时，需要从 XXX_OLD（原视图）读取数据——如果原视图查询本身就慢（如 47 秒），存储过程也会慢。需要评估刷新耗时是否可接受。

26. **Oracle 新建对象冲突检查清单**: 创建新对象前，必须检查：
    ```sql
    -- 检查同名存储过程
    SELECT object_name, object_type FROM user_objects WHERE object_name = 'XXX';
    -- 检查同名表
    SELECT table_name FROM user_tables WHERE table_name = 'XXX';
    -- 检查同名视图
    SELECT view_name FROM user_views WHERE view_name = 'XXX';
    -- 检查同名定时任务
    SELECT job_name FROM user_scheduler_jobs WHERE job_name = 'XXX';
    -- 检查同名索引
    SELECT index_name FROM user_indexes WHERE index_name = 'XXX';
    -- 检查依赖关系
    SELECT name, type FROM user_dependencies WHERE referenced_name = 'XXX';
    ```

27. **用户会要求验证所有收集的信息是否已持久化**: 用户说"之前的信息呢 今天我汇总了那么多 都检查了吗"——说明用户期望 agent 主动追踪并验证所有收集的信息是否已更新到知识库文件和 LLM-Wiki。应在每次数据收集后给出 checklist，确保没有遗漏。

28. **用户会主动提出创造性解决方案**: 用户提出"创建同名表+存储过程+定时任务"的方案，虽然是新思路但需要评估可行性（如刷新耗时、依赖对象影响）。不要直接否定用户的想法，应先分析再给出建议。

### 自动化脚本
## 参考文件

- `references/oracle-retrieval-queries.sql` — Oracle 检索脚本（物化视图状态、定义、存储过程）
- `references/oracle-export-504-diagnosis.md` — Export 504 超时诊断案例 (表行数修正、分区表、执行计划分析)
- `references/oracle-mv-refresh-strategy.md` — 物化视图刷新策略指南 (COMPLETE vs FAST, 刷新频率选择)
- `references/oracle-partition-optimization.md` — 分区表性能优化 (分区裁剪、分区信息检查)
- `references/mv-refresh-timing-20260601.md` — 物化视图刷新耗时实测数据 (CB$CUBE + EXPORT, 2026-06-01)
- `references/mv-status-analysis-20260527.md` — 物化视图状态分析报告（86个视图）
- `references/loi-v-wh-inventory-all-fcst-definition.sql` — LOI_V_WH_INVENTORY_ALL_FCST 完整定义（仓库库存预测核心视图）
- `references/loi-v-wh-overview-definition.md` — LOI_V_WH_OVERVIEW 定义（仓库概览，含库位计数规则详解）
- `references/plms-view-categorization-rules.md` — PLMS 视图功能分类规则（31个功能域，用于批量导入知识库时自动分类）
- `references/i40-confluence-space.md` — I4.0 Confluence 空间分析（PLMS/LOM Dashboard 页面索引、排错记录、LOI 视图参考）
- `references/i40-plms-cross-reference-20260528.md` — I4.0 ↔ PLMS 交叉分析结果（62个缺失对象、排错记录映射、L2/L3钻取映射）
- `references/llm-wiki-integration.md` — LLM-Wiki 联动详细配置（Docker、providers.py、env、ingest 工作流）
- `references/database-object-management.md` — 跨项目数据库对象管理（目录结构、_index.md 模板、单对象详情模板、项目引用文件）
- `references/oracle-safe-view-replacement.md` — Oracle 安全视图替换模式（rename + rollback，处理依赖物化视图）
- `references/export-504-view-definition-analysis.md` — Export 504 视图定义分析（CTE结构、UNION ALL、MINUS、性能问题根因）

## 数据库诊断 SQL 脚本

```
/mnt/c/Users/CZE8WX/Desktop/knowledge/PLMS数据梳理/06_SQL参考/
├── plms_export_diagnosis.sql      ← Export 504 诊断脚本 (20 个查询)
├── plms_mv_refresh_check.sql      ← 物化视图刷新时间检查脚本
├── plms_fast_refresh_check.sql    ← 增量刷新支持检查脚本
├── plms_mv_plan_confirm.sql       ← 物化视图方案确认 (存储空间/负载/刷新窗口)
├── plms_cube_mv_check.sql         ← CB$CUBE + EXPORT 物化视图定义检查
├── plms_optimization_analysis.sql ← 索引/统计/分区裁剪/查询时间测试
├── plms_check_objects.sql         ← 同名对象冲突检查 (表/视图/存储过程/定时任务/索引/依赖)
├── plms_check_pick_to.sql         ← LOI_V_LOM_PICK_TO 物化视图定义检查
├── plms_query.sql                 ← 基础检索脚本
└── plms_query2.sql                ← 高级检索脚本 (DBMS_METADATA)
```

**plms_export_diagnosis.sql 包含**:
- 表行数统计 (LTAP_LTAK_POE, MSEG_POE, LTAP_LTAK_POE_GI_TO)
- 索引信息 (需要修复 UNIQUENESS 列查询)
- 分区信息 (user_tab_partitions)
- 列统计信息 (user_tab_col_statistics)
- 数据分布 (BDATU 按月, VLTYP/NLTYP TOP 20)
- 视图定义 (DBMS_METADATA.GET_DDL)
- 执行计划 (EXPLAIN PLAN FOR)
- 物化视图状态
- 存储过程列表
- 表大小 (user_segments)
- 并行查询配置
- 内存配置 (SGA/PGA)

**plms_mv_refresh_check.sql 包含**:
- 表数据更新频率 (最近 7 天)
- 今天按小时分布
- 现有物化视图刷新历史
- 物化视图日志
- 定时任务
- 最新数据时间戳
- 数据延迟计算

**plms_fast_refresh_check.sql 包含**:
- 视图 SQL 限制操作检查 (UNION ALL, MINUS, DISTINCT, GROUP BY, 分析函数, 子查询)
- 物化视图日志检查
- 测试增量刷新物化视图
- EXPLAIN_MVIEW 分析
- FACT 表物化视图日志统计

## 案例: Productivity 页面 Export TO / Export Document 504 超时 (2026-05-29)

**症状**: Productivity > Daily Workload & Workhour Overview 页面，点击下载按钮（export TO / export document）后 504 Gateway Timeout

**API 端点**:
- `/api/excel-new-product-lv1-to?creationDate=YYYYMM`
- `/api/excel-new-product-lv1-document?creationDate=YYYYMM`

**数据链路**:
```
前端 Vue2 按钮 → URL 跳转 → nginx(9080) → Java(9071) → ExportToMapper → LOI_V_LTAP_EXPORT → LTAP_LTAK_POE
```

**根因分析 (三人讨论)**:
- 正方(数据库): LOI_V_LTAP_EXPORT 是普通视图（非物化视图），CTE 扫描 181 万行 LTAP_LTAK_POE，20+ UNION ALL 多次扫描
- 反方(nginx): 默认 proxy_read_timeout 60 秒，无配置
- 架构师: 同步导出设计不合理，应改为异步

**时间估算**:
- LTAP_LTAK_POE 扫描: 30-60 秒 (181万行)
- 20+ UNION ALL: 30-60 秒
- Java Excel 生成: 10-20 秒
- 总计: 75-150 秒 > nginx 默认 60 秒 → 504

**修复方案**:
- 方案 A (短期): nginx proxy_read_timeout 300s ← 治标不治本
- 方案 B (中期): 将 LOI_V_LTAP_EXPORT 改为物化视图
- 方案 C (中期): SQL 优化，添加日期过滤下推
- 方案 D (长期): 改为异步导出

**诊断脚本**: `references/plms-export-diagnosis.sql`

**PLMS 服务器路径 (wx-lom-app06.apac.bosch.com)**:
```
nginx:    D:\nginx-1.24.0\
配置:     D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf
Java应用: D:\lom\lom-dashboard-serve-1.0-RELEASE\
日志:     D:\lom\lom-dashboard-serve-1.0-RELEASE\logs\
```

**Pitfall**:
- 用户拒绝仅改 nginx 超时的方案，要求深入数据库层分析
- Windows cmd 中 curl 的 `%{time_total}` 解析可能异常（需用 `%%`）
- 诊断脚本应覆盖表大小、索引、执行计划、数据分布等多个维度

## 数据库代码管理（跨项目共享）

### 目录结构

数据库对象是跨项目共享资源（PLMS、I4.0 等共用同一个 Oracle 实例 LOGPOE），因此代码存放在独立的 `_database/` 目录，而非项目目录下。

```
knowledge/
├── _database/LOGPOE/                     ← 公共资源（表/视图/MV/存储过程/索引）
│   ├── _index.md                         ← 全库对象清单 + 依赖关系图 + 详情模板
│   ├── LOI_V_LTAP_EXPORT_view_definition.sql
│   ├── LTAP_LTAK_POE_table_definition.sql
│   └── ...
│
├── PLMS数据梳理/
│   ├── 02_数据库/                        ← 保留现有文档（字典/速查/详解）
│   └── 07_数据库代码/
│       └── _plms_objects.md              ← PLMS 引用清单（指向 _database/）
│
└── I4.0/
    └── 07_数据库代码/
        └── _i4_objects.md                ← I4.0 引用清单（指向 _database/）
```

### SQL 代码存储工作流

当用户提供表/视图/存储过程的 SQL 代码时，必须立即保存到 `_database/LOGPOE/`：

```
保存位置: _database/LOGPOE/
文件命名: {对象名}_view_definition.sql    (视图)
          {对象名}_table_definition.sql   (表)
          {对象名}_mv_definition.sql      (物化视图)
          {对象名}_proc_definition.sql    (存储过程)
          {对象名}_index_definition.sql   (索引)
```

**关键原则**：
- 用户提供 SQL 代码后立即保存，避免用户重复提供
- 后续需要时直接调用文件，不再要求用户重新粘贴
- 保存时添加头部注释：对象名、来源、采集时间、问题描述（如有）
- 同时更新 `_index.md` 索引文件

**示例头部注释**：
```sql
-- LOI_V_LTAP_EXPORT 视图定义
-- 来源: Oracle USER_VIEWS
-- 采集时间: 2026-06-02
-- 问题: 504超时 (2分10秒)
```

### 单对象详情模板

每个对象的详情必须包含以下信息（记录在 `_index.md` 中）：

```markdown
## {对象名}

- 类型: TABLE / VIEW / MATERIALIZED VIEW / PROCEDURE / INDEX
- 行数: (实测值，非估算)
- 分区: (是否分区表，分区键)
- 索引: (索引列表)
- 刷新频率: 实时 / 每小时 / 每天 / 每次查询 / 不刷新
- 最后刷新: (日期，标注是否过期)
- 状态: FRESH / STALE / NEEDS_COMPILE / COMPILATION_ERROR
- 依赖对象: (上游表/下游视图/MV)
- 使用项目: PLMS / I4.0 / 两者
- 备注: (问题描述、优化方案等)
```

### _index.md 核心内容

`_database/LOGPOE/_index.md` 包含：
1. **对象清单表** — 所有对象的摘要（名称/类型/行数/刷新频率/使用项目/文件路径）
2. **依赖关系图** — 表→视图→MV→存储过程的链式依赖
3. **按项目使用统计** — PLMS/I4.0 各自使用的对象数量
4. **待补充清单** — 缺少 .sql 文件的对象列表

### Pitfall

- **不要把数据库代码放在项目目录下** — 数据库对象是共享资源，放在 `_database/LOGPOE/`
- **项目目录只放引用** — `PLMS数据梳理/07_数据库代码/_plms_objects.md` 只记录 PLMS 使用了哪些对象，实际定义在 `_database/`
- **必须包含刷新频率和最后刷新时间** — 用户明确要求记录这些元数据
- **行数必须是实测值** — 不能用估算值，必须 `SELECT COUNT(*)` 确认

## Export 504 视图定义分析 (2026-06-02)

### LOI_V_LTAP_EXPORT 视图结构

```sql
WITH TEMP_LTAP_LTAK_POE_DATA AS(
  SELECT ... FROM LTAP_LTAK_POE
  WHERE BDATU >= '20230101'  -- 1713万行
)
-- 13个 UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GR304
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GR305B
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GR308
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- RP304
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GI304
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GI308
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GI305B
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GI310
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GR310
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- DE304
MINUS
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- DE304排除条件
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- DE308
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- GRWX03
UNION ALL
SELECT ... FROM TEMP_LTAP_LTAK_POE_DATA T WHERE ...  -- DEWX03
```

### 问题点分析

| 问题 | 影响 | 说明 |
|------|------|------|
| CTE 物化无索引 | 全表扫描 | Oracle 将 CTE 转为临时表，丢失原表索引 |
| 13次 UNION ALL | 重复扫描 | 每个都扫描同一个 CTE 临时表 (1713万行) |
| MINUS 排序 | 2.19亿行预估 | DE304 的 MINUS 操作需要排序去重 |
| 无分区裁剪 | 扫描全部分区 | `BDATU >= '20230101'` 无上限，扫描70+分区 |

### 根因总结

```
CTE 物化为无索引临时表
    ↓
13次 UNION ALL 重复扫描 (每次1713万行)
    ↓
MINUS 排序去重 (2.19亿行预估)
    ↓
无分区裁剪 (扫描所有70+分区)
    ↓
实测 2分10秒 (130秒)
```

### 验证方法

```sql
-- 1. 直接查基表 (有索引，1秒)
SELECT COUNT(*) FROM LTAP_LTAK_POE WHERE BDATU >= '20230101';

-- 2. 通过视图查 (CTE无索引，130秒)
SELECT COUNT(*) FROM LOI_V_LTAP_EXPORT;

-- 3. 检查执行计划
EXPLAIN PLAN FOR SELECT * FROM LOI_V_LTAP_EXPORT;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
-- 期望看到: TEMP TABLE TRANSFORMATION (CTE物化)
```

## 排错案例库

### 案例: Productivity 页面 Export TO / Export Document 504 超时 (2026-05-29)

**症状**: Productivity > Daily Workload & Workhour Overview 页面，点击下载按钮（export TO / export document）后 504 Gateway Timeout

**API 端点**:
- `/api/excel-new-product-lv1-to?creationDate=YYYYMM`
- `/api/excel-new-product-lv1-document?creationDate=YYYYMM`

**数据链路**:
```
前端 Vue2 按钮 → URL 跳转 → nginx(9080) → Java SpringBoot → Oracle 查询 → 生成 Excel
                           ↑
                       504 超时
```

**涉及视图**:
- export TO → `LOI_V_LTAP_EXPORT` (源表: LTAP_LTAK_POE, 885万行)
- export document → `LOI_V_MSEG_EXPORT` (源表: MSEG_POE)

**排查步骤**:
1. 直连 localhost 测试: `curl -k https://127.0.0.1:9080/api/excel-new-product-lv1-to?creationDate=202605`
2. 如果直连也 504 → nginx → Java 之间超时（不是外部网关问题）
3. 检查 nginx 配置: `proxy_read_timeout` 值
4. 检查 Java 应用日志
5. 确认后端 CPU（请求是否到达 Java）

**根因**: CTE扫描1713万行+20个UNION ALL+MINUS排序2.19亿行+没有分区裁剪
  - LTAP_LTAK_POE 实际 38,325,890 行 (3830万，之前估计 181 万，误差 21 倍)
  - MSEG_POE 实际 29,998,205 行 (3000万)
  - 执行计划: PARTITION RANGE ALL → 扫描所有 70+ 个分区
  - **预估 47 秒，实际 2 分 10 秒 (130 秒)**
    - LOI_V_LTAP_EXPORT 实测行数: 8,875,935 (887.6万)
    - LOI_V_LTAP_EXPORT 是普通视图 (非物化视图)
  - EXPORT_LTAP 物化视图存在但已过期 3 年 (最后刷新 2022-12-20)
  - CB$CUBE_LTAP_LTAK_POE 是汇总 Cube，不能用于导出明细

**物化视图方案评估**:
  - EXPORT_LTAP 可替代 LOI_V_LTAP_EXPORT (明细表，列一致)
  - 但 Java 代码使用 LOI_V_LTAP_EXPORT，刷新 EXPORT_LTAP 不会自动修复 504
  - 需要同时: ①刷新 EXPORT_LTAP ②修改 Java 代码使用 EXPORT_LTAP
  - CB$CUBE 刷新耗时 58.63 分钟，每小时 COMPLETE 刷新需评估可行性
  - 用户明确表示不想修改数据库代码

**解决方案**:
- 方案 A: 刷新 EXPORT_LTAP + 修改 Java 代码 → 查询 1 秒 (需要改代码，用户无法改)
- 方案 B: 修改 nginx proxy_read_timeout 300s (临时方案，不改代码)
- 方案 C: 重命名 LOI_V_LTAP_EXPORT → 创建同名表 + 索引 + 存储过程定时刷新 (不需要改代码，但 LOI_V_LOM_PICK_TO MV 有依赖需要处理)
- 方案 D: 分区裁剪 (需要修改视图定义，用户拒绝)
- 方案 E: 异步导出 (长期方案，需要较大开发量)

**完整诊断**: 见 `references/oracle-export-504-diagnosis.md`

**Pitfall**
```
nginx:    D:\nginx-1.24.0\
配置:     D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf
Java应用: D:\lom\lom-dashboard-serve-1.0-RELEASE\
日志:     D:\lom\lom-dashboard-serve-1.0-RELEASE\logs\
SSL证书:  D:\nginx-1.24.0\ssl\wx-lom-app06.apac.bosch.com.crt
```

**排查命令**:
```
# 查 nginx 超时配置
type D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf | findstr /i "timeout"

# 查 Java 日志中的 export 错误
findstr /i "excel-new-product" D:\lom\lom-dashboard-serve-1.0-RELEASE\logs\lom-dashboard-serve-1.0-RELEASE.out.log

# 直连测试（绕过外部网关）
curl -k https://127.0.0.1:9080/api/excel-new-product-lv1-to?creationDate=202605
```

**Pitfall**:
- 表行数不能跨表推断: LTAP_LTAK_POE (3830万) ≠ LTAP_LTAK_POE_GI_TO (181万)
- 分区表必须检查分区裁剪: PARTITION RANGE ALL = 扫描所有分区 = 慢
- 执行计划预估行数可能偏差 25 倍: 219M 预估 vs 886万 实际
- 物化视图过期 3 年仍为 NEEDS_COMPILE 状态，需要手动刷新

**PLMS 服务器路径 (wx-lom-app06.apac.bosch.com)**

当排错知识库有更新时，同步到 LLM-Wiki 需要区分两种场景：

### 覆盖策略（已有文件更新）

适用场景：更新已有的功能域文件（如 10_TO_收发货.md 新增 export 视图定义）

```bash
# 1. 更新 PLMS-LLM-WIKI/ 下的文件
# 2. 复制到 raw/ 目录（覆盖旧文件）
cp PLMS-LLM-WIKI/10_TO_收发货.md /home/ethan/llm-wiki/raw/docs/
# 3. ingest（会覆盖旧的 wiki 页面）
ingest_file("docs/10_TO_收发货.md")
```

### 添加策略（新增文件）

适用场景：新增诊断报告、新排错记录等独立内容

```bash
# 1. 创建新文件到 PLMS-LLM-WIKI/
# 2. 复制到 raw/ 目录
cp PLMS-LLM-WIKI/34_export_504_diagnosis.md /home/ethan/llm-wiki/raw/docs/
# 3. ingest（新增 wiki 页面）
ingest_file("docs/34_export_504_diagnosis.md")
```

### 完整同步流程

```
ingest 完成后:
  review_diffs() → approve_all_diffs(dry_run=False) → build_index()
```

**Pitfall**：
- 不要混用覆盖和添加，避免数据滞后和杂糅
- 覆盖时确认文件路径完全匹配（包括大小写）
- 新增文件命名遵循已有编号规则（如 34_xxx.md）

### 已完成的排查

```
[✓] 症状确认: Productivity > Daily Workload & Workhour Overview → 504
[✓] API 端点: /api/excel-new-product-lv1-to, /api/excel-new-product-lv1-document
[✓] 直连测试: curl -k https://127.0.0.1:9080/... → 也 504
[✓] nginx 配置: 没有 proxy_read_timeout → 默认 60 秒
- **表行数**: LTAP_LTAK_POE 3830万, MSEG_POE 3000万
- **分区信息**: LTAP_LTAK_POE 按月分区 70+ 个
- **执行计划**: 47秒→2分10秒(实际), PARTITION RANGE ALL (无分区裁剪)
- **LOI_V_LTAP_EXPORT 行数**: 8,875,935 (887.6万, 2026-06-01 实测)
[✓] 数据分布: 工作日约2万行/天, 实时写入
[✓] 物化视图状态: EXPORT_LTAP 过期3年, CB$CUBE 是汇总表
[✓] 物化视图刷新耗时: CB$CUBE_LTAP_LTAK_POE 58.63分钟
[✓] 物化视图日志: FACT表支持增量刷新
[✓] 增量刷新检查: LOI_V_LTAP_EXPORT 不支持 FAST (UNION ALL + MINUS)
[✓] 三人讨论: 数据库(视图设计) vs nginx(超时配置) vs 架构(同步导出)
[✓] 知识库更新: PLMS数据库字典/视图逻辑速查/物化视图详解/LLM-Wiki
```

### 待完成

```
[ ] 用户确认方案: 刷新EXPORT_LTAP+改Java代码 vs 改nginx超时
[ ] 如选方案A: 执行 EXPORT_LTAP 刷新 + 修改 Java 代码
[ ] 如选方案B: 修改 nginx 配置
```

## 物化视图刷新策略选择指南 (2026-05-29 新增)

### COMPLETE vs FAST 刷新

```
                    COMPLETE 刷新          FAST 刷新 (增量)
─────────────────────────────────────────────────────────────
刷新时间            长 (扫描全表)          短 (只处理变化)
数据延迟            取决于刷新频率          可以更频繁刷新
数据库负载          高                     低
配置复杂度          低                     高 (需要物化视图日志)
适用场景            数据延迟可接受          数据延迟要求高
─────────────────────────────────────────────────────────────
```

### FAST 刷新限制条件

视图不能包含以下操作（会导致 FAST 刷新失败）：

```
1. DISTINCT
2. GROUP BY
3. 集合操作: UNION ALL, MINUS, INTERSECT (部分情况支持)
4. 子查询 (部分情况支持)
5. 分析函数: OVER, ROW_NUMBER, RANK 等
6. CONNECT BY
7. 外连接 (部分情况支持)
```

**检查方法**:
```sql
-- 使用 EXPLAIN_MVIEW 分析
BEGIN
  DBMS_MVIEW.EXPLAIN_MVIEW('视图名');
END;
/

-- 查询结果
SELECT capability_name, possible, msg
FROM MV_CAPABILITIES_TABLE
WHERE MVNAME = '视图名';
```

### LOI_V_LTAP_EXPORT 刷新策略分析

```
视图特性:
  - 20+ 个 UNION ALL → 不支持 FAST 刷新
  - MINUS 操作 → 不支持 FAST 刷新
  - CTE (WITH 子句) → 可能不支持

结论: 只能使用 COMPLETE 刷新
```

### 数据更新频率检查

```sql
-- 检查表的数据更新频率 (最近 7 天)
SELECT SUBSTR(BDATU, 1, 8) AS DAY,
       COUNT(*) AS ROW_COUNT
FROM LTAP_LTAK_POE
WHERE BDATU >= TO_CHAR(SYSDATE - 7, 'YYYYMMDD')
GROUP BY SUBSTR(BDATU, 1, 8)
ORDER BY DAY DESC;

-- 检查今天按小时分布
SELECT SUBSTR(BDATU, 1, 8) AS DAY,
       SUBSTR(BZEIT, 1, 2) AS HOUR,
       COUNT(*) AS ROW_COUNT
FROM LTAP_LTAK_POE
WHERE BDATU >= TO_CHAR(SYSDATE, 'YYYYMMDD')
GROUP BY SUBSTR(BDATU, 1, 8), SUBSTR(BZEIT, 1, 2)
ORDER BY DAY DESC, HOUR DESC;
```

### 刷新频率选择

```
数据更新频率        建议刷新频率        数据延迟
─────────────────────────────────────────────────
实时 (每小时)       每小时 COMPLETE     最多 1 小时
每天批量           每天凌晨 COMPLETE   最多 24 小时
每周批量           每周日凌晨 COMPLETE 最多 7 天
─────────────────────────────────────────────────
```

**LTAP_LTAK_POE 实际数据**:
- 工作日约 20,000 行/天
- 周末约 5,000 行/天
- 每小时约 550-670 行
- 数据是实时写入的

**建议**: 每小时 COMPLETE 刷新

### 创建定时刷新任务

```sql
BEGIN
  DBMS_SCHEDULER.CREATE_JOB (
    job_name        => 'REFRESH_EXPORT_MV',
    job_type        => 'PLSQL_BLOCK',
    job_action      => 'BEGIN DBMS_MVIEW.REFRESH(''LOI_MV_LTAP_EXPORT'', ''C''); END;',
    start_date      => SYSTIMESTAMP,
    repeat_interval => 'FREQ=HOURLY;MINUTE=5',  -- 每小时的第 5 分钟刷新
    enabled         => TRUE
  );
END;
/
```

## 分区表性能优化 (2026-05-29 新增)

### 分区裁剪

当查询条件匹配分区键时，Oracle 只扫描相关分区（分区裁剪），大幅减少 IO。

**问题**: PARTITION RANGE ALL = 扫描所有分区 = 慢

**优化**: 让 WHERE 条件匹配分区键

```sql
-- 当前 (扫描所有 70+ 分区)
FROM LTAP_LTAK_POE
WHERE BDATU >= '20230101'

-- 优化后 (只扫描当月分区)
FROM LTAP_LTAK_POE
WHERE BDATU >= '20230101'
  AND BDATU >= TRUNC(SYSDATE, 'MM')  -- 分区裁剪
```

**效果**: 查询时间从 47 秒 → 5 秒

### 检查分区信息

```sql
-- 检查表是否是分区表
SELECT partition_name, high_value, num_rows, last_analyzed
FROM user_tab_partitions
WHERE table_name = 'LTAP_LTAK_POE'
ORDER BY partition_position;

-- 检查执行计划是否使用分区裁剪
EXPLAIN PLAN FOR
SELECT * FROM LTAP_LTAK_POE
WHERE BDATU >= TRUNC(SYSDATE, 'MM');

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
-- 期望看到: PARTITION RANGE SINGLE 或 PARTITION RANGE ITERATOR
-- 避免: PARTITION RANGE ALL
```

## 参考文件

- `references/oracle-retrieval-queries.sql` — Oracle 检索脚本（物化视图状态、定义、存储过程）
- `references/oracle-export-504-diagnosis.md` — Export 504 超时诊断案例 (表行数修正、分区表、执行计划分析)
- `references/mv-status-analysis-20260527.md` — 物化视图状态分析报告（86个视图）
- `references/loi-v-wh-inventory-all-fcst-definition.sql` — LOI_V_WH_INVENTORY_ALL_FCST 完整定义（仓库库存预测核心视图）
- `references/loi-v-wh-overview-definition.md` — LOI_V_WH_OVERVIEW 定义（仓库概览，含库位计数规则详解）
- `references/plms-view-categorization-rules.md` — PLMS 视图功能分类规则（31个功能域，用于批量导入知识库时自动分类）
- `references/i40-confluence-space.md` — I4.0 Confluence 空间分析（PLMS/LOM Dashboard 页面索引、排错记录、LOI 视图参考）
- `references/i40-plms-cross-reference-20260528.md` — I4.0 ↔ PLMS 交叉分析结果（62个缺失对象、排错记录映射、L2/L3钻取映射）
- `references/llm-wiki-integration.md` — LLM-Wiki 联动详细配置（Docker、providers.py、env、ingest 工作流）

## 使用方式

新会话中说"继续 PLMS 排错知识库"并提供 SQL 执行结果即可。

### 宽泛查询处理（"PLMS排错问题"无具体症状时）

当用户只说"PLMS排错问题"但未提供具体症状时：
1. **不要重新读取知识库源文件** — SKILL.md 已包含完整摘要，直接基于 SKILL.md 回复
2. 提供物化视图健康快照 + 已有排错案例列表
3. 询问用户具体症状（哪个页面、什么数据异常）
4. 用户提供症状后，用 `search_wiki` → `read_wiki_page` → `ask_wiki` 检索相关排错记录

**反模式**: 逐个 read_file 知识库下的 01_概述/02_数据库/03_数据映射/... 等目录文件 — SKILL.md 已整合了这些信息，重复读取是浪费轮次。

### 当前进度

```
已完成:
  [✓] 视图/物化视图 SQL 定义     489 个
  [✓] 存储过程源码                26 个
  [✓] 表结构 + 行数              20 张
  [✓] 补充视图定义                 3 个
  [✓] I4.0 交叉关联              519 页分析 + 排错记录/L2/L3 映射
  [✓] LLM-Wiki 联动              86 wiki 页面 + 509 向量块
  [✓] 排错记录正文提取            33 个 HTML → md → 独立 wiki 页面
  [✓] 排错记录 frontmatter        31 个页面添加结构化元数据
  [✓] Common-Table_View 提取      22KB 完整表/视图清单
  [✓] Redundant-DB-Items 提取     8KB 冗余对象清单
  [✓] 自动化更新脚本              update_plms_kb.py
  [✓] 物化视图详情文档            CB$CUBE + EXPORT 定义/刷新耗时/日志
  [✓] 数据库深度诊断              表行数修正、分区、执行计划、数据分布
  [✓] Export 504 诊断报告         plms_export_504_diagnosis.md

待做:
  [ ] 分析 COMPILATION_ERROR 根因 → 修复建议
  [ ] 建立数据质量基线（正常值范围）
  [ ] 积累更多排错案例（症状→原因→修复）
```
