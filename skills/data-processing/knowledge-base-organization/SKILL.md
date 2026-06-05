---
name: knowledge-base-organization
description: "将分散的文档整理到知识库的结构化目录中，采用渐进式目录结构（概述→详细），自动扫描、分类、移动并生成 README。"
tags: [file-organization, knowledge-base, documentation, directory-structure]
triggers:
  - "整理/归档/组织 知识库/文档/文件"
  - "建立XX文件夹并整理相关文件"
  - "项目目录结构采用渐进式"
  - "为什么多出来很多XX文件"
---

# Knowledge Base Organization

将分散在桌面、work 目录等位置的文档整理到知识库的结构化目录中。

## 渐进式目录结构设计原则

> 详细配置和 ingest 流程参见 `references/llm-wiki-ingest-workflow.md`
> Oracle SQL Developer 导出解析参见 `references/oracle-sql-export-parsing.md`

渐进式 = 从概述到详细，从基础到高级。用户阅读时按顺序即可逐步深入。

命名规范：
```
NN_中文名称/
```
- 使用数字前缀 `01_` `02_` ... 控制逻辑顺序
- 中文名称简洁明了，表达该层的内容定位
- 每层文件数量建议 2-6 个，过多说明需要拆分层级

典型层级模板（按需裁剪）：
```
项目名/
├── README.md              # 目录说明 + 使用建议 + 文件清单
├── 01_概述/               # 系统架构、总览、入门
├── 02_数据结构/           # 数据库字典、表结构、字段说明
├── 03_数据映射/           # 数据来源、映射关系、查找表
├── 04_调用链/             # API 链路、前后端映射、依赖关系
└── 05_操作手册/           # 用户操作指南、FAQ
```

## 工作流程

### Step 1: 扫描相关文件

用 `search_files` 在可能的位置搜索关键词文件：
- 知识库根目录（常有散落的项目文档）
- `work/项目名/` 目录（工作区产生的分析文件）
- 桌面（临时产物）

```bash
# 1. 根目录散落文件
find knowledge_root -maxdepth 1 -type f
# 2. 已有项目子目录的根层级（可能有遗漏文件）
find knowledge_root -mindepth 2 -maxdepth 2 -type f ! -name README.md
# 3. 按文件名关键词搜索
```

用 `execute_code` 批量读取文件头部，判断内容类型和归属。

### Step 2: 分类策略

按内容语义分类，不是按文件类型：
- 概述类：标题含"映射"、"总览"、"架构"、"overview"
- 数据类：标题含"数据库"、"字典"、"表结构"、"SQL"
- 映射类：标题含"来源"、"映射"、"查找"、"对应"
- 链路类：标题含"调用链"、"依赖"、"路由"、"API"
- 手册类：标题含"操作"、"手册"、"指南"、"教程"

### Step 3: 创建目录并移动文件

```python
# execute_code 批量操作，不要逐个 terminal 命令
import shutil, os

# 先建所有目录
for subdir in subdirs:
    os.makedirs(os.path.join(base_dir, subdir), exist_ok=True)

# 再批量移动
for filename, subdir in mapping.items():
    shutil.move(src, dst)
```

**关键**：用 `execute_code` + `shutil.move` 批量移动，不要用逐个 `terminal` 命令。

### Step 4: 生成 README.md

README 必须包含：
1. 一句话说明本目录是什么
2. 目录结构树（带中文注释）
3. 每个子目录的用途说明
4. 使用建议（按渐进顺序）
5. 维护说明

### Step 5: 验证（含二次扫描）

移动完成后必须做二次扫描，确保无遗漏：
```bash
# 检查项目目录根层级是否有散落文件
find knowledge_root/项目名 -mindepth 2 -maxdepth 2 -type f ! -name README.md
```
本次实测中首次扫描遗漏了 `plms_query2.sql`，二次扫描才发现。

### Step 6: 第二阶段 — 清理建议

整理完成后，单独列出清理建议（不自动执行）：
- 临时文件（如 Word 锁文件 `~$*.docx`）
- 内容重复的文件（如原始导出 vs 整理后的汇总版）
- 已过时的配置文档
- 无扩展名文件（建议加 `.md`）

**用户偏好**：先完成所有文件归位，再列出清理建议。用户确认后才执行删除/重命名。
执行清理后，必须同步更新受影响的 README.md。

## Confluence HTML 导出分析工作流

当用户给出一个 Confluence 导出目录（包含大量 HTML 文件）要求归档到知识库时：

