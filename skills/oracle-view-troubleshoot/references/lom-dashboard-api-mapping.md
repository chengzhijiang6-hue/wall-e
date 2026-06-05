# LOM Dashboard 前端页面 → API → 数据库对象 映射表

## Warehouse Occupation Overview 页面
- **前端文件**: `src/views/Home/HomeCapacity.vue`
- **下载按钮**: `handleDownLoad(name)` → `window.open('/api/wh/over-2y/export?wh=${name}')`
- **后端 Controller**: `WHLoiOver2yStockController.exportSheet()`
- **Mapper**: `LoiVOver2yStockMapper.getByPage()`
- **SQL**: `SELECT * FROM ${schema}.LOI_V_OVER_2Y_STOCK WHERE UPPER(wh) = UPPER(#{wh})`
- **数据库对象**: `LOI_V_OVER_2Y_STOCK` (VIEW, 查询 `FACT_WH_PRODUCT_DW` 中 >730天 的数据)
- **仓库名映射**: RBCD, RDC-WX, RDC-WX2, RDC-BD, RBCD-WX03

## Bonded WH 详情页
- **前端文件**: `src/views/WareHouseNew/Product/WareHouseProductBd.vue`
- **下载按钮**: `exportExcel()` → `window.open('/api/excel-product')`
- **后端 Controller**: `ExcelProductController.excelProductDownload()`
- **Mapper**: `NewWhProductDwDao.findAllExcel()`
- **SQL**: `SELECT * FROM ${schema}.FACT_V_WH_PRODUCT_DW` (无 WHERE，全量导出)
- **数据库对象**: `FACT_V_WH_PRODUCT_DW` (VIEW, 查询 `FACT_WH_PRODUCT_DW`)

## 页面数据接口（非下载）
- **表格数据**: `POST /api/wh-product-dw-all` → `NewWhProductDwDao.findAll()` → 带 `WHERE WAREHOUSE='RDC-BD'`
- **饼图数据**: `GET /api/wh-product-dw-pie` → `NewWhProductDwDao.findPieBar()` → 带 `WHERE WAREHOUSE='RDC-BD'`

## 关键数据库对象
| 对象名 | 类型 | 数据来源 | 备注 |
|--------|------|----------|------|
| `FACT_WH_PRODUCT_DW` | TABLE | ETL | 基础表，43462行 |
| `FACT_V_WH_PRODUCT_DW` | VIEW | `FACT_WH_PRODUCT_DW` | CASE WHEN 转换仓库名 |
| `LOI_V_OVER_2Y_STOCK` | VIEW | `FACT_WH_PRODUCT_DW` | 只保留 >730天 数据 |
| `LOI_V_WH_OVERVIEW` | MATERIALIZED VIEW | 多表汇总 | 每4小时刷新，有 OR 优先级问题 |
| `LOI_V_WAREHOUSE_CAPACITY_BASE` | VIEW | 基础容量数据 | 被 LOI_V_WH_OVERVIEW 依赖 |
| `LOI_MT_WAREHOUSE_DEFINITION` | TABLE | 仓库定义 | 最大容量配置 |

## 仓库名对照
| 前端名称 | 数据库 WAREHOUSE 值 | 备注 |
|----------|---------------------|------|
| RBCD | RBCD | 主仓库 |
| RDC-WX | RDC-WX | 无锡RDC |
| RDC-WF | RBCD-WX03 | 前端显示名不同 |
| RDC-BD | RDC-BD | Bonded WH，无超2年库存 |
| - | RDC-WX2 | 数据库有但前端不显示 |
