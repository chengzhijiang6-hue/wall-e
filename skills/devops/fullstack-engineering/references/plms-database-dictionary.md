# PLMS 数据库字典 (LOGPOE Schema)

提取时间: 2026-05-27 | 数据库: wx0orarac02.apac.bosch.com:38000/bcdlog_app.apac.bosch.com

## 物化视图 (14个, 全部 DEMAND 刷新)

| 名称 | 方法 | 状态 | 核心逻辑 |
|------|------|------|---------|
| LOI_MV_AUTOGR_PPU | COMPLETE | OK | GR W/WO Camera TO |
| LOI_MV_AUTORACK_PPU | COMPLETE | OK | AutoRack TO |
| LOI_MV_DE_MATERIAL_FLOW | COMPLETE | NEEDS_COMPILE | DE物料流分类 |
| LOI_MV_OPEN_TO_DETAILS | FORCE | NEEDS_COMPILE | Open TO详情(20+UNION) |
| LOI_MV_TO_HOUR_HISTORY | COMPLETE | FRESH | TO每小时历史 |
| LOI_MV_WH_CAPACITY_DETAIL_SD | COMPLETE | NEEDS_COMPILE | 仓库容量(AR1×2) |

刷新: `EXEC DBMS_MVIEW.REFRESH('LOGPOE.视图名', 'C');`

## 关键视图逻辑

- LOI_V_OPEN_TO: 20+UNION ALL, 源LTAP_LTAK_POE_OPEN_TO, 交通灯=DELTA*24h
- LOI_V_OVER_2Y_STOCK: FACT_WH_PRODUCT_DW过滤GR>730天
- LOI_V_PRODUCTIVITY_LV1: CB$CUBE_LTAP_LTAK_POE+CB$CUBE_WORKHOUR+CB$CUBE_TARGET
- LOI_V_TO_SUM: FACT_MSEG_POE_HOUR+FACT_LTAP_LTAK_POE_HOUR+基线(DE=8,GI=25,GR=12,RP=2)
- LOI_V_AGR_RATE: RFID_GR/Auto Camera GR/Other Manual GR/ALPE Scan
- LOI_V_BASE_MATERIAL_MASTER: 88列, JOIN SAP_MARC+DIM_MATERIAL+LOI_MT_MATERIAL_CATEGORY+SAP_MARA

## 源表依赖

- LTAP_LTAK_POE(1.8M) → LOI_MV_OPEN_TO_DETAILS, LOI_MV_DE_MATERIAL_FLOW, LOI_MV_AUTOGR_PPU
- LTAP_LTAK_POE_GI_TO(1.8M) → GI装载率
- FACT_WH_PRODUCT_DW → LOI_V_OVER_2Y_STOCK, LOI_MV_WH_CAPACITY_DETAIL_SD
- GR_AUTOMATION_RATE_DATA(554K) → LOI_V_AGR_RATE
- CB$CUBE_* → LOI_V_PRODUCTIVITY_LV1
- DIQ_SU_COUNT_RP_SUMMARY(2.5M) → LOI_V_COUNT_RP

## 交叉比对 (代码扫描 + PDF手册 + 数据库直查)

| 维度 | 数量 |
|------|------|
| 数据库实际对象 | 179 |
| 文档记录 | 168 |
| 共同验证 | 146 |
| 仅数据库 | 33 (SAP源表+ETL+维度表) |
| 仅文档 | 12 (待确认) |

## Open TO 交通灯阈值 (小时)

| 业务类型 | OK | REMINDER | FAIL |
|----------|-----|----------|------|
| DE 成品发货(WX03) | < 3 | 3-4 | > 4 |
| DE 成品发货(B304) | < 5 | 5-6 | > 6 |
| DE 体移库 | < 5 | 5-6 | > 6 |
| GR 直收/翻包/包材 | < 3 | 5-6 | > 6 |
| RP 二级拉动 | < 7 | 7-8 | > 8 |
| DE 样品(RBHP) | < 8 | 8-14 | > 14 |
| GR 超市直送(FCI) | < 12 | 12-14 | > 14 |

## 库位计数规则

- AR1 + SU IN (K3,K4,K5): COUNT(HU)×2
- AR1 + 其他: COUNT(HU)
- 非AR1: COUNT(HU)
