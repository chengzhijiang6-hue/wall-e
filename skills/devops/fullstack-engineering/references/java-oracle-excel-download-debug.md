# Java Spring Boot + Oracle Excel 下载调试指南

## 典型症状
- 前端点击下载按钮，Excel 文件下载成功
- Excel 有列名（表头），但没有数据行
- 页面上图表/表格可能正常显示，也可能为空

## 调试工作流

### Step 1: 确定前端下载触发点
```javascript
// Vue.js 中常见的下载方式
// 方式1: window.open 直接下载
async exportExcel() {
  window.open(`${process.env.VUE_APP_BASE_URL}/excel-product`);
}

// 方式2: 创建隐藏 <a> 标签
const link = document.createElement('a');
link.href = exportUrl;
link.click();

// 方式3: axios 请求后处理 blob
axios.get('/api/export', { responseType: 'blob' })
```

**搜索技巧**：
- 搜索 `window.open`、`export`、`download`、`excel`
- 检查 `.env.production` 中的 `VUE_APP_BASE_URL`（通常是 `/api`）
- 检查 `vue.config.js` 中的 proxy 配置（`pathRewrite` 去掉 `/api` 前缀）

### Step 2: 追踪后端接口
```
前端: /api/excel-product
  ↓ nginx pathRewrite: ^/api → ""
后端: /excel-product
  ↓ Controller
ExcelProductController.excelProductDownload()
  ↓ DAO
NewWhProductDwDao.findAllExcel(schema)
  ↓ MyBatis SQL
SELECT * FROM ${schema}.FACT_V_WH_PRODUCT_DW
```

**关键检查点**：
- `@Value("${lom-kpi.schema}")` 注入的 schema 值
- `${schema}` 是字符串替换，不是参数绑定
- prod 环境的 schema 可能与 dev 不同

### Step 3: 验证数据库
```sql
-- 1. 检查对象类型（表还是视图）
SELECT OBJECT_NAME, OBJECT_TYPE, STATUS 
FROM ALL_OBJECTS 
WHERE OBJECT_NAME = 'FACT_V_WH_PRODUCT_DW' AND OWNER = 'LOGPOE';

-- 2. 检查数据量
SELECT COUNT(*) FROM LOGPOE.FACT_V_WH_PRODUCT_DW;

-- 3. 如果是视图，检查底层表
DESC LOGPOE.FACT_WH_PRODUCT_DW;
SELECT COUNT(*) FROM LOGPOE.FACT_WH_PRODUCT_DW;

-- 4. 检查视图依赖
SELECT REFERENCED_OWNER, REFERENCED_NAME, REFERENCED_TYPE 
FROM ALL_DEPENDENCIES 
WHERE NAME = 'FACT_V_WH_PRODUCT_DW' AND OWNER = 'LOGPOE';
```

### Step 4: 检查应用日志
```bash
# 搜索 Oracle 错误
grep -i "ORA-\|error\|exception" app.out.log | tail -30

# 搜索特定接口
grep -i "excel-product\|FACT_V_WH" app.out.log

# 搜索视图相关错误
grep -i "table or view does not exist\|ORA-00942" app.out.log
```

## 常见根因

### 根因1: Oracle 视图 INVALID
**表现**：手动查询视图有数据，但应用查询返回空
**原因**：底层表结构变化导致视图失效，Oracle 在直接查询时自动重编译，但应用连接池可能缓存了错误状态
**修复**：`ALTER VIEW VIEW_NAME COMPILE;` 或重启应用

### 根因2: ETL 依赖表为空
**表现**：表/视图存在，状态 VALID，但 `SELECT COUNT(*)` 返回 0
**原因**：数据由外部 ETL 任务加载，任务未运行或失败
**排查**：
```sql
-- 检查表是否有 INSERT 权限的用户
SELECT GRANTEE, PRIVILEGE FROM ALL_TAB_PRIVS WHERE TABLE_NAME = 'TABLE_NAME';

-- 检查是否有物化视图日志
SELECT * FROM ALL_MVIEW_LOGS WHERE MASTER = 'TABLE_NAME';
```

### 根因3: 前端下载依赖页面数据
**表现**：下载接口本身有数据，但 Excel 为空
**原因**：前端下载逻辑使用了页面已加载的数据（如 `/wh-overview` 接口），而非下载接口的数据
**排查**：检查前端下载函数是否使用了 `this.tableData` 或 `this.whOverviewList` 等页面状态

### 根因4: nginx upstream timeout
**表现**：nginx 日志显示 `upstream timed out`
**原因**：Java 应用无响应（崩溃、连接池耗尽、数据库连接超时）
**排查**：
```bash
# 检查 Java 进程
netstat -ano | findstr :9071
tasklist | findstr java

# 检查连接池状态
grep -i "HikariPool\|connection" app.out.log | tail -10
```

## API 测试技巧（WSL 环境）

当浏览器无法访问内网地址时，用 `curl` 测试 API：

```bash
# 测试下载接口（-k 忽略证书错误）
curl -k -o /tmp/test.xls "https://wx-lom-app06.apac.bosch.com:9080/api/excel-product"

# 检查文件类型
file /tmp/test.xls

# 检查文件内容（提取文本）
strings /tmp/test.xls | head -20

# 检查是否有数据行（搜索日期格式）
strings /tmp/test.xls | grep -E "^[0-9]{8}" | head -5

# 测试 JSON API（可能需要 token）
curl -k "https://wx-lom-app06.apac.bosch.com:9080/api/wh-overview"
```

## LOM Dashboard 项目结构参考

```
后端 (lom-dashboard-serve-master-develop/)
├── src/main/java/com/touchspring/lomkpi/
│   ├── controller/          # REST 接口
│   ├── dao/                 # MyBatis DAO 接口
│   ├── domain/entity/       # 实体类
│   ├── service/             # 业务逻辑
│   ├── task/                # 定时任务
│   └── utils/               # 工具类（ExcelUtil 等）
├── src/main/resources/
│   ├── application-dev.yml  # dev 配置
│   ├── application-prod.yml # prod 配置
│   └── mapper/              # MyBatis XML
└── libs/                    # 本地 JAR 依赖

前端 (source code/)
├── src/
│   ├── views/WareHouseNew/  # 仓库相关页面
│   ├── api/                 # API 接口定义
│   └── components/          # 公共组件
├── .env.production          # 生产环境变量
└── vue.config.js            # 代理配置

数据库 (Oracle)
├── LOGPOE schema            # 开发环境
├── logpoe schema            # prod 环境（配置文件中）
└── 关键表/视图:
    ├── FACT_V_WH_PRODUCT_DW # 仓库产品数据（视图）
    ├── FACT_WH_PRODUCT_DW   # 仓库产品基础表
    ├── LOI_V_WH_OVERVIEW    # 仓库概览（表，ETL 依赖）
    └── LOI_V_WH_PRODUCT     # 仓库产品视图
```
