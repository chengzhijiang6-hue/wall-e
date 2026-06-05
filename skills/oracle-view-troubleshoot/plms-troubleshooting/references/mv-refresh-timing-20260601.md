# PLMS 物化视图刷新耗时 (2026-06-01 实测数据)

## CB$CUBE 物化视图刷新耗时

| 物化视图 | 大小 (MB) | 刷新耗时 (分钟) | 刷新模式 | 状态 |
|----------|-----------|-----------------|----------|------|
| CB$CUBE_LTAP_LTAK_POE | 4,517 | 58.63 | FORCE/DEMAND (每小时) | NEEDS_COMPILE |
| CB$CUBE_MSEG | 1,558 | 55.48 | COMPLETE/DEMAND | NEEDS_COMPILE |
| CB$CUBE_TARGET | 446 | 56.00 | COMPLETE/DEMAND | FRESH |
| CB$CUBE_WORKHOUR | 10 | 56.85 | COMPLETE/DEMAND | NEEDS_COMPILE |
| CB$CUBE_AGR | - | 55.72 | - | NEEDS_COMPILE |
| CB$CUBE_WH_PRODUCT | - | 55.58 | - | STALE |
| CB$CUBE_PRODUCT | - | 55.50 | - | FRESH |
| CB$CUBE_AWT | - | 32.95 | - | UNKNOWN |
| CB$CUBE_ACTUAL_STOCK | - | 36.13 | - | COMPILATION_ERROR |
| CB$CUBE_ACTUAL_BLOCK_STOCK | - | 36.18 | - | COMPILATION_ERROR |
| CB$CUBE_SUPPLIER_OTD | - | 814.05 (~13.5h) | - | NEEDS_COMPILE |
| CB$CUBE_LZT | - | 745,352.92 (~517天) | - | STALE |
| CB$CUBE_OUTPUT | - | 2,568,610.52 (~1783天) | - | STALE |

## EXPORT 物化视图

| 物化视图 | 行数 | 最后刷新 | 状态 | 可替代 |
|----------|------|----------|------|--------|
| EXPORT_LTAP | 10,522,946 | 2022-12-20 | NEEDS_COMPILE | LOI_V_LTAP_EXPORT |
| EXPORT_MSEG | - | 2023-01-09 | NEEDS_COMPILE | LOI_V_MSEG_EXPORT |

## 关键结论

1. CB$CUBE 刷新耗时普遍 55-59 分钟，每小时 COMPLETE 刷新需评估可行性
2. EXPORT_LTAP 已过期 3 年，需要手动刷新
3. CB$CUBE_LTAP_LTAK_POE 是汇总 Cube（GROUP BY + ROLLUP），不能替代 LOI_V_LTAP_EXPORT
4. EXPORT_LTAP 是明细表，可以替代 LOI_V_LTAP_EXPORT

## 物化视图日志

| 源表 | 日志表 | 日志行数 | 支持增量刷新 |
|------|--------|----------|-------------|
| FACT_LTAP_LTAK_POE | MLOG$_FACT_LTAP_LTAK_POE | 6,697,669 | YES |
| FACT_MSEG_POE | MLOG$_FACT_MSEG_POE | 477,792 | YES |
