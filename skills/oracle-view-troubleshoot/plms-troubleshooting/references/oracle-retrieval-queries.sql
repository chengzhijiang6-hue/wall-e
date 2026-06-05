-- PLMS 排错知识库 - Oracle 检索脚本
-- 执行环境: Oracle (LOGPOE 用户)
-- 使用方法: SQL Developer 中按 F5 执行全部，导出结果为文件

SET PAGESIZE 50000
SET LINESIZE 32767
SET TRIMSPOOL ON
SET LONG 32767
SET LONGCHUNKSIZE 32767
SET FEEDBACK OFF

-- [1] 物化视图状态（最重要！先返回这个）
SELECT mview_name, TO_CHAR(last_refresh_date,'YYYY-MM-DD HH24:MI:SS') AS last_refresh, staleness, compile_state FROM user_mviews ORDER BY mview_name;

-- [2] 物化视图定义（用 DBMS_METADATA 绕过 LONG 限制）
SELECT mview_name, DBMS_METADATA.GET_DDL('MATERIALIZED_VIEW', mview_name, USER) AS mv_ddl FROM user_mviews WHERE mview_name LIKE 'LOI%' ORDER BY mview_name;

-- [3] LOI 视图定义（用 DBMS_METADATA）
SELECT view_name, DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS view_ddl FROM user_views WHERE view_name LIKE 'LOI%' ORDER BY view_name;

-- [4] 所有视图列表（不含 LONG 列）
SELECT view_name FROM user_views ORDER BY view_name;

-- [5] 存储过程/函数列表
SELECT DISTINCT name, type, MAX(line) AS lines FROM user_source WHERE type IN ('PROCEDURE','FUNCTION','PACKAGE','PACKAGE BODY') GROUP BY name, type ORDER BY type, name;

-- [6] 失效物化视图定义
SELECT mview_name, DBMS_METADATA.GET_DDL('MATERIALIZED_VIEW', mview_name, USER) AS mv_ddl FROM user_mviews WHERE compile_state = 'COMPILATION_ERROR' ORDER BY mview_name;

-- [7] 失效物化视图依赖关系
SELECT d.name AS mview_name, d.referenced_name, d.referenced_type FROM user_dependencies d WHERE d.name IN (SELECT mview_name FROM user_mviews WHERE compile_state = 'COMPILATION_ERROR') ORDER BY d.name, d.referenced_name;

-- [8] 触发器列表
SELECT trigger_name, table_name, trigger_type, triggering_event, status FROM user_triggers ORDER BY trigger_name;

-- [9] 同义词
SELECT synonym_name, table_owner, table_name FROM user_synonyms ORDER BY synonym_name;
