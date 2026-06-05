# PLMS 视图功能分类规则

> 用于将 LOI_* 视图/MV 按功能域自动分类，适用于知识库文档生成和排错索引。

## 分类规则（按优先级匹配）

| 优先级 | 前缀模式 | 功能域 | 说明 |
|--------|---------|--------|------|
| 1 | `LOI_MV_*` | A_物化视图-业务逻辑 | 所有 LOI_MV_ 前缀的物化视图 |
| 2 | `LOI_V_WH*`, `LOI_V_WAREHOUSE*` | B_仓库容量 | 仓库容量/利用率/趋势 |
| 3 | `LOI_V_INV*`, `LOI_V_INVENTORY*`, `LOI_V_BASE_INVENTORY*`, `LOI_V_STK*`, `LOI_V_STOCK*` | C_库存 | 库存概览/分类/健康度 |
| 4 | `LOI_V_OTD*`, `LOI_V_ALL_OTD*`, `LOI_V_CUS_OTD*`, `LOI_V_SUPPLIER_OTD*`, `LOI_V_DAILY_OTD*`, `LOI_V_MTY_OTD*`, `LOI_V_YEAR_OTD*` | D_OTD | 准时交付率 |
| 5 | `LOI_V_OUTPUT*`, `LOI_V_PRODUCT*`(不含_H), `LOI_V_PLANNED*`, `LOI_V_PRO_*` | E_产出 | 生产率/产出/效率 |
| 6 | `LOI_V_LZT*`, `LOI_V_SYSTEM_LZT*` | F_LZT | 理想周期时间 |
| 7 | `LOI_V_AWT*`, `LOI_V_KWT*`, `LOI_V_QINP*`, `LOI_V_SUB_AWT*`, `LOI_V_PLD_ACT_AWT*` | G_AWT/KWT | AWT/KWT 库存/调平 |
| 8 | `LOI_V_COST*`, `LOI_V_FREIGHT*`, `LOI_V_TCO*`, `LOI_V_LOADING*`, `LOI_V_N_F_COST*` | H_成本 | 物流成本/TCO/运费 |
| 9 | `LOI_V_LOP*`, `LOI_V_LIS*` | I_LOP/LIS | 看板/LIS 指标 |
| 10 | `LOI_V_BASE_*` | J_基础视图 | SAP 基础数据封装 |
| 11 | `LOI_V_TEMP_*` | K_临时视图 | 中间计算/临时数据 |
| 12 | `LOI_V_PKG*`, `LOI_V_PACKAGE*`, `LOI_V_SET_PKG*` | L_包装 | 包装用量/物料/结构 |
| 13 | `LOI_V_DEMAND*`, `LOI_V_BLUESHEET*`, `LOI_V_YEARLY_PLAN*`, `LOI_V_MAKE_PLAN*`, `LOI_V_SOURCE_PLAN*`, `LOI_V_NIVPLUES*` | M_需求/计划 | 需求报告/计划变更 |
| 14 | `LOI_V_TO_*`, `LOI_V_OPEN_TO*`, `LOI_V_INBOUND*`, `LOI_V_OUTBOUND*`, `LOI_V_TO$`, `LOI_V_TO_SUM*`, `LOI_V_TO_HOUR*`, `LOI_V_TO_PROCESS*` | N_TO | Transfer Order |
| 15 | `LOI_V_WORKHOUR*`, `LOI_V_ATTENDANCE*`, `LOI_V_PEOPLE*`, `LOI_V_DAILY_PRODUCTION*`, `LOI_V_DAILY_PRODUCTIVITY*` | O_工时 | 工时/人力/出勤 |
| 16 | `LOI_V_SCC*`, `LOI_V_COVERAGE*`, `LOI_V_WHSTOCK*`, `LOI_V_MATERIAL_COVERAGE*` | P_覆盖 | 供应覆盖天数 |
| 17 | `LOI_V_RFID*`, `LOI_V_KLT*` | Q_RFID/KLT | 容器/RFID 追踪 |
| 18 | `LOI_V_DE_*`, `LOI_V_MAE*`, `LOI_V_DUPLICATED*`, `LOI_V_GR_*` | R_DE异常 | 发货异常/重复GR |
| 19 | `LOI_V_SSC*`, `LOI_V_MGT*` | S_管理看板 | SSC/MGT 综合看板 |
| 20 | `LOI_V_RESB*`, `LOI_V_BOM*` | T_BOM/预留 | BOM 用量/预留物料 |
| 21 | `LOI_V_LOM*`, `LOI_V_CONTROLTOWER*`, `LOI_V_C_T*` | U_LOM | LOM/ControlTower |
| 22 | `LOI_V_CRS*` | V_CRS | CRS 报表 |
| 23 | `LOI_V_ISTAR*`, `LOI_V_MOE*` | W_ISTAR | ISTAR/MOE 指标 |
| 24 | `LOI_V_OVER*`, `LOI_V_SLOW*`, `LOI_V_BLOCKED*`, `LOI_V_SCRAP*`, `LOI_V_OVERDUE*`, `LOI_V_SL_*` | X_异常库存 | 超期/阻滞/报废 |
| 25 | `LOI_V_SPECIAL*`, `LOI_V_HXY*` | Y_特殊运费 | 特殊运费/预测 |
| 26 | `LOI_V_PARETO*`, `LOI_V_TOLERENCE*`, `LOI_V_TOP10*`, `LOI_V_REASON*`, `LOI_V_TCT*`, `LOI_V_LABEL*` | Z_分析 | 帕累托/分析统计 |
| 27 | `LOI_V_MSEG*`, `LOI_V_LTAP*` | ZA_SAP导出 | SAP 数据导出/提取 |
| 28 | `LOI_V_DEFAULT*`, `LOI_V_REMARK*`, `LOI_V_KDMAT*`, `LOI_V_SDSA*`, `LOI_V_SOLDTO*`, `LOI_V_DIQ*`, `LOI_V_RP_*`, `LOI_V_RTP*`, `LOI_V_PROCESS_PLAN*`, `LOI_V_TABLE_*`, `LOI_V_SYSTEM_*`, `LOI_V_PLANT*`, `LOI_V_WH_B304*` | ZB_校验 | 校验/系统/工具 |
| 29 | `LOI_V_TREE_*`, `LOI_V_SUB_WC*`, `LOI_V_SUM_*`, `LOI_V_SUB_INVENTORY*` | ZC_汇总 | 树状/汇总视图 |
| 30 | `LOI_V_PPD*`, `LOI_V_FCT_*`, `LOI_V_M0*` | ZD_生产计划 | 生产计划/预测 |
| 31 | `CB$*`, `DIM_*`, `LOP3_*`, `LOI_30*`, `LOI_310*`, `LOI_AWT_WATERFALL*`, `LOI_BK_*`, `LOI_INVENTORY_*`, `LOI_LOGISTIC*`, `LOI_LZT_*`, `LOI_MT_*`, `LOI_PDCA*`, `LOI_PEOPLE*`, `LOI_RBCD*`, `LOI_TO_PROCESS*`, `M_V_*`, `MVIEW_*` | ZE_其他 | 非标准前缀对象 |

