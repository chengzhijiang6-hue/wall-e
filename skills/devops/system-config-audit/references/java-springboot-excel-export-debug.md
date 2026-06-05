# Java Spring Boot Excel 导出调试方法论

## 适用场景
用户报告：前端下载按钮可以导出 Excel，有列名（表头），但没有数据行。

## 调试流程

### Phase 1: 定位导出接口
```bash
# 搜索 Controller 中的导出相关注解
grep -rn "export\|download\|excel" src/main/java/**/controller/ --include="*.java"

# 搜索 Excel 工具类
grep -rn "ExcelUtil\|exportExcel\|EasyPOI" src/main/java/ --include="*.java"
```

常见导出接口模式：
- `@RequestMapping("/excel-xxx")` + `HttpServletResponse` 参数
- `@GetMapping("/export-xxx-download")`
- 使用 `ExcelUtil.exportExcel()` 或 `EasyPOI` 注解

### Phase 2: 检查 Controller 导出逻辑
典型代码结构：
```java
@RequestMapping("/excel-product")
public void excelProductDownload(HttpServletResponse response) {
    // 1. 构建表头
    List<List<String>> excelData = new ArrayList<>();
    List<String> head = new ArrayList<>();
    head.add("列名1");
    head.add("列名2");
    excelData.add(head);
    
    // 2. 查询数据 ← 问题通常在这里
    List<Entity> data = dao.findAll(schema);
    
    // 3. 填充数据行
    for (Entity item : data) {
        List<String> row = new ArrayList<>();
        row.add(item.getField1());
        excelData.add(row);
    }
    
    // 4. 导出
    ExcelUtil.exportExcel(response, excelData, sheetName, fileName, 15);
}
```

### Phase 3: 检查 DAO/Mapper 查询
```bash
# 定位 DAO 接口
find src/main/java -name "*Dao.java" -o -name "*Mapper.java" | xargs grep -l "findAll\|selectAll\|queryList"

# 检查对应的 Mapper XML
find src/main/resources/mapper -name "*.xml" | xargs grep -l "findAll\|selectAll"
```

关键检查点：
1. **SQL 查询是否正确** - SELECT 语句是否能返回数据
2. **schema 参数** - 是否传入了正确的 schema/用户名
3. **表名前缀** - Oracle 中可能是 `SCHEMA.TABLE_NAME` 格式

### Phase 4: 检查数据库配置
```yaml
# application-dev.yml 或 application-prod.yml
spring:
  datasource:
    jdbc-url: jdbc:oracle:thin:@//host:port/service
    username: LOM_PDCA
    password: xxx

lom-kpi:
  schema: LOM_PDCA  # ← 这个 schema 会被传入 DAO 查询
```

### Phase 5: 验证数据存在性
```sql
-- 连接数据库验证表中是否有数据
SELECT COUNT(*) FROM LOM_PDCA.TABLE_NAME;

-- 检查最近数据
SELECT * FROM LOM_PDCA.TABLE_NAME WHERE ROWNUM <= 10;
```

## 常见原因

| 原因 | 症状 | 解决方案 |
|------|------|----------|
| 数据库无数据 | SELECT 返回空 | 检查数据源、定时任务是否正常运行 |
| Schema 错误 | 查询了错误的 schema | 检查 `lom-kpi.schema` 配置 |
| 权限不足 | ORA-00942 表不存在 | 检查数据库用户权限 |
| SQL 查询错误 | Mapper XML 中 SQL 有误 | 检查 SQL 语法和表名 |
| 数据库连接失败 | 连接超时或拒绝 | 检查网络和数据库状态 |
| 日期过滤条件 | 数据被过滤掉了 | 检查 Controller 中的查询参数 |

## 调试检查清单
1. [ ] 找到导出接口的 Controller 代码
2. [ ] 找到对应的 DAO 接口和 Mapper XML
3. [ ] 检查 SQL 查询是否正确
4. [ ] 验证 schema 配置是否正确
5. [ ] 连接数据库验证表中是否有数据
6. [ ] 检查 Controller 中是否有过滤条件（日期、状态等）
7. [ ] 检查数据库用户权限

## 相关文件位置
- Controller: `src/main/java/**/controller/*Controller.java`
- DAO: `src/main/java/**/dao/*Dao.java`
- Mapper: `src/main/resources/mapper/*.xml`
- 配置: `src/main/resources/application-*.yml`
- 工具类: `src/main/java/**/utils/ExcelUtil.java`
