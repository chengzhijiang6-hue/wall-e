# PLMS (LOM Dashboard) 数据血缘映射

系统: https://wx-lom-app06.apac.bosch.com:9080/
技术栈: Vue.js + Spring Boot + MyBatis + Oracle (schema: LOGPOE)
认证: Azure AD SSO (azureToken) | 成功码: 1200 | 超时: 80s

---

## 页面 → 数据来源（中英对照）

### Home / 首页 `/`
说明: 系统主入口，聚合各模块 KPI 概览卡片

- Warehouse Capacity Overview / 仓库容量概览
  API: capacityOverviewApi.js, mapCityApi.js, overviewApi.js, wareHouseApi.js
  Controller: WHLoiOver2yStockController.java
  表: LOI_V_OVER_2Y_STOCK

- MAE Overview / MAE 概览
  API: maeApi.js
  Controller: MachineVehicleMaintenanceController.java, MachineVehicleMasterDataController.java
  表: LOI_AA_LINE_PPU, LOI_MV_AUTOGR_PPU, LOI_MV_AUTORACK_PPU, LOI_PJ_PPU_MAPPING, LOI_V_LOADING_VOLUME_COST, LOI_V_OUTPUT_MBR_WHHC_PJ, MACHINE_VEHICLE_MAINTENANCE

- Productivity Overview / 生产率概览
  API: productivityDialogApi.js
  Controller: ProductivityLevelController.java
  表: LOI_LOM_PEOPLE_HC, LOI_SHIFT_CO_TREND, LOI_V_OUTPUT_MBR_WHHC, LOI_V_PRODUCTIVITY_LV1, PEOPLE_CF_MBR_VERSION, U_PRODUCTIVITY_TARGET_DATA

- People Overview / 人员概览 → API: peopleApi.js → Controller: PeopleCertificateStatusController.java

- Shelf Life Overview / 保质期概览 → API: homeShelfLifeApi.js

### Dock / 月台 `/dock`
说明: 装卸月台管理：时间窗、占用率、Lead Time、OTD、故障跟踪

- Dock Lead Time / 月台 Lead Time → API: grLeadTime.js
- Dock Utilization / 月台占用率 → API: goodsReceiptApi.js → Controller: DkUtilizationTargetController, GROpenToController → 表: DK_UTILIZATION_TARGET, LOI_MV_OPEN_TO_DETAILS
- Dock Failure / 月台故障 → API: dockApi.js → Controller: AreaDockMappingController, DkMilkrunTargetController → 表: AREA_DOCK_MAPPING, DK_MILKRUN_TARGET, LOI_V_MILKRUN_TIME_WINDOW
- Dock Time Window / 时间窗 → API: grTimeWindow.js → Controller: DkMilkrunTargetController → 表: DK_MILKRUN_TARGET, LOI_V_MILKRUN_TIME_WINDOW
- Dock OTD / 月台 OTD → API: grTimeWindow.js → Controller: DkMilkrunTargetController → 表: DK_MILKRUN_TARGET, LOI_V_MILKRUN_TIME_WINDOW
- Failure Pareto / 故障 Pareto → API: dockApi.js → Controller: AreaDockMappingController, DkMilkrunTargetController → 表: AREA_DOCK_MAPPING, DK_MILKRUN_TARGET

### Goods Receipt (GR) / 收货 `/goods-receipt`
说明: 收货管理：流程步骤、Open TO、自动化率、质量、ASN

- Process Steps / 流程步骤 (`/goods-receipt/process-steps`) → API: processStepsApi.js
- Open TO (`/goods-receipt/open-to`) → API: openToApi.js
- Failure Pareto → API: qualityApi.js, receiptQualityApi.js
- GR Automation Rate / 自动化率 → API: automation.js, grAutomationDialogApi.js → Controller: GRAutoRateController → 表: GR_AUTOMATION_RATE_DATA, V_GR_AUTOMATION_RATE_DATA
- Receipt Quality / 收货质量 → API: receiptQualityApi.js
- Average Lead Time / 平均 Lead Time → API: zrwLeadTime.js
- AGR KPI Tracking (`/agr-kpi-tracking`) → API: agrKpiTrackingApi.js
- GR CIP Management (`/point-cip`) → API: grCipManageApi.js