## 元数据提取规则

从 SQL 定义中自动提取：
- **刷新策略**: `REFRESH (COMPLETE|FORCE|FAST) ON DEMAND`
- **调度周期**: `NEXT (SYSDATE + expr)`
- **源表**: `FROM table` 和 `JOIN table`（排除 DUAL、SELECT、LOGPOE）

## 使用场景

1. 批量导入视图定义到知识库时自动分类
2. 排错时快速定位相关视图（如"库存异常" → 查 C_库存 类别）
3. 生成分类汇总表

## 已知分类统计（2026-05-28，488个对象）

```
  其他/未分类:    163    库存 Inventory:   33
  LOP/LIS 看板:   26    OTD 准时交付:     26
  基础视图 BASE:  25    产出 Productivity: 25
  AWT/KWT/QINP:  18    仓库容量:         18
  临时视图 TEMP:  18    LZT:              15
  Transfer Order: 13    成本/TCO:         12
  包装 Package:   10    需求/计划:         13
  LOM/CT:          7    SSC/MGT:           7
  工时/人力:        6    异常库存/超期:     10
  校验/系统/工具:   14    分析/统计:         7
  BOM/预留:         4    供应覆盖:           4
  RFID/KLT:         4    DE发货/异常:        3
  CRS:              3    ISTAR/MOE:          3
  特殊运费:         2    生产计划:           3
  树状/汇总:        3    SAP导出:            2
```

> "其他/未分类" 163个需要进一步人工归类或新增规则。
