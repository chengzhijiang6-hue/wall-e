# LOM Dashboard 项目调试笔记

## 项目架构

### 部署拓扑
```
生产环境: wx-lom-app06.apac.bosch.com:9080 (HTTPS)
├─ 前端: Vue 2 SPA (编译后静态资源, 由 Spring Boot 直接托管)
├─ 后端: Spring Boot 2.5.5 (单体应用, 同一端口)
├─ 认证: Azure AD SSO (via wx-web-td01.apac.bosch.com/WindowsAuth)
└─ 数据库: Oracle (LOGPOE schema)
```
- 前端和后端合体部署在 9080 端口，无 Nginx 反向代理层
- `/api/*` 路径由 Spring Boot Controller 处理，其余路径 fallback 到前端 index.html (SPA catch-all)
- 所有 API 请求需要 Azure AD SSO token，未认证返回 `{"msg":"Invalid token","code":"50000"}`

### 后端
- **路径**: `/mnt/c/Users/CZE8WX/Desktop/work/PLMS/lom-dashboard-serve-master-develop/`
- **框架**: Spring Boot 2.5.5 + MyBatis 2.0.1 + Oracle
- **Java**: 1.8
- **规模**: 771个Java文件, 232个Controller, 213个MyBatis XML
- **端口**: dev=9090, prod=9071
- **Schema**: dev=`LOM_PDCA`, prod=`logpoe`
- **连接池**: HikariCP 3.4.5
- **API文档**: Knife4j 2.0.9 (Swagger增强, 路径未独立暴露)
- **关键依赖**: core-2.0.jar (自研核心库), ojdbc7 (Oracle驱动, 本地JAR)
- **Maven仓库**: bcsc-digi.apac.bosch.com (Bosch内部Nexus)
- **数据库支持**: Oracle (主) + SQL Server + MySQL
- **分析报告**: `项目分析报告.md` 和 `数据库表结构分析报告.md` 已存在于项目根目录

### 前端
- **路径**: `/mnt/c/Users/CZE8WX/Desktop/work/PLMS/source code/`
- **框架**: Vue 2.6 + Vue Router 3 + Vuex 3
- **UI库**: Element UI 2.12
- **图表**: ECharts 5 + ECharts 4 (并存) + AntV G2/G6
- **地图**: Leaflet + Vue-AMap
- **构建**: Vue CLI 3 (`vue-cli-service`)
- **API代理**: `vue.config.js` 中 `/api/*` → `https://wx-lom-app06.apac.bosch.com:9080/api`
- **IES代理**: `/GIApiURL/*` → `https://wx-lom-app06.apac.bosch.com:9080/GIApiURL`
- **认证**: Azure SSO (加载 `https://wx-web-td01.apac.bosch.com/WindowsAuth` 脚本)
- **SPA路由**: history 模式, 约50+页面

### 数据库
- **类型**: Oracle
- **连接**: `jdbc:oracle:thin:@//wx0orarac02.apac.bosch.com:38000/rbcdlog_app.apac.bosch.com`
- **用户**: dev=`LOM_PDCA`, prod=`LOG_PDCA`
- **表空间**: RBCDLOG
- **核心表**: 18+张 (libs/ 目录下 SQL 脚本定义)
  - 系统: LOM_SYS_DICT / LOM_SYS_DICT_ITEM
  - 区域: AREA_DOCK_MAPPING / AREA_EMR_MAPPING / GR_NTACCOUNT_AREA_MAPPING
  - 目标: DK_EMR_OTD_TARGET / DK_MILKRUN_TARGET / DK_UTILIZATION_TARGET / RP_RATE_OVERVIEW_TARGET
  - 流程: GR_PROCESS_STEPS / GR_PROCESS_STEPS_DETAILS
  - 设备: MACHINE_VEHICLE_MASTER_DATA / MACHINE_VEHICLE_MAINTENANCE
  - 人员: PEOPLE_CERTIFICATE_STATUS / PEOPLE_CF_MBR_VERSION / PLANNER_DEPT_EMAIL_MAPPING
  - 数据: GR_AUTOMATION_RATE_DATA (有视图 V_GR_AUTOMATION_RATE_DATA)
  - 评估: LOM_PERSONAL_SKILL_EVALUATION

