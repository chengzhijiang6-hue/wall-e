# PLMS / LOM-KPI 项目结构参考

## 项目概况
- 名称: LOM-KPI (Logistics Operations Management KPI Dashboard)
- 地址: https://wx-lom-app06.apac.bosch.com:9080
- 类型: 前后端合体单体应用 (Vue SPA + Spring Boot)

## 前端 (source code/)
- 框架: Vue 2.6 + Vue Router 3 + Vuex 3 + Element UI 2.12
- 构建: Vue CLI 3, history 模式
- 图表: ECharts 5, AntV G2/G6, Leaflet 地图
- API调用: `fetch({url, method})` from `src/utils/fetch.js`, Azure SSO token
- API文件: `src/api/*.js` (112个), 用 `VUE_APP_BASE_URL` (即 `/api`)
- 路由: `src/router.js` (76个路由)
- 组件: `src/views/*.vue` (394个有API导入)

## 后端 (lom-dashboard-serve-master-develop/)
- 框架: Spring Boot 2.5.5 + MyBatis 2.0.1 + Java 8
- 包路径: `com.touchspring.lomkpi`
- Controller: 232个, 大多直接注入 Mapper (不经 Service)
- DAO: `src/main/java/.../dao/`
- Mapper XML: `src/main/resources/mapper/` (213个, 1306个SQL方法)
- 数据库: Oracle, schema via `@Value("${lom-kpi.schema}")`
- 表空间: RBCDLOG
- 认证: Azure AD SSO + Jasypt 加密

## 关键目录
```
前端:
  src/api/          - API服务文件 (112个)
  src/views/        - Vue页面组件
  src/router.js     - 路由定义
  src/utils/fetch.js - HTTP请求封装

后端:
  controller/       - 232个Controller
  dao/              - DAO接口 (对应Mapper XML)
  service/          - Service层 (少数Controller使用)
  domain/entity/    - 实体类
  resources/mapper/ - 213个MyBatis XML
```

## 表命名规则
- `LOI_` 前缀: LOI系统表/视图 (最多)
- `LOM_` 前缀: LOM系统表
- `U_` 前缀: 用户配置/目标表
- `GR_` 前缀: 收货相关
- `DK_` 前缀: 月台相关
- `SAP_` 前缀: SAP同步数据
- `V_` 前缀: 视图
- `AKA_` 前缀: IES系统数据

## 生成的映射文件
- `PLMS映射表.txt` - 完整版 (API→Controller→表, 772行)
- `PLMS数据库快速查找表.txt` - 精简版 (按模块查表, 546行)
- `PLMS逐页面精确映射.txt` - 逐页版 (页面→API函数, 637行)
- `PLMS完整调用链.txt` - 含SQL版 (页面→API→Controller→SQL, 1281行)
- `PLMS视图基表依赖.txt` - 视图展开 (视图→基表依赖)

## 数据库对象统计 (LOGPOE schema)
- 基表: 1428
- 视图: 782
- 物化视图: 64
- PLMS引用: 294 对象 (160 基表 + 61 视图 + 17 MV)
- 视图展开后最终基表: 295

## 知识库产出文件
- `/mnt/c/Users/CZE8WX/Desktop/knowledge/PLMS数据来源映射_完整版.md` — 37KB，含子功能+附录（API/Controller/视图全量映射）
- `/mnt/c/Users/CZE8WX/Desktop/knowledge/PLMS操作手册_数据来源.md` — 12KB，整合代码分析+PDF手册+图片分析的中英对照版
- `/mnt/c/Users/CZE8WX/Desktop/knowledge/PLMS数据来源映射.md` — 初版（仅主页面级别）

## PDF 操作手册
- 来源: Docupedia 导出 (Physical Logistics Management System _ LOM Dashboard)
- 作者: CHENG Zhijiang (RBCD/LOI), 2026-05-27
- 页数: 147, 覆盖全部模块
- 已转为图片: `/mnt/c/Users/CZE8WX/Desktop/pdf_pages/page_*.png`
- 全量文字: `/mnt/c/Users/CZE8WX/Desktop/pdf_pages/all_text.txt` (267KB)
- PDF 中发现 87 张表/视图，含完整 SQL 查询和业务逻辑