### 识别方法
Confluence 导出的特征文件：
- `index.html` — 重定向到根页面
- `toc.html` — 完整页面树（10K+ 行，含所有 `<a href="xxx.html">` 链接）
- 每个 HTML 文件名格式: `页面标题.数字ID.html`
- 目录下有 `_scroll_external/`, `css/`, `js/`, `images/` 等资源子目录
- HTML 文件内 `<meta name="exp-space-key" content="XXX">` 标识 Confluence 空间

### 分类技术：面包屑引用法

**核心思路**：通过搜索所有 HTML 文件中是否包含某个父页面的链接来判断其归属。

```python
# 用 search_files 搜索特定父页面的面包屑引用
# 比如判断哪些页面在 "LOM Dashboard" 子树下：
search_files(
    pattern="Physical-Logistics-Management-System-_-LOM-Dashboard.2742792006.html",
    file_glob="*.html",
    output_mode="files_only"
)
# 返回的文件 = 属于该父页面的子页面（面包屑中有引用）
# 不在结果中的 = 不属于该子树
```

分类步骤：
1. 读取根页面（`index.html` 指向的那个），确定空间名称和主题
2. 读取 `toc.html` 前 100 行，理解页面层级结构
3. 确定关键父页面的文件名（如 `LOM-Dashboard.xxx.html`）
4. 用 `search_files` 搜索该文件名在面包屑中的引用 → 分出相关/不相关两大类
5. 对不相关类再用其他关键词细分（如 AGV、IES、RFID 等独立子项目）

### 页面内容提取

HTML 文件内容在 `<div id="main-content" class="wiki-content">` 内。
搜索内容时直接用 `search_files` 搜索整个 HTML 文件（含标签），
用 `read_file` + offset/limit 读取特定区域。

**注意**：不要尝试用 terminal + python 解析 HTML — 用户可能拒绝 terminal 命令。
改用 `search_files`（内容搜索）和 `read_file`（精确读取）即可完成大部分分析。

### 目录结构模板

```
项目名/
├── README.md              ← 主分类分析（A 相关/B 间接/C 不相关）
├── 01_概述/               ← 项目总览、与已有知识库的关系
├── 02_[核心主题]相关/     ← 直接相关的页面索引
├── 03_非[核心主题]项目/   ← 不相关的独立子项目索引
├── 04_排错记录/           ← Bug/Issue 页面索引
├── 05_系统架构/           ← 整体架构文档
├── 06_SQL视图参考/        ← 数据库/SQL 相关页面索引
└── 99_原始导出/           ← 原始 HTML 文件（cp -r，不修改）
```

每个子目录下创建 `索引.md`，列出文件名 + 页面标题 + 简要说明。

## 大型 Schema Dump → Wiki Pipeline

当用户给出一个大型数据库 schema 导出文件（SQL DDL、物化视图定义、视图定义等）要求整理到知识库并接入 LLM-Wiki 时：

### Phase 1: 解析与分类

1. 用 `execute_code` 解析文件，提取每个对象的名称和 SQL 定义
2. 按功能域分类（库存/OTD/成本/仓库等），命名规则 `NN_功能域.md`
3. 提取元数据：源表列表、刷新策略（MV）、调度周期、UNION ALL 数量

### Phase 2: 精简生成

1. **去除 DDL 噪声** — 删除 STORAGE/PCTFREE/TABLESPACE/BUFFER_POOL 等物理存储参数，只保留业务逻辑（SELECT/WHERE/JOIN）
2. 每个功能域生成一个 .md 文件，包含：
   - 视图列表汇总表（名称、类型、源表、刷新策略）
   - 每个视图的详细定义（元数据 + 精简 SQL）
3. 输出到专用子目录 `项目-LLM-WIKI/` 作为数据溯源源

### Phase 3: LLM-Wiki Ingest

1. 将精简文件复制到 llm-wiki 的 `raw/docs/` 目录
2. 用 `mcp_LLM_WIKI_ingest_file` 逐个 ingest（避免 `ingest_all` 超时）
3. 用 `mcp_LLM_WIKI_approve_all_diffs` 批量审核
4. 用 `mcp_LLM_WIKI_build_index` 重建向量索引

**关键**: 大文件 ingest 会超时，必须逐个处理。先处理小文件（<30KB），再处理大文件。

**关键 Pitfall — MCP ingest 超时与容器环境变量**:

