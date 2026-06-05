# PLMS 存储过程/函数清单

## 获取日期: 2026-05-27

## 函数 (8个)

| 名称 | 行数 | 用途推测 |
|-----|------|---------|
| FN_GETQTY_SUM | 33 | 数量汇总 |
| FN_GETVALUE_TEST | 30 | 测试用 |
| FN_RETURN_PLAN_CHANGE | 183 | 计划变更返回 |
| FN_RETURN_TB | 32 | 表返回 |
| FN_RETURN_WATERFALL_TB | 200 | 瀑布图表返回 |
| FUNCTION1 | 4 | 测试用 |
| GET511 | 36 | 511查询 |
| PACKAGE1 | 5 | 包定义 |

## 关键业务存储过程 (按行数排序)

### 核心数据处理 (500+ 行)

| 名称 | 行数 | 推测用途 |
|-----|------|---------|
| LOI_DATA_PROCESS | 1382 | 主数据处理管道 |
| LOI_P_INVENTORY_ALL_W_CATE_BAK | 935 | 库存分类(备份) |
| LOI_P_INV_ALL_W_CATEGORY_H | 928 | 库存分类历史 |
| LOI_P_INVENTORY_ALL_W_CATEGORY | 507 | 库存分类 |
| LOI_P_INVENTORY_ALL_W_CATEGORY_EWM | 507 | 库存分类(EWM) |
| LOI_P_INVENTORY_ALL_W_CATEGORY_XD | 435 | 库存分类(XD) |
| LOC_P_YTD_TLC_OTHERS | 728 | YTD TLC其他 |
| LOI_P_MATERIAL_CATEGORY | 715 | 物料分类 |

### 事实表 ETL (200-500 行)

| 名称 | 行数 | 推测用途 |
|-----|------|---------|
| P_GENERAL_FACT_LTAP_LTAK_POE | 432 | TO事实表ETL |
| LOI_DATA_PROCESS_20200928 | 639 | 数据处理(历史版本) |
| LOC_P_AUTOMATION_NEW | 419 | 自动化率 |
| P_UI_RESULT | 379 | UI结果处理 |
| SP_PRODUCTIVITY_TEST | 376 | 生产率(测试) |
| P_GENERAL_FACT_LTAP_LTAK_HOUR | 366 | TO小时事实表 |
| SP_PRODUCTIVITY | 370 | 生产率 |
| LOI_P_SP_PRODUCTIVITY | 329 | 生产率 |
| LOI_P_INVENTORY_CATEGORY | 333 | 库存分类 |
| LOI_P_DEMAND_REPORT | 275 | 需求报告 |
| P_FACT_WH_PRODUCT_DW | 228 | 仓库产品事实表 |
| P_GENERAL_FACT_MSEG_POE | 187 | 移动事实表 |
| P_GENERAL_FACT_MSEG_POE_HOUR | 178 | 移动小时事实表 |
| P_FACT_ACTUAL_STOCK_DW | 179 | 实际库存事实表 |
| P_GENERAL_FACT_WORKHOUR | 173 | 工时事实表 |
| LOI_P_SMART_REPORT | 184 | 智能报告 |

### 其他重要过程

| 名称 | 行数 | 推测用途 |
|-----|------|---------|
| LOI_P_DEMAND_REPORT_SHORT_VERSION | 145 | 需求报告(简版) |
| P_GENERAL_FACT_LTAP_LTAK_POE_BK | 144 | TO事实表(备份) |
| CIT_CUSTOMER_INVENTORY | 137 | 客户库存 |
| LOI_JOB_DAILY_TASK | 110 | 每日任务 |
| LOI_JOB_DAILY_TASK_XD | 101 | 每日任务(XD) |
| P_GENERAL_FACT_LTAP_LTAK_AGR | 101 | 自动化率事实表 |
| P_UI_RESULT_SUPPLIER | 105 | 供应商UI结果 |
| LOI_P_SUB_PRODUCT_HIE | 98 | 产品层级 |
| LOI_P_BLOCK_STOCK_MEASURES_MOE | 93 | 冻结库存MOE |
| LOI_PDCA_COUNT_FCT | 91 | PDCA计数FCT |
| P_GENERAL_TEMP_LTAP_LTAK_POE | 83 | TO临时表 |
| P_GENERAL_TEMP_LTAP_LTAK_POE_BK | 80 | TO临时表(备份) |
| P_GENERAL_TEMP_LTAP_LTAK_AGR | 78 | 自动化率临时表 |
| P_FACT_AWT_WATERFALL_DETAIL_DW | 76 | AWT瀑布事实表 |
| LOI_P_PDCA_COUNT | 74 | PDCA计数 |
| LOP_DASHBOARD_MONTHLY_LOC | 73 | 月度仪表板(LOC) |
| SP_DELIVERY_WATERFALL | 73 | 交付瀑布 |
| LOI_P_MT_MATERIAL_CATEGORY | 36 | 物料分类 |

## Package

- PACKAGE1 (5行) — 测试用

## 命名规范

- `LOI_P_*` — LOI 存储过程
- `LOI_DATA_*` — LOI 数据处理
- `LOI_JOB_*` — LOI 定时任务
- `P_GENERAL_FACT_*` — 通用事实表ETL
- `P_GENERAL_TEMP_*` — 通用临时表
- `P_FACT_*` — 事实表ETL
- `P_MAINTENANCE_*` — 物化视图维护
- `SP_*` — 存储过程
- `CB$*` — 物化视图(OLAP Cube)
- `FN_*` — 函数
