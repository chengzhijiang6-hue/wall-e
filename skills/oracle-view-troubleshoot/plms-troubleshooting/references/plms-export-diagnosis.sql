-- PLMS Export 504 超时 - 数据库诊断脚本
-- 用途: 诊断 export API 超时的根因（表大小、索引、执行计划、数据分布）
-- 在 SQL Developer 中按 F5 执行全部，复制"脚本输出"返回

SET PAGESIZE 50000
SET LINESIZE 32767
SET TRIMSPOOL ON
SET LONG 32767
SET LONGCHUNKSIZE 32767
SET FEEDBACK OFF
SET HEADING ON

-- [1] 表行数统计
PROMPT ====== [1] 表行数统计 ======
SELECT 'LTAP_LTAK_POE' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM LTAP_LTAK_POE
UNION ALL SELECT 'LTAP_LTAK_POE_GI_TO', COUNT(*) FROM LTAP_LTAK_POE_GI_TO
UNION ALL SELECT 'MSEG_POE', COUNT(*) FROM MSEG_POE
UNION ALL SELECT 'LTAP_LTAK_POE_OPEN_TO', COUNT(*) FROM LTAP_LTAK_POE_OPEN_TO;

-- [2] LTAP_LTAK_POE 索引信息
PROMPT ====== [2] LTAP_LTAK_POE 索引信息 ======
SELECT index_name, uniqueness, column_name, column_position
FROM user_ind_columns WHERE table_name = 'LTAP_LTAK_POE'
ORDER BY index_name, column_position;

-- [3] MSEG_POE 索引信息
PROMPT ====== [3] MSEG_POE 索引信息 ======
SELECT index_name, uniqueness, column_name, column_position
FROM user_ind_columns WHERE table_name = 'MSEG_POE'
ORDER BY index_name, column_position;

-- [4] 分区信息
PROMPT ====== [4] LTAP_LTAK_POE 分区信息 ======
SELECT partition_name, high_value, num_rows, last_analyzed
FROM user_tab_partitions WHERE table_name = 'LTAP_LTAK_POE'
ORDER BY partition_position;

-- [5] 列统计信息
PROMPT ====== [5] LTAP_LTAK_POE 列统计 ======
SELECT column_name, data_type, num_distinct, num_nulls, last_analyzed
FROM user_tab_col_statistics
WHERE table_name = 'LTAP_LTAK_POE'
AND column_name IN ('BDATU', 'VLTYP', 'NLTYP', 'LGNUM', 'BWART', 'WERKS')
ORDER BY column_name;

-- [6] BDATU 按月分布
PROMPT ====== [6] LTAP_LTAK_POE BDATU 分布 ======
SELECT SUBSTR(BDATU, 1, 6) AS YEAR_MONTH, COUNT(*) AS ROW_COUNT
FROM LTAP_LTAK_POE GROUP BY SUBSTR(BDATU, 1, 6)
ORDER BY YEAR_MONTH DESC FETCH FIRST 20 ROWS ONLY;

-- [7] VLTYP 分布 (源存储类型 TOP 20)
PROMPT ====== [7] LTAP_LTAK_POE VLTYP 分布 ======
SELECT VLTYP, COUNT(*) AS ROW_COUNT FROM LTAP_LTAK_POE
GROUP BY VLTYP ORDER BY ROW_COUNT DESC FETCH FIRST 20 ROWS ONLY;

-- [8] NLTYP 分布 (目标存储类型 TOP 20)
PROMPT ====== [8] LTAP_LTAK_POE NLTYP 分布 ======
SELECT NLTYP, COUNT(*) AS ROW_COUNT FROM LTAP_LTAK_POE
GROUP BY NLTYP ORDER BY ROW_COUNT DESC FETCH FIRST 20 ROWS ONLY;

-- [9] LOI_V_LTAP_EXPORT 视图定义
PROMPT ====== [9] LOI_V_LTAP_EXPORT 视图定义 ======
SELECT DBMS_METADATA.GET_DDL('VIEW', 'LOI_V_LTAP_EXPORT', USER) AS VIEW_DDL FROM DUAL;