1. `ingest_all` 对 30+ 文件必定超时（180s MCP 限制），必须用 `ingest_file` 逐个处理
2. `ingest_file` 单文件也可能超时（180s），文件需控制在 50KB 以内
3. **容器 .env 变更必须 recreate**: `docker stop/rm` + `docker run --env-file` 才能生效，`docker-compose up -d` 在 v1 版本可能因 `ContainerConfig` KeyError 失败
4. **mimo-embedding 不可靠**（返回 502 Bad Gateway），切换到 DashScope `text-embedding-v3`：
   - 需要在 providers.py 中添加 `DashScopeProvider` 类（使用 OpenAI 兼容端点 `dashscope.aliyuncs.com/compatible-mode/v1`）
   - .env 设置 `EMBED_PROVIDER=dashscope`, `EMBED_MODEL=text-embedding-v3`, `DASHSCOPE_API_KEY=***`
   - 用 `docker cp` 将更新后的 providers.py 覆盖容器内文件，然后 recreate

### 数据溯源架构

```
原始导出 → 项目-LLM-WIKI/*.md (精简版, 数据溯源源)
  → llm-wiki/raw/docs/ (Docker 挂载)
    → wiki/concepts/*.md (LLM 生成的 wiki 页面)
      → 向量索引 (语义检索)
```

更新时只需修改 `项目-LLM-WIKI/` 下的文件，复制到 raw 目录后重新 ingest。

## 跨项目交叉引用（Confluence 导出 ↔ 已有知识库）

当 Confluence 导出的内容与知识库中已有项目高度相关时（如 I4.0 空间包含 PLMS 系统文档），
需要建立三方映射文档，将数据库对象、UI 页面、前端路由关联起来。

### 三方映射文档结构

```markdown
## 一、数据库对象 → Confluence 页面 → PLMS 前端路由

| Oracle 对象 | Confluence 页面 | PLMS 前端路由 | Controller | 说明 |
|------------|----------------|--------------|------------|------|

## 二、排错记录 → 数据库对象关联

| 排错页面 | 故障对象 | 根因 | 修复方式 |
|----------|---------|------|---------|

## 三、排错指南
- 快速定位路径（5步法）
- 常用诊断 SQL（可直接执行）
- 数据刷新链路图

## 四、互补关系
| 已有知识库 | 新项目可补充 |
```

### 数据来源

- **已有知识库侧**：读取 `01_概述/数据来源映射`、`02_数据库/视图定义`、`04_调用链/逐页面映射`
- **Confluence 侧**：用 `search_files` 搜索 HTML 中的 SQL 语句、视图名称、Controller 名
- **交叉**：以 Oracle 对象名（如 `LOI_V_WH_OVERVIEW`）为 key，两边匹配

### 输出位置

交叉引用文档放在新项目的 `02_[核心主题]相关/` 目录下，
文件名格式：`[新项目]与[已有项目]数据关联.md`

**关键原则**：不动原数据，所有产出另存到新项目目录。

## 向量检索质量优化

当 ask_wiki 的回答不够精确时（找到正确页面但 LLM 合成答案太泛），根本原因通常是：
1. wiki 页面内容是散文式摘要，缺少结构化字段
2. 向量检索命中了相关页面，但 LLM 无法从非结构化文本中提取具体事实

### 混合索引架构（推荐）

不改 wiki 页面正文（保留自然语言的语义丰富度），只给页面添加 frontmatter 元数据：

```yaml
---
views: [LOI_V_OUTPUT_FULL, LOI_V_OUTPUT_DAILY]
root_cause: "to_char 占位符不足导致版本号乱码"
affected_tables: [INVENTORY_ALL]
tags: [output, to_char, oracle, 月度报表]
---
```

效果：
- 正文保留口语化描述（"左下角 future coverage 没数据"）→ 自然语言查询能命中
- frontmatter 提供结构化字段（视图名/根因/标签）→ 精确匹配能命中
- ask_wiki 合成时 LLM 能从 frontmatter 直接提取答案，减少幻觉

### 排错记录结构化模板

```markdown
---
views: [LOI_V_xxx]
root_cause: "一句话根因"
affected_tables: [TABLE1, TABLE2]
tags: [keyword1, keyword2]
---

# 问题标题

## 症状
用户可见的异常表现

## 根因
技术层面的原因分析

## 解决方案
具体修复步骤

## 验证
修复后的验证方法
```

## 记忆迁移至 Mem0 模式

当用户要求整理 memory 并迁移到 Mem0 时：

