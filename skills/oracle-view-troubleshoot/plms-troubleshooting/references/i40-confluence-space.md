# I4.0 Confluence 空间与 PLMS 的关系

## 来源

Confluence 空间 `I40Projects`（显示名 `RBCDLOI`），v12，导出于 2026-05-27。
原始文件: `knowledge/I4.0/99_原始导出/`（519 个 HTML 页面）

## 空间结构

I4.0 Projects 是 RBCD LOI 团队的 Confluence 文档空间，包含多个数字化物流子项目。
其中 PLMS (LOM Dashboard) 是最大的子项目，约占 10% 页面。

### 子项目清单

| 子项目 | PLMS 关联 |
|--------|-----------|
| PLMS / LOM Dashboard | **直接相关** |
| LIS (Logistics Information System) | 间接相关 |
| LOP (Logistics Operations Platform) | 间接相关 |
| AGV / AutoGR / PPU | 不相关 |
| IES (智能设备系统) | 不相关 |
| RFID | 不相关 |
| AWT (自动仓库运输) | 不相关 |
| Auto MBR / Capacity Simulation | 不相关 |
| QinP (清浦 JIT 供应) | 不相关 |
| Smart Supply Chain / TEF | 不相关 |

## PLMS 相关页面（~50 页）

集中在 `Physical Logistics Management System _ LOM Dashboard` 页面树下：

- **Production Manual**: 每个功能域的 UI + SQL 逻辑
- **L2/L3 下钻**: GR/GI/DE/RP/DK/Productivity/Delivery/People/Safety 各模块
- **排错记录**: 30+ 个日期编号的 Bug 页面

## 关键参考文件

| 文件 | 大小 | 说明 |
|------|------|------|
| Common-Table_View.1868842067.html | 65KB | 所有公共表/视图清单 |
| Redundant-DB-Items.1895643564.html | 72KB | 冗余数据库项 |
| Job_List_VM.1888997170.html | 83KB | VM 作业列表 |
| I-4.0-System-Architecture.1291723331.html | 34KB | LOP/LOM locked reports |

## 排错记录中的高频 LOI 视图

- `LOI_V_INVENTORY_ALL_W_CATEGORY` — 库存汇总（含分类）
- `LOI_V_WH_FUTURE_TREND` / `LOI_V_WH_FUTURE_TREND_DETAIL` — 仓库预测趋势
- `LOI_V_OUTPUT_FULL` — 产出全量
- `LOI_V_DEAD_STOCK` — 死库存
- `LOI_MT_BLOCKED_STOCK_MEASURES` — 封存库存措施
- `LOI_HIS_SUPPLY_ON` — 历史供应
- `LOI_P_MATERIAL_CATEGORY` / `LOI_P_INVENTORY_ALL_W_CATEGORY` — 材料分类存储过程
- `P_UI_RESULT` — 通用 UI 结果存储过程

## LOP/LOM/LIS 系统关系

- **LOP** (Logistics Operations Platform): 物流操作平台，面向供应链操作层面
- **LOM** (Physical Logistics Management System): 物流管理仪表盘，面向管理层 KPI
- **LIS** (Logistics Information System): 物流信息系统，面向日常产出监控
- 三者共享 Oracle LOGPOE 数据库，通过 BODS ETL 作业从 SAP 同步数据

## 使用场景

当排错时需要查看 Dashboard 页面的 SQL 逻辑、数据源、或历史问题记录：
1. 查 `knowledge/I4.0/02_PLMS相关/页面索引.md` 找到对应功能域页面
2. 在 `knowledge/I4.0/99_原始导出/` 中打开对应 HTML 文件
3. 搜索 `Database & Data logic` 或 `Calculation logic` 区域获取 SQL
4. 查 `knowledge/I4.0/04_排错记录/排错记录索引.md` 看是否有类似历史问题