### Goods Issue (GI) / 发货 `/goods-issue`
说明: 发货管理：OTD、Lead Time、装载率、Reph 工位、Cycle Time

- Reph Station Daily (`/reph-station`) → API: testApi.js（IES 外部系统）
- GI Open TO → API: issueApi.js
- GI OTD → API: testApi.js（IES 外部系统）
- GI Load Rate / 装载率 → API: testApi.js（IES 外部系统）
- GI Lead Time → API: testApi.js（IES 外部系统）
- GI Failure Pareto → API: issueApi.js
- GI Incidence / 发生率 → API: dispatchApi.js → Controller: DEMaterialFlowController → 表: LOI_MV_DE_MATERIAL_FLOW, U_DISPATCH
- Reph Daily / Cycle Daily → API: iesApi.js（IES 外部系统）

### Goods Dispatch (DE) / 发运 `/goods-dispatch`
说明: 发运管理：自动化率、Lead Time、Open 失败、物料流

- DE Lead Time → API: dispatchApi.js → Controller: DEMaterialFlowController → 表: LOI_MV_DE_MATERIAL_FLOW, U_DISPATCH
- DE Automation Rate → API: toHourHistoryApi.js → Controller: ProductivityLevelController → 表: LOI_V_PRODUCTIVITY_LV1

### Warehouse / 仓库 `/ware-house`
说明: 仓库管理：容量、产品库存、超2年库存、慢流、死库存、库位状态

- Warehouse Status (`/ware-house-status`) → API: wareHouseApi.js → Controller: WHLoiOver2yStockController
- WH Product WX (`/wh-product-wx`) → API: whProductDwApi.js
- WH Product BD (`/wh-product-bd`) → API: whProductDwApi.js
- WH Product WF (`/wh-product-wf`) → API: whProductDwApi.js
- AR1 Overview (`/ar1-overview`) → API: wareHouseApi.js
- Storage Bin 301/302/307 (`/room-301`) → API: storageBinStatusApi.js

### Goods Repack / 翻包 `/goods-repack`
- RTP Rate → API: rpApi.js → Controller: RPRTPRateController → 表: LOI_V_RTP_RATE_DATE, LOI_V_RTP_RATE_MONTH
- Top PN → API: rpApi.js → Controller: RpTopMaterialController → 表: LOI_V_TOP10_PN_BATCH_CT
- KPIs: LOI_V_COUNT_RP, RP_REPACKING_TARGET, RP_RATE_OVERVIEW_TARGET

### Safety / 安全 `/safety`
- LPC Execution Rate (`/lpc-execution-rate`) → API: executionRateApi.js → Controller: UExecutionRateController → 表: U_EXECUTION_RATE
- Training Rate (`/training-rate`) → API: executionRateApi.js → Controller: USafetyTrainController → 表: U_SAFETY_TRAIN

### People / 人员
- Attendance (`/attendance`) → API: attendanceNewApi.js
- People Skills (`/skill`) → 无直接 API
- OT Statistics (`/ot-statistics`) → API: overTimeApi.js

### Cost / PPU 成本
- Service Cost Tracking (`/PPU-cost-tracking`) → API: maeApi.js → Controller: MachineVehicleMasterDataController → 表: LOI_AA_LINE_PPU, LOI_V_LOADING_VOLUME_COST
- AGV/AGR/AutoRack/AA Line 跟踪 → API: maeApi.js（同上）

### MAE / 设备效率
- AGV (`/slim-agv`) → API: GIplans.js, maeApi.js
- AGR (`/slim-agr`) → API: goodsReceiptApi.js
- AutoRack (`/auto-rack`) → API: maeApi.js

### Package / 包装 `/package`
- Clean Complaints → API: cleanComplaintApi.js

