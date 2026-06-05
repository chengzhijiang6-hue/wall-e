# Oracle 视图问题诊断手册

## 常见错误码

### ORA-00909: invalid number of arguments
- **原因**：函数参数数量不对
- **常见场景**：CASE WHEN 语句类型不匹配、视图引用的表结构变化
- **触发条件**：底层表列类型变更导致视图中的类型转换失败
- **症状**：查询视图时报错，但视图状态可能是 VALID

### ORA-00942: table or view does not exist
- **原因**：视图不存在或用户无权限访问
- **常见场景**：视图被删除、权限未授予、schema 不正确
- **症状**：查询直接报错，不是返回空数据

### ORA-00001: unique constraint violated
- **原因**：违反唯一约束
- **常见场景**：重复插入数据
- **与视图无关**，但可能出现在同一日志中

## 诊断步骤

### 1. 检查视图状态
```sql
SELECT OBJECT_NAME, OBJECT_TYPE, STATUS 
FROM ALL_OBJECTS 
WHERE OBJECT_NAME = 'VIEW_NAME' AND OWNER = 'SCHEMA_NAME';
```
- VALID: 视图正常
- INVALID: 视图需要重新编译

### 2. 测试视图能否查询
```sql
SELECT * FROM SCHEMA_NAME.VIEW_NAME WHERE ROWNUM <= 1;
```
- 如果返回数据：视图已自动重编译（如果之前是 INVALID）
- 如果报错 ORA-00909：视图定义有问题
- 如果报错 ORA-00942：视图不存在或无权限

### 3. 检查底层表
```sql
-- 表是否存在及数据量
SELECT COUNT(*) FROM SCHEMA_NAME.BASE_TABLE;

-- 表结构
DESC SCHEMA_NAME.BASE_TABLE;

-- 对象状态
SELECT OBJECT_NAME, STATUS 
FROM ALL_OBJECTS 
WHERE OBJECT_NAME = 'BASE_TABLE' AND OWNER = 'SCHEMA_NAME';
```

### 4. 检查权限
```sql
-- 检查授予的权限
SELECT GRANTEE, PRIVILEGE 
FROM ALL_TAB_PRIVS 
WHERE TABLE_NAME = 'VIEW_NAME';

-- 检查视图定义
SELECT TEXT 
FROM ALL_VIEWS 
WHERE VIEW_NAME = 'VIEW_NAME' AND OWNER = 'SCHEMA_NAME';
```

## Java 应用行为

### MyBatis 查询视图时的行为
1. 视图 VALID 且有数据：正常返回列表
2. 视图 INVALID：抛出 SQL 异常，Controller 捕获后返回空列表
3. 视图不存在（ORA-00942）：抛出 SQL 异常，nginx 超时

### Excel 下载只有列名的根因链
```
前端 window.open('/api/excel-xxx')
  → Controller 调用 DAO.findAllExcel(schema)
    → MyBatis 执行 SQL 查询视图
      → 视图 INVALID 或不存在
        → 抛出异常或返回空列表
          → Excel 只写入表头行
```

## 修复方法

### 方法1：手动触发重编译
```sql
ALTER VIEW SCHEMA_NAME.VIEW_NAME COMPILE;
```

### 方法2：重建视图
```sql
CREATE OR REPLACE VIEW SCHEMA_NAME.VIEW_NAME AS ...;
```

### 方法3：查询触发自动重编译
```sql
SELECT * FROM SCHEMA_NAME.VIEW_NAME WHERE ROWNUM <= 1;
```

### 方法4：重启 Java 应用
清除应用缓存和连接池中的旧状态。

## 预防措施

### 定期检查 INVALID 对象
```sql
SELECT OBJECT_NAME, OBJECT_TYPE, STATUS 
FROM ALL_OBJECTS 
WHERE STATUS = 'INVALID' AND OWNER = 'SCHEMA_NAME';
```

### 在 Java 代码中添加日志
```java
// 在 Controller 中捕获异常并记录日志
try {
    List<Data> data = dao.findAll(schema);
} catch (Exception e) {
    log.error("查询失败: schema={}, error={}", schema, e.getMessage());
    throw e;
}
```

### 视图定义中添加 FORCE 关键字
```sql
CREATE OR REPLACE FORCE EDITIONABLE VIEW ...
```
- FORCE: 即使基表不存在也创建视图
- EDITIONABLE: 支持版本化视图

## Nginx 层面的诊断

### upstream timed out
当 nginx 日志显示 `upstream timed out` 时：
1. Java 应用可能已崩溃
2. Java 应用监听地址不正确（IPv4 vs IPv6）
3. 数据库连接池耗尽

### 排查步骤
```powershell
# 检查端口监听
netstat -ano | findstr :9071

# 检查 Java 进程
tasklist | findstr java

# 检查应用日志
Get-Content -Path "D:\lom\logs\*.out.log" -Tail 50
```
