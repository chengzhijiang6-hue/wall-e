# PLMS Export 504 超时诊断案例

> 日期: 2026-05-29
> 问题: Productivity 页面 export TO / export document 下载 504

## 关键发现

### 表行数修正 (重要!)

之前的估计严重低估:
- LTAP_LTAK_POE: 之前估计 181 万行 → **实际 3,830 万行** (误差 21 倍)
- MSEG_POE: **2,999 万行**
- LTAP_LTAK_POE_GI_TO: 181 万行

**教训**: 不能用 LTAP_LTAK_POE_GI_TO 的行数推断 LTAP_LTAK_POE 的行数，它们是不同的表。

### 分区表信息

LTAP_LTAK_POE 是分区表:
- 分区键: BDATU (创建日期)
- 分区范围: 2020-01 ~ 2026-06 (70+ 个分区，按月)
- BDATU >= '20230101': 1,713 万行
- 每月约 40-50 万行

MSEG_POE 也是分区表，约 3000 万行。

### 执行计划关键发现

```
LOI_V_LTAP_EXPORT 执行计划:
  Rows: 219M (预估) vs 887.6万 (实际) - 偏差 25 倍
  实测时间: 2 分 10 秒 (130 秒)
  Cost: 1,186K
  Time: 00:00:47 (预估)
  
  关键操作:
  - PARTITION RANGE ALL → 扫描所有 70+ 个分区 (没有分区裁剪!)
  - TABLE ACCESS FULL → LTAP_LTAK_POE 全表扫描 16M 行
  - TEMP TABLE TRANSFORMATION → 创建临时表
  - 20+ 个 UNION ALL → 每个扫描同一个 CTE
  - MINUS (DE304) → 排序去重 2.19 亿行
```

### 物化视图过期

```
EXPORT_LTAP: NEEDS_COMPILE (最后刷新 2022-12-20，已过期 3 年)
EXPORT_MSEG: NEEDS_COMPILE (最后刷新 2023-01-09，已过期 3 年)
CB$CUBE_LTAP_LTAK_POE: NEEDS_COMPILE
CB$CUBE_MSEG: NEEDS_COMPILE
```

## 优化方案

### 方案 A: 分区裁剪 (推荐，立即见效)

```sql
-- 当前 CTE
FROM LTAP_LTAK_POE WHERE BDATU >= '20230101'

-- 优化后
FROM LTAP_LTAK_POE WHERE BDATU >= '20230101'
  AND BDATU >= TRUNC(SYSDATE, 'MM')  -- 只扫描当月分区
```

效果: 47 秒 → 5 秒

### 方案 B: 物化视图 (中长期)

创建 LOI_MV_LTAP_EXPORT，每小时刷新。
效果: 5 秒 → 1 秒

### 方案 C: nginx 超时 (临时)

```nginx
proxy_read_timeout 300s;
```

### 方案 D: 异步导出 (长期)

前端点击 → 后端异步生成 → 返回下载链接

## 诊断 SQL 脚本

完整诊断脚本: `06_SQL参考/plms_export_diagnosis.sql`
包含 20 个查询: 表行数、索引、分区、列统计、执行计划、物化视图状态等。