### Delivery / 交付 `/deliver`
- RBCD/RDC Delivery → API: homeDeliverApi.js → Controller: DeliveryOverviewController → 表: LOI_V_LOM_DEL_ACT_D, LOI_V_LOM_DEL_ACT_M, LOI_V_RBCD_DEL_SUM, LOI_V_RDC_DEL_SUM

### Environment / 环境监控 `/environment`
- Environment Overview + Detail → API: environmentApi.js

### PDCA
- Leveling PDCA (`/leveling-pdca`) / Block PDCA (`/block-pdca`) → API: pdcaData.js

---

## 关键数据库视图

| 视图 | 类型 | Controller |
|------|------|------------|
| LOI_V_OVER_2Y_STOCK | View | WHLoiOver2yStockController |
| LOI_V_DEAD_STOCK | View | BlockStockController |
| LOI_V_OPEN_TO | View | GROpenToController |
| LOI_MV_OPEN_TO_DETAILS | MV | GROpenToController |
| LOI_V_LOM_DEL_ACT_D | View | DeliveryOverviewController |
| LOI_V_LOM_DEL_ACT_M | View | DeliveryOverviewController |
| LOI_V_FAILURE_MANAGEMENT | View | GiFailureDataController |
| LOI_V_GI_INCIDENCE | View | GiIncidenceController |
| LOI_V_PRODUCTIVITY_LV1 | View | ProductivityLevelController |
| LOI_V_OUTPUT_MBR_WHHC | View | ProductivityLevelController |
| LOI_V_MILKRUN_TIME_WINDOW | View | DkMilkrunTargetController |
| LOI_V_DOCK_TIME_WINDOW | View | DockTimeWindowController |
| LOI_V_RTP_RATE_DATE | View | RPRTPRateController |
| LOI_V_SLOW_MOVING_DETAIL | View | WhSlowMovingController |
| GR_AUTOMATION_RATE_DATA | Table | GRAutoRateController |
| V_GR_AUTOMATION_RATE_DATA | View | GRAutoRateController |

---

## 外部系统接口

- **IES** (Internal Execution System): GI 计划、Reph 工位、AGV 时间、交付绩效
- **SAP**: 仓库接口
- **AGR**: AGR 系统
- **IMR**: IMR 系统
- **IRP**: IRP 系统
- **PI**: PI 系统

---

## 统计

- 77 路由页面, 615 Vue 组件
- 112 API 文件, 213 Controller, 206 Mapper XML
- 244 数据库表/视图（LOGPOE schema）
- PDF 操作手册中发现 87 张表/视图（含 SQL 查询）

## PDF 补充：通用数据 Cube

GR/RP/GI/DE 的 Workload 通过 UNION ALL 聚合自以下 Cube：

- CB$CUBE_LTAP_LTAK_POE — Transfer Order 工作量
- CB$CUBE_MSEG — 移动类型工作量
- CB$CUBE_AGR — AGR 工作量
- CB$CUBE_WORKHOUR — 工时

查询模式: `SELECT WORKLOAD FROM CB$CUBE_xxx WHERE LOCATION='GR'/'RP'/'GI'/'DE'`

## PDF 补充：关键业务逻辑

**GR Productivity**: workload = LTAP_LTAK_POE + MSEG + AGR (UNION ALL), productivity = workload / workhour

**WH Occupation Rate**: occupied / max_capacity, 来自 LOI_MT_WAREHOUSE_DEFINITION + LOI_V_OCCUPATION_RATE

**WH Storage Bin 计数规则**:
- 普通仓位: 1 bin = 1 count
- V02 (RDC-WX2): 按库位计数
- AR1 (普通托盘 SU≠K3/K4/K5): 按 HU 计数
- AR1 (特殊托盘 SU=K3/K4/K5): 按 HU × 2

**Machine Overdue MAE**: next_maintenance_date <= today, 用 ROW_NUMBER() 取每个 vehicle 最新维护记录

**Quality Shelf Life**: 匹配 LOI_V_BASE_SOURCE_LIST + LOI_V_BASE_MATERIAL_MASTER, 分三类: In Three Months / Match Standard / No source list