-- [10] LOI_V_MSEG_EXPORT 视图定义
PROMPT ====== [10] LOI_V_MSEG_EXPORT 视图定义 ======
SELECT DBMS_METADATA.GET_DDL('VIEW', 'LOI_V_MSEG_EXPORT', USER) AS VIEW_DDL FROM DUAL;

-- [11] LOI_V_LTAP_EXPORT 执行计划
PROMPT ====== [11] LOI_V_LTAP_EXPORT 执行计划 ======
EXPLAIN PLAN FOR
SELECT * FROM LOI_V_LTAP_EXPORT WHERE CREATION_DATE >= TRUNC(SYSDATE, 'MM') FETCH FIRST 100 ROWS ONLY;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- [12] LOI_V_MSEG_EXPORT 执行计划
PROMPT ====== [12] LOI_V_MSEG_EXPORT 执行计划 ======
EXPLAIN PLAN FOR
SELECT * FROM LOI_V_MSEG_EXPORT WHERE CREATION_DATE >= TRUNC(SYSDATE, 'MM') FETCH FIRST 100 ROWS ONLY;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- [13] 相关物化视图状态
PROMPT ====== [13] 相关物化视图状态 ======
SELECT mview_name, staleness, compile_state, last_refresh_date
FROM user_mviews
WHERE mview_name LIKE '%LTAP%' OR mview_name LIKE '%MSEG%' OR mview_name LIKE '%EXPORT%'
ORDER BY mview_name;

-- [14] Export 相关存储过程
PROMPT ====== [14] Export 相关存储过程 ======
SELECT name, type, MAX(line) AS lines FROM user_source
WHERE UPPER(text) LIKE '%EXPORT%' OR UPPER(text) LIKE '%LTAP_EXPORT%' OR UPPER(text) LIKE '%MSEG_EXPORT%'
GROUP BY name, type ORDER BY type, name;

-- [15] 表大小 (MB)
PROMPT ====== [15] 表大小 ======
SELECT segment_name, segment_type, ROUND(bytes/1024/1024, 2) AS size_mb
FROM user_segments
WHERE segment_name IN ('LTAP_LTAK_POE', 'LTAP_LTAK_POE_GI_TO', 'MSEG_POE')
ORDER BY segment_name;

-- [16] BDATU >= '20230101' 的实际行数
PROMPT ====== [16] BDATU >= 20230101 行数 ======
SELECT COUNT(*) AS ROW_COUNT_2023_PLUS FROM LTAP_LTAK_POE WHERE BDATU >= '20230101';

-- [17] LOI_V_LTAP_EXPORT 预估行数
PROMPT ====== [17] LOI_V_LTAP_EXPORT 预估行数 ======
SELECT COUNT(*) AS ESTIMATED_ROWS FROM LOI_V_LTAP_EXPORT;

-- [18] LOI_V_LTAP_EXPORT 按月份统计
PROMPT ====== [18] LOI_V_LTAP_EXPORT 按月份统计 ======
SELECT SUBSTR(CREATION_DATE, 1, 6) AS YEAR_MONTH, COUNT(*) AS ROW_COUNT
FROM LOI_V_LTAP_EXPORT GROUP BY SUBSTR(CREATION_DATE, 1, 6)
ORDER BY YEAR_MONTH DESC FETCH FIRST 12 ROWS ONLY;

-- [19] 并行查询配置
PROMPT ====== [19] 并行查询配置 ======
SELECT name, value FROM v$parameter
WHERE name IN ('parallel_max_servers', 'parallel_min_servers', 'parallel_degree_policy');

-- [20] 内存配置
PROMPT ====== [20] 内存配置 ======
SELECT name, ROUND(value/1024/1024, 2) AS value_mb FROM v$parameter
WHERE name IN ('pga_aggregate_target', 'sga_target', 'sga_max_size');
