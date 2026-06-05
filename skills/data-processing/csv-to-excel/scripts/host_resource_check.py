#!/usr/bin/env python3
"""
宿主机资源检查脚本 — 通过 WSL 调用 PowerShell 获取 Windows 宿主机资源
用法: python3 host_resource_check.py
"""
import subprocess
import json

def run_ps(command):
    """执行 PowerShell 命令并返回输出"""
    result = subprocess.run(
        ["powershell.exe", "-Command", command],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

def get_host_resources():
    """获取宿主机资源使用情况"""
    # 内存
    mem_raw = run_ps("Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ConvertTo-Json")
    mem = json.loads(mem_raw)
    mem_total_gb = mem["TotalVisibleMemorySize"] / (1024**2)
    mem_used_gb = (mem["TotalVisibleMemorySize"] - mem["FreePhysicalMemory"]) / (1024**2)
    mem_free_gb = mem["FreePhysicalMemory"] / (1024**2)
    mem_pct = (mem_used_gb / mem_total_gb) * 100

    # CPU
    cpu_raw = run_ps("Get-CimInstance Win32_Processor | Select-Object LoadPercentage, NumberOfCores, NumberOfLogicalProcessors | ConvertTo-Json")
    cpu = json.loads(cpu_raw)

    # 磁盘（所有固定磁盘 DriveType=3）
    disk_raw = run_ps("Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID, Size, FreeSpace | ConvertTo-Json")
    disk_data = json.loads(disk_raw)
    if isinstance(disk_data, dict):
        disk_data = [disk_data]

    result = {
        "cpu": {
            "usage_percent": cpu["LoadPercentage"],
            "cores": cpu["NumberOfCores"],
            "logical_processors": cpu["NumberOfLogicalProcessors"]
        },
        "memory": {
            "total_gb": round(mem_total_gb, 2),
            "used_gb": round(mem_used_gb, 2),
            "free_gb": round(mem_free_gb, 2),
            "usage_percent": round(mem_pct, 1)
        },
        "disks": []
    }

    for d in disk_data:
        total = d["Size"] / (1024**3)
        free = d["FreeSpace"] / (1024**3)
        used = total - free
        result["disks"].append({
            "drive": d["DeviceID"],
            "total_gb": round(total, 2),
            "used_gb": round(used, 2),
            "free_gb": round(free, 2),
            "usage_percent": round((used / total) * 100, 1)
        })

    return result

if __name__ == "__main__":
    try:
        resources = get_host_resources()
        print(json.dumps(resources, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
