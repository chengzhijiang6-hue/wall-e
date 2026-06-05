# Java Maven 项目 SQL 脚本分析方法论

## 适用场景
当需要分析 Java 项目中的 SQL 脚本以了解数据库表结构时使用。典型路径：`项目根目录/libs/*.sql`

## 工作流程

### 1. 定位 SQL 文件
```bash
# 列出所有 SQL 文件
find /path/to/project/libs -name "*.sql" -type f | sort

# 统计数量
find /path/to/project/libs -name "*.sql" | wc -l
```

### 2. 批量提取表名
使用正则表达式从 CREATE TABLE 语句中提取表名：
```python
import re

# 匹配 CREATE TABLE 语句
create_match = re.search(r'CREATE\s+TABLE\s+(\w+)', sql_content, re.IGNORECASE)
if create_match:
    table_name = create_match.group(1)
```

### 3. 提取字段定义
```python
# 找到 CREATE TABLE 语句中的字段定义块
create_block = re.search(r'CREATE\s+TABLE.*?\((.*?)\)', content, re.IGNORECASE | re.DOTALL)
if create_block:
    fields_text = create_block.group(1)
    # 按行解析字段
    for line in fields_text.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            # 解析字段名和类型
            pass
```

### 4. 识别关键信息
- **主键**: PRIMARY KEY 约束或约定俗成的 ID 字段
- **审计字段**: CREATE_TIME, UPDATE_TIME, CREATE_BY, UPDATE_BY
- **业务字段**: 根据字段名和注释判断业务含义
- **COMMENT**: Oracle 使用 `COMMENT ON COLUMN` 语法添加字段注释

### 5. 分析索引
```sql
-- 索引定义格式
CREATE INDEX index_name ON table_name (column1, column2);
CREATE UNIQUE INDEX index_name ON table_name (column ASC);
```

### 6. 识别视图
视图通常以 `V_` 或 `VIEW` 开头，使用 SELECT 语句定义。

## Oracle SQL 特征
- 表空间: `TABLESPACE xxx`
- 存储参数: `STORAGE (INITIAL 65536 NEXT 1048576 ...)`
- 字段类型: `VARCHAR2`, `NVARCHAR2`, `NUMBER`, `TIMESTAMP(6)`, `DATE`
- 注释: `COMMENT ON COLUMN table.column IS 'xxx'`

## 报告输出格式
建议按业务模块分组，每张表包含：
1. 表名和中文说明
2. 字段列表（字段名、类型、说明）
3. 主键和索引
4. 关联关系（基于外键或业务逻辑推测）

## 示例：pom.xml 依赖分析
从 pom.xml 可识别：
- 数据库类型: mysql-connector-java (MySQL), ojdbc7 (Oracle), mssql-jdbc (SQL Server)
- ORM 框架: mybatis-spring-boot-starter
- 连接池: HikariCP
- 分页插件: pagehelper-spring-boot-starter

## 注意事项
- SQL 文件可能包含多个表定义（如 DICT.sql 包含 LOM_SYS_DICT 和 LOM_SYS_DICT_ITEM）
- ALTER TABLE 语句表示后续添加的字段
- 系统作用域依赖（system scope）的 JAR 文件需要在 libs 目录中存在
- 视图定义中的 JOIN 关联可帮助理解表间关系
