#!/usr/bin/env python3
"""系统资源监控脚本 — 输出 CPU/内存/磁盘使用率，跳过周末和法定节假日"""
import psutil
import json
from datetime import datetime, date

# 2026年中国法定节假日（从 gov.cn 提取，详见 skills/devops/system-monitoring/references/holidays_2026.md）
HOLIDAYS_2026 = [
    date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3),
    date(2026, 2, 15), date(2026, 2, 16), date(2026, 2, 17),
    date(2026, 2, 18), date(2026, 2, 19), date(2026, 2, 20),
    date(2026, 2, 21), date(2026, 2, 22), date(2026, 2, 23),
    date(2026, 4, 4), date(2026, 4, 5), date(2026, 4, 6),
    date(2026, 5, 1), date(2026, 5, 2), date(2026, 5, 3),
    date(2026, 5, 4), date(2026, 5, 5),
    date(2026, 6, 19), date(2026, 6, 20), date(2026, 6, 21),
    date(2026, 9, 25), date(2026, 9, 26), date(2026, 9, 27),
    date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3),
    date(2026, 10, 4), date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 7),
]

END_DATE = date(2026, 6, 1)  # 截止日期，按需修改

def is_workday(d):
    if d.weekday() >= 5:
        return False
    if d in HOLIDAYS_2026:
        return False
    return True

def get_system_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "is_workday": True,
        "cpu": {"usage_percent": cpu_percent, "cores": psutil.cpu_count()},
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "usage_percent": memory.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "usage_percent": disk.percent,
        },
    }

if __name__ == "__main__":
    try:
        today = date.today()
        if today > END_DATE:
            print(json.dumps({"status": "stopped", "reason": f"已超过截止日期 {END_DATE}"}, ensure_ascii=False))
        elif not is_workday(today):
            print(json.dumps({"status": "skipped", "reason": "非工作日（周末或节假日）", "date": today.strftime("%Y-%m-%d")}, ensure_ascii=False))
        else:
            print(json.dumps(get_system_resources(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
