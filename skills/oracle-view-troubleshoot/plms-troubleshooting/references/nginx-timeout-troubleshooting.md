# nginx 504 超时排查指南

## 问题模式

```
症状: 页面下载按钮点击后 504 Gateway Timeout
典型 API: /api/excel-new-product-lv1-to, /api/excel-new-product-lv1-document
```

## 数据流分析

```
前端按钮
   ↓
nginx(9080) ←── 默认 60 秒超时 ←── 直接原因
   ↓
Java(9071) ←── 同步等待 Excel 生成
   ↓
ExportToMapper
   ↓
LOI_V_LTAP_EXPORT ←── 普通视图，每次重新查询 ←── 根因
   ↓
LTAP_LTAK_POE (181万行) ←── 全表扫描 ←── 深层根因
```

## 时间估算模型

```
假设:
  - LTAP_LTAK_POE 表扫描: 30-60 秒 (181万行，无索引)
  - 20+ 个 UNION ALL: 30-60 秒 (多次扫描 CTE)
  - Java Excel 生成: 10-20 秒 (内存中生成)
  - 网络传输: 5-10 秒

总计: 75-150 秒

nginx 默认超时: 60 秒
实际需要时间: 75-150 秒
结果: 504 Gateway Timeout
```

## Windows CMD 排查命令

### 第 1 步：查看 nginx 超时配置

```cmd
type D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf | findstr /i "timeout"
```

预期：看到 `ssl_session_timeout` 但没有 `proxy_read_timeout` = 使用默认 60 秒

### 第 2 步：查看 nginx 代理目标

```cmd
type D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf | findstr /i "proxy_pass"
```

预期：看到 `proxy_pass http://localhost:9071/` = Java 应用端口

### 第 3 步：搜索 Java 日志中的 export 错误

```cmd
findstr /i /n "excel-new-product" D:\lom\lom-dashboard-serve-1.0-RELEASE\logs\lom-dashboard-serve-1.0-RELEASE.out.log
```

如果无结果，扩大搜索范围：

```cmd
findstr /i /n "export\|timeout\|504" D:\lom\lom-dashboard-serve-1.0-RELEASE\logs\lom-dashboard-serve-1.0-RELEASE.out.log | findstr /i "excel\|product\|lv1"
```

### 第 4 步：确认 Java 应用是否在运行

```cmd
netstat -ano | findstr "9071"
```

预期：看到 LISTENING 状态

### 第 5 步：直连 Java 端口测试（绕过 nginx）

```cmd
curl -k -o NUL -s -w "HTTP Code: %%{http_code}, Time: %%{time_total}\n" "https://127.0.0.1:9071/api/excel-new-product-lv1-to?creationDate=202605"
```

如果 9071 不支持 HTTPS，试 HTTP：

```cmd
curl -o NUL -s -w "HTTP Code: %%{http_code}, Time: %%{time_total}\n" "http://127.0.0.1:9071/api/excel-new-product-lv1-to?creationDate=202605"
```

### 第 6 步：查看完整 nginx 配置

```cmd
type D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf
```

确认 location /api/ 块是否有超时配置。

## 修复方案

### 方案 A：修改 nginx 超时配置（推荐，最快）

**步骤 1：备份配置文件**

```cmd
copy D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf.bak
```

**步骤 2：修改配置文件**

用记事本打开：

```cmd
notepad D:\nginx-1.24.0\conf\app-conf\lom-dashboard.conf
```

找到 `location /api/` 块：

```nginx
        location /api/ {
            proxy_pass  http://localhost:9071/;
        }
```

替换为：

```nginx
        location /api/ {
            proxy_pass  http://localhost:9071/;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
            proxy_send_timeout 300s;
        }
```

**步骤 3：测试配置语法**

```cmd
D:\nginx-1.24.0\nginx.exe -t
```

预期：`syntax is ok` 和 `test is successful`

**步骤 4：重新加载配置（不中断服务）**

```cmd
D:\nginx-1.24.0\nginx.exe -s reload
```

**步骤 5：验证修复**

浏览器访问 PLMS 页面，测试 export TO / export document 下载。

### 方案 B：SQL 优化（中期）

将 LOI_V_LTAP_EXPORT 改为物化视图，或优化 SQL 添加日期过滤下推。

### 方案 C：异步导出（长期）

前端点击 → 后端生成任务 → 异步生成 Excel → 返回下载链接。

## Pitfalls

1. **Windows cmd 中 curl 的 `%{time_total}` 需要写成 `%%{time_total}`**（双百分号）
2. **nginx 配置在 app-conf 子目录**（lom-dashboard.conf），不在主 nginx.conf 中
3. **Java 应用日志文件名含版本号**（lom-dashboard-serve-1.0-RELEASE.out.log）
4. **curl 计时在 Windows cmd 中可能不生效**：某些 curl 版本或 cmd 配置下，`%%{time_total}` 不会被解析。此时只能通过其他方式判断超时。
5. **nginx -s reload 不会中断现有连接**：正在处理的请求会继续完成，新请求使用新配置。