### 前端路由关键页面
| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | HomeNew.vue | 首页 |
| `/login` | Login.vue | 登录 |
| `/goods-receipt` | GoodsReceipt.vue | 收货(GR) |
| `/goods-issue` | GoodIssuenew.vue | 发货(GI) |
| `/goods-dispatch` | GoodsDispatchNew.vue | 调度 |
| `/ware-house` | WareHouseNew.vue | 仓库概览 |
| `/dock` | DockNew.vue | 月台管理 |
| `/deliver` | Deliver.vue | 配送 |
| `/machine` | MachineSecond.vue | 设备管理 |
| `/skill` | PeopleSkills.vue | 人员技能 |
| `/safety` | Safety.vue | 安全 |
| `/environment` | EnvironmentOverview.vue | 环境监控 |
| `/attendance` | HomeAttendanceNew.vue | 考勤 |
| `/PPU-cost-tracking` | CostView.vue | PPU成本 |
| `/slim-agv` | SlimAgv.vue | AGV指标 |
| `/slim-agr` | SlimAgr.vue | AGR指标 |
| `/auto-rack` | AutoRack.vue | 自动货架 |
| `/leveling-pdca` | Pdca.vue | 平准化PDCA |
| `/block-pdca` | BlockPdca.vue | Block PDCA |
| `/HeatMap` | HeatMap.vue | 热力图 |
| `/TrafficLight` | TrafficLight.vue | 交通灯 |

## 关键表/视图

| 名称 | 类型 | 说明 | 数据来源 |
|------|------|------|----------|
| `FACT_V_WH_PRODUCT_DW` | 视图 | 仓库产品数据 | 底层表 `FACT_WH_PRODUCT_DW` |
| `FACT_WH_PRODUCT_DW` | 表 | 仓库产品基础表 | ETL |
| `LOI_V_WH_OVERVIEW` | 表/物化视图 | 仓库概览 | ETL 或物化视图刷新 |
| `LOI_V_WAREHOUSE_CAPACITY_BASE` | 视图 | 仓库容量基础 | 底层表 |
| `LOI_V_SUB_INVENTORY_ALL_LATEST` | 视图 | 子库存最新数据 | 底层表 |

## 下载功能链路

### Bonded WH 下载按钮
```
前端: WareHouseProductBd.vue → exportExcel()
  ↓ window.open('/api/excel-product')
nginx: pathRewrite ^/api → ""
  ↓ /excel-product
后端: ExcelProductController.excelProductDownload()
  ↓ NewWhProductDwDao.findAllExcel(schema)
SQL: SELECT * FROM ${schema}.FACT_V_WH_PRODUCT_DW
  ↓
ExcelUtil.exportExcelOver() → 生成 .xls 文件
```

### Warehouse Occupation Overview 页面数据
```
前端: HomeCapacityOverview.vue → getWhOverview()
  ↓ /api/wh-overview
后端: UWhMaxOccupiedController.getWhOverview()
  ↓ primaryJdbcTemplate.queryForList("select * from schema.LOI_V_WH_OVERVIEW")
  ↓
返回 JSON 数据给前端
```

## 已知问题和解决方案

### 1. 物化视图 ORA-00909
**症状**: `LOI_V_WH_OVERVIEW` MATERIALIZED VIEW 状态为 INVALID
**根因**: SQL 中 OR 条件缺少括号（优先级问题）
**解决**: `EXEC DBMS_MVIEW.REFRESH('LOGPOE.LOI_V_WH_OVERVIEW');`

### 2. 下载 Excel 只有列名
**症状**: 下载的 Excel 文件有表头但没有数据行
**可能根因**:
- 底层视图 INVALID
- ETL 依赖表为空
- 前端下载逻辑依赖页面数据（而非下载接口数据）

### 3. nginx upstream timeout
**症状**: nginx 日志显示 `upstream timed out`
**根因**: Java 应用无响应
**检查**: `netstat -ano | findstr :9071`

## 调试命令速查

### 数据库
```sql
-- 检查对象状态
SELECT OBJECT_NAME, OBJECT_TYPE, STATUS FROM ALL_OBJECTS WHERE OBJECT_NAME = 'XXX' AND OWNER = 'LOGPOE';

-- 检查物化视图状态
SELECT MVIEW_NAME, LAST_REFRESH_DATE, STALENESS, COMPILE_STATE FROM ALL_MVIEWS WHERE MVIEW_NAME = 'XXX';

-- 刷新物化视图
EXEC DBMS_MVIEW.REFRESH('LOGPOE.XXX');

-- 编译对象
ALTER MATERIALIZED VIEW LOGPOE.XXX COMPILE;
```

### 应用日志
```bash
# 搜索错误
grep -i "ORA-\|error\|exception" app.out.log | tail -20

# 搜索特定接口
grep -i "excel-product\|FACT_V_WH" app.out.log
```

### API 测试
```bash
# 测试下载接口
curl -k -o /tmp/test.xls "https://wx-lom-app06.apac.bosch.com:9080/api/excel-product"

# 检查文件内容
file /tmp/test.xls
strings /tmp/test.xls | head -20
```