1. 用 Mem0 API（非 CLI，`hermes mem0` 子命令不存在）
2. API 端点：`http://localhost:59110/memories`
3. 认证头：`x-api-key: {ADMIN_API_KEY}`（从 `/mnt/c/wsl/mem0/server/.env` 读取）
4. 长内容会写入失败 → 缩短到 200 字以内
5. 写入方式：`execute_code` + `write_file` 写临时 JSON + `terminal curl` 调 API
6. 项目归类路径：`/环境/`、`/项目/PLMS/`、`/项目/I4.0/` 等

## 跨项目数据库对象管理

当多个项目（PLMS、I4.0等）共享同一个数据库实例时，数据库对象（表/视图/MV/存储过程）是公共资源，不应归属于单个项目目录。

### 目录结构

```
knowledge/
├── _database/                        ← 数据库公共资源（跨项目）
│   └── {DB实例名}/                   ← 如 LOGPOE
│       ├── _index.md                 ← 全库对象清单 + 依赖关系图 + 详情模板
│       ├── {对象名}_view_definition.sql
│       ├── {对象名}_table_definition.sql
│       ├── {对象名}_mv_definition.sql
│       └── {对象名}_proc_definition.sql
│
├── PLMS数据梳理/
│   └── 07_数据库代码/
│       └── _plms_objects.md          ← PLMS 使用的对象引用清单
│
└── I4.0/
    └── 07_数据库代码/
        └── _i4_objects.md            ← I4.0 使用的对象引用清单
```

### 单对象详情模板（记录在 `_index.md`）

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

### SQL 代码存储工作流

当用户提供表/视图/存储过程的 SQL 代码时：
1. 立即保存到 `_database/{实例名}/` 目录
2. 文件名: `{对象名}_view_definition.sql` / `_table_definition.sql` / `_mv_definition.sql` / `_proc_definition.sql`
3. 文件头部添加注释：对象名、来源、采集时间、问题描述（如有）
4. 同步更新 `_index.md` 索引文件
5. 后续需要时直接调用文件，避免用户重复提供

**关键原则**：
- 数据库对象是共享资源，放在 `_database/`
- 项目目录只放引用（指向 `_database/` 的清单文件）
- 必须包含刷新频率和最后刷新时间（用户明确要求）
- 行数必须是实测值，不能用估算值

## 排错记录处理模式

排错记录（Bug/Issue 页面）必须逐条独立 ingest，不能合并为一个大文件。

原因：LLM ingest 将整个文件生成一个 wiki 页面，合并文件会导致 LLM 只提取摘要而丢失具体根因。

正确流程：
1. 每个排错记录 → 独立 .md 文件（文件名含日期编号如 `220307_xxx.md`）
2. 放入 `raw/docs/trouble/` 子目录
3. 逐个 `ingest_file`（文件通常 <5KB，不会超时）
4. 每个生成独立 wiki 页面，向量索引可精确定位

自动化脚本参考：`scripts/update_plms_kb.py` — 自动检测导出格式、解析、更新知识库、可选同步到 LLM-Wiki。

## 编辑已有 Raw 文件的完整工作流

> 具体示例参见 `references/lis-inventory-logic-update-example.md`

当需要修改 LLM-Wiki 中已有内容时（不是新增文件），必须完成完整闭环：

1. **备份原文件**: `cp file file.bak`
2. **修改 raw 文件**: 用 `patch` 工具精确修改（如 SQL 条件逻辑、WHEN-THEN 规则）
3. **重新 ingest**: `mcp_LLM_WIKI_ingest_file(file_path)` 生成 diff
4. **审核 diff**: `review_diffs` → `read_diff` 确认内容 → `approve_diff`
5. **手动更新 wiki 页面**: ingested 生成的是**新** wiki 页面（concepts/ 下），但**原有的 wiki 页面**（如 i4-platform/ 下）不会自动更新，必须手动用 `patch` 同步修改
6. **记录修改到 Mem0**: 用 `mem0_add` 存储修改摘要（时间、内容、影响范围、备份位置），方便用户回溯

**关键 Pitfall**: ingest 只创建新页面，不更新旧页面。如果原始素材被多个 wiki 页面引用，所有引用页面都需要手动同步。

**关键 Pitfall — 文档层 vs 系统层**: 修改知识库文档时，必须向用户明确区分两个层面：
1. **文档层**（agent 处理）：raw 文件、LLM-Wiki、wiki 页面 — 仅记录逻辑描述
2. **系统层**（用户处理）：数据库表（如 `DIM_ACTUAL_STOCK_RULE`）、存储过程、视图定义 — 实际运行的逻辑

