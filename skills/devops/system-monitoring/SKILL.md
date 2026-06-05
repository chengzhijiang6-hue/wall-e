---
name: system-monitoring
description: 系统资源定时监控，支持跳过周末/法定节假日、截止日期自动停止，解决 WSL 环境下 Python 包依赖问题
trigger: 用户要求定时监控系统资源、设置 cron 定时任务、或需要跳过节假日的周期性检测
---

# 系统资源定时监控技能

## 适用场景
- 定时检测 WSL/服务器的 CPU、内存、磁盘使用率
- 需要跳过周末和法定节假日
- 需要设置截止日期自动停止
- 输出 JSON 格式便于后续处理

## 关键陷阱（必须注意）

### 1. Python 环境分裂
WSL 中存在两个 Python 环境：
- 系统 Python: `/usr/bin/python3` — 通常没有 pip，无法安装第三方包
- Hermes venv: `/mnt/c/wsl/hermes_official/venv/bin/python3` — 有 pip，已安装 psutil/croniter

**cron job 使用系统 Python 执行，但系统 Python 没有第三方包。**

解决方案：创建 shell 包装器，强制使用 hermes venv Python：
```bash
#!/bin/bash
/mnt/c/wsl/hermes_official/venv/bin/python3 /path/to/script.py
```

### 2. croniter 依赖
hermes 的 cronjob 工具要求系统 Python 有 croniter 包，但系统 Python 没有 pip。
**不要使用 hermes 的 cronjob 工具**，直接用 `crontab -e` 或 `echo ... | crontab -` 创建。

### 3. psutil 安装
psutil 需要安装到 hermes venv：
```bash
/mnt/c/wsl/hermes_official/venv/bin/pip install psutil
```

## 执行步骤

### 1. 创建监控脚本
脚本路径: `~/.hermes/scripts/system_monitor.py`

核心逻辑：
```python
import psutil
import json
from datetime import datetime, date

# 法定节假日列表（从政府网站提取）
HOLIDAYS_2026 = [...]  # 具体日期列表

def is_workday(d):
    if d.weekday() >= 5:  # 周末
        return False
    if d in HOLIDAYS_2026:  # 法定节假日
        return False
    return True

# 主逻辑：检查截止日期 → 检查工作日 → 输出资源
```

### 2. 创建 shell 包装器
脚本路径: `~/.hermes/scripts/system_monitor.sh`
```bash
#!/bin/bash
/mnt/c/wsl/hermes_official/venv/bin/python3 "$(dirname "$0")/system_monitor.py"
```
必须 `chmod +x`。

### 3. 安装依赖
```bash
/mnt/c/wsl/hermes_official/venv/bin/pip install psutil
```

### 4. 创建 cron 定时任务
```bash
# 周一到周五 9:00-17:00 每小时执行
echo "0 9-17 * * 1-5 /home/ethan/.hermes/scripts/system_monitor.sh" | crontab -
# 验证
crontab -l
```

### 5. 测试验证
```bash
/home/ethan/.hermes/scripts/system_monitor.sh
```
预期输出：JSON 格式的 CPU/内存/磁盘使用率。

## Cron 表达式速查
| 表达式 | 含义 |
|--------|------|
| `0 9-17 * * 1-5` | 周一至周五 9:00-17:00 每小时整点 |
| `*/30 * * * *` | 每30分钟 |
| `0 9 * * 1` | 每周一 9:00 |
| `0 0 1 * *` | 每月1日 0:00 |

## 法定节假日获取方法
1. 访问 https://www.gov.cn/zhengce/zhengceku/ 搜索当年节假日安排
2. 用 curl 提取页面内容，grep 关键词定位
3. 手动解析日期范围，展开为逐日列表
4. 注意：截止日期之后的节假日无需录入

## 输出格式
```json
{
  "timestamp": "2026-05-08 15:13:06",
  "date": "2026-05-08",
  "is_workday": true,
  "cpu": {"usage_percent": 0.9, "cores": 12},
  "memory": {"total_gb": 7.61, "used_gb": 2.39, "available_gb": 5.21, "usage_percent": 31.5},
  "disk": {"total_gb": 1006.85, "used_gb": 44.32, "free_gb": 911.32, "usage_percent": 4.6}
}
```

非工作日输出：
```json
{"status": "skipped", "reason": "非工作日（周末或节假日）", "date": "2026-05-09"}
```

超截止日期输出：
```json
{"status": "stopped", "reason": "已超过截止日期 2026-06-01"}
```

## 参考文件
- `references/holidays_2026.md` — 2026年中国法定节假日完整列表
