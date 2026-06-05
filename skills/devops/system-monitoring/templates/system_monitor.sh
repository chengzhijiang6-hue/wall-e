#!/bin/bash
# 系统资源监控 shell 包装器
# 用途: cron job 中强制使用 hermes venv Python，避免系统 Python 缺包问题
# 用法: chmod +x 后直接执行，或加入 crontab

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="/mnt/c/wsl/hermes_official/venv/bin/python3"
MONITOR_SCRIPT="$SCRIPT_DIR/system_monitor.py"

$PYTHON_PATH "$MONITOR_SCRIPT"