完成文档层修改后，必须告知用户："文档已更新，但实际系统中的 [具体表/存储过程] 也需要同步修改，是否需要我帮您检查？" 避免用户误以为文档修改等于系统生效。

## 修改记录管理

当修改知识库中的文档时，需要在文档中添加修改记录，方便用户回溯。

### 修改记录格式

在文档的"待补充"章节前添加"修改记录"章节：

```markdown
## 修改记录

### YYYY-MM-DD
**变更内容**：简要描述修改内容
**影响范围**：
- 列出受影响的对象/规则/配置
**修改详情**：
- 具体修改点1
- 具体修改点2
**同步状态**：
- ✅ 原始文件已更新
- ✅ LLM-Wiki 已同步
- ✅ 相关页面已更新
**备份位置**：`/path/to/backup.bak`
```

### 记录到 Mem0

修改完成后，用 `mem0_add` 存储修改摘要，格式：
```
YYYY-MM-DD [系统名]修改：[简要内容]，影响[范围]。原始文件[路径]已更新，LLM-Wiki已同步，备份位置[路径]。详细记录见[文档路径]修改记录章节。
```

**关键原则**：
1. 修改记录必须包含时间、内容、影响范围、同步状态
2. 备份位置必须明确，方便回滚
3. Mem0 记录用于快速检索，详细信息仍以文档为准

## Pitfalls

1. **不要遗漏源文件**：搜索时用多个关键词，检查 `work/` 和知识库根目录两个位置
2. **不要删除源文件夹**：只移动文件，保留原目录结构（可能还有其他非数据梳理文件）
3. **临时文件处理**：不要在整理过程中提出删除建议——先完成所有文件归位，整理结束后再单独列出清理建议供用户决定。用户偏好"只整理不删除，完成后告诉我建议"的工作流
4. **备份**：整理前不需要备份（是移动不是修改），但如果是修改文件内容则必须备份
5. **用户说"重试"时的响应策略**：用户说"重试"表示对进度不满，要求加快节奏减少分析直接执行。此时应跳过详细分析，直接执行修改操作，减少中间解释步骤。
6. **文件冲突**：如果目标目录已有同名文件，询问用户是覆盖、重命名还是跳过
7. **已有目录也需检查**：已有渐进式结构的项目目录根层级可能有散落文件（如 .sql、.txt），扫描时用 `find -mindepth 2 -maxdepth 2` 检查，一并归入正确子目录
- **二次扫描防遗漏**：`search_files` 可能遗漏根目录下非典型扩展名的文件（如无扩展名文件），移动后用 `find -maxdepth 1` 再扫一次根目录
- **README 同步更新**：执行删除或重命名操作后，必须更新对应项目目录的 README.md 中的文件清单和目录树。根 README.md 也需检查是否受影响
- **LLM 生成重复 frontmatter key 导致 Quartz 崩溃**：ingest 生成的 wiki 页面中 YAML frontmatter 可能有重复 key（如 `tags:` 出现两次），YAML 解析失败 → Quartz 构建退出。已在 `mcp_server.py` 添加 `_sanitize_frontmatter()` 函数，在 `approve_diff` / `approve_all_diffs` 写入前自动去重（保留第一个，删除后续重复）。实际案例：30 个 wiki 页面受影响。实现细节见 `references/llm-wiki-ingest-workflow.md`
- **Quartz 目录重组后构建失败**：删除或重命名 wiki 子目录（如 decisions/entities）后，Quartz 的 `public/` 缓存有残留文件（如 `.gitkeep`），检测到变化时 `unlink` 报 `ENOENT`。解决：`docker exec quartz-wiki rm -rf /usr/src/app/public/*` 清空缓存后重启容器

## 用户偏好

- 目录结构采用渐进式（从概述到详细）
- 中文命名
- 每个层级有明确的语义定位
- README.md 必须有，作为导航入口
- 敏感信息（Token、API Key）整理时注意：不删除，但可补全上下文信息

## 补全不完整文档的技巧

当文件内容不完整（如只有 token 片段、缺少来源说明）时：
1. 提取文件中的关键词（如 token 值、项目名）
2. 用 `session_search` 搜索历史会话，追溯原始上下文
3. 从会话记录中提取：来源 URL、创建时间、用途、验证状态
4. 补全后重命名文件为 `.md` 格式，添加结构化说明
