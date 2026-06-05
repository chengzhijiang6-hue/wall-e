# SQL Developer 导出文件格式参考

## 格式 1: USER_SOURCE（存储过程/函数源码）

```
NAME\tLINE_NUM\t"SOURCE_CODE\r\n
```

- 每行一个源码行
- 行号递增
- 源码用双引号包裹
- CRLF 换行
- 文件末尾可能有 ORA- 错误行（跳过）
- Section header 如 `1.` `2.` 是查询分段标记（跳过）

**解析正则**: `^(\w+)\t(\d+)\t"(.*)$`

## 格式 2: USER_VIEWS（视图定义）

```
VIEW_NAME\t"SQL_DEFINITION\r\n
```

- 每个视图一个条目
- SQL 跨多行，用双引号包裹
- 可能为空（查询未返回数据）

**解析正则**: `^(\w+)\t"(.+)$`

## 格式 3: USER_TAB_COLUMNS（表结构）

```
TABLE_NAME\tCOLUMN_NAME\tDATA_TYPE\tDATA_LENGTH\tNULLABLE
```

- Tab 分隔
- 每行一列

## 格式 4: 行数统计

```
TABLE_NAME\tROW_COUNT
```

- Tab 分隔
- 来自 `SELECT table_name, COUNT(*) FROM table_name` 的结果

## 混合导出文件

一个文件可能包含多个 Section，用数字+点分隔：
```
1.
[USER_SOURCE 数据]
2.
[USER_VIEWS 数据]
3.
[USER_TAB_COLUMNS 数据]
4.
[行数统计]
5.
[USER_MVIEWS 数据]
```

## 解析脚本

已保存: `/mnt/c/Users/CZE8WX/Desktop/knowledge/PLMS数据梳理/scripts/update_plms_kb.py`
