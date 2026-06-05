---
name: windows-server-audit
description: Windows Server 资产清点与迁移审计 — 端口、服务、计划任务、软件、共享、IIS、ODBC 全量采集，非微软项目自动标记高亮
trigger: 服务器迁移、资产清点、服务盘点、端口审计、Windows Server inventory
---

# Windows Server 资产清点与迁移审计

## 适用场景
- 服务器迁移前的资产清点
- 确认服务器运行的服务、端口、计划任务、软件、共享
- 快速区分微软/非微软项目，定位需要迁移的内容
- 终端用户无感迁移

## 采集清单（8 项）

| 序号 | 项目 | 关键字段 | 非微软标记 |
|------|------|---------|-----------|
| 1 | 端口映射 | Port, Protocol, Identity, Service, Path, Publisher | Is_Microsoft |
| 2 | 所有服务 | Name, State, StartMode, LogOnAccount, Path, Publisher | Is_Microsoft |
| 3 | 计划任务 | TaskName, TaskPath, State, Author, LastRunTime, Action | Is_Microsoft |
| 4 | 已安装软件 | DisplayName, Version, Publisher, InstallLocation | Is_Microsoft |
| 5 | 网络共享 | Name, Path, Description | Is_Default |
| 6 | IIS 网站 | SiteName, Bindings | N/A |
| 7 | ODBC 数据源 | DSN_Name, Driver, Server, Database, Type | N/A |
| 8 | 环境变量 + Hosts | Name, Value, Scope | N/A |

## 非微软判定逻辑
- **服务/软件**：检查 Publisher 是否包含 "Microsoft"，或服务账户为 LocalSystem/NetworkService/LocalService
- **计划任务**：TaskPath 以 `\Microsoft\` 开头或 Author 包含 "Microsoft"
- **端口**：已知系统端口（135/445/139/5985 等）标记为系统端口
- **共享**：C$/D$/ADMIN$/IPC$ 标记为默认共享

## PowerShell 脚本输出
输出 8 个 CSV 文件到指定目录，Is_Microsoft 列标记 Yes/No。
脚本详见 `templates/asset_inventory_v4.ps1`

## 离线环境处理
目标服务器通常无公网，PowerShell 脚本必须零依赖：
- 不使用 ImportExcel 模块
- 不使用第三方 PowerShell 库
- 使用原生 Get-CimInstance / Get-WmiObject / Get-ScheduledTask / Get-SmbShare

## 合并输出
CSV 复制到宿主机后，用 Agent 的 openpyxl 合并为多 Sheet Excel。

### 报告格式（All-Items 模式，推荐）
输出所有项目（MS + non-MS），通过 Is_Microsoft 列区分：
- All Ports：含 Is_Microsoft + Risk_Level 列
- All Services：含 Is_Microsoft + Risk_Level 列
- All Tasks：含 Is_Microsoft + Risk_Level 列
- All Software：含 Is_Microsoft + Risk_Level 列

格式规范：
- 非微软项目（Is_Microsoft=No）整行浅红色高亮 `PatternFill("solid", fgColor="FFC7CE")`
- Risk_Level 列：HIGH 红底白字 / MEDIUM 橙底 / LOW 绿底
- 首行蓝底白字加粗，冻结首行，隔行着色
- 文件存放：`C:\Users\CZE8WX\Desktop\work\server-migration\{device-ip}\merged\`

参见模板 `templates/merge_csv_to_excel.py`

## 非微软项目分析

提供两个版本的分析脚本：

### 简化版（推荐日常使用）
`templates/analyze_non_ms_simple.py` — 4个Sheet，直接列出非微软项目：
- Non-MS Ports：端口、关联服务、路径
- Non-MS Services：服务名、状态、启动方式、路径
- Non-MS Tasks：任务名、路径、执行动作
- Non-MS Software：软件名、版本、发布者、路径

### 完整版（需要依赖分析时）
`templates/analyze_non_ms_items.py` — 8个Sheet，含依赖关系和风险评估：
- Dashboard：统计 + 饼图
- Ports/Services/Tasks/Software/Shares：非微软项目详情
- Dependencies：服务→端口→进程→软件关联矩阵
- Migration_Checklist：迁移检查清单

### 非微软判定逻辑（无 Is_Microsoft 列时的 fallback）
当 CSV 文件没有 Is_Microsoft 列时，使用结构化查找（优先）+ 关键词兜底：

**策略：已知服务名集合 > 关键词匹配 > 路径/发布者匹配**

```python
def is_ms(item):
    svc_name = item.get("Name", item.get("Service_Name", "")).lower()
    display_name = item.get("DisplayName", item.get("Identity", "")).lower()
    path = item.get("PathName", item.get("Installation_Path", "")).lower()
    publisher = item.get("Publisher", "").lower()
    task_path = item.get("TaskPath", "").lower()

    # 1. 已知微软服务名集合（最可靠）
    ms_services = {
        "appxsvc", "appinfo", "bfe", "brokerinfrastructure", "comsysapp", "certpropsvc",
        "coremessagingregistrar", "cryptsvc", "dps", "dcomlaunch", "dhcp", "diagtrack",
        "dispbrokerdesktopsvc", "dnscache", "dssvc", "eventlog", "eventsystem", "fontcache",
        "hvhost", "insights", "keyiso", "lsm", "lanmanserver", "lanmanworkstation",
        "licensemanager", "msdtc", "ncbservice", "netsetupsvc", "netlogon", "nlasvc",
        "pcasvc", "plugplay", "policyagent", "power", "profsvc", "rpceptmapper", "rpcss",
        "sens", "samsss", "schedule", "securityhealthservice", "sense", "sessionenv",
        "staterepository", "storsvc", "sysmain", "systemeventsbroker", "tabletinputservice",
        "termservice", "themes", "timebrokersvc", "tokenbroker", "umrdpservice", "usermanager",
        "usosvc", "vgauthservice", "vm3dservice", "vmtools", "w32time", "wcmsvc",
        "wdnissvc", "windefend", "winhttpautoproxysvc", "winrm", "winmgmt", "wpnservice",
        "camsvc", "gpsvc", "iphlpsvc", "lmhosts", "mpssvc", "netprofm", "nsi", "wlidsvc",
        "wmiapsrv", "aelookupsvc", "autotimesvc", "bdesvc", "bthserv", "cdpsvc",
        "clipsvc", "embeddedmode", "entappsvc", "hidserv", "icssvc", "lfsvc",
        "lltdsvc", "msiscsi", "ncsi", "netprofmsvc", "pnrpsvc", "printnotify",
        "qwave", "rasauto", "rasman", "rdpcorets", "remoteregistry", "rpclocator",
        "scardsvr", "sdrsvc", "seclogon", "sensorservice", "sensrsvc", "shsvcs",
        "smphost", "spectrum", "sppsvc", "svsvc", "swprv", "tapisrv", "trkwks",
        "vds", "vmcompute", "vmms", "vmvss", "vss", "wbiosrvc", "wcncsvc",
        "webclient", "wia", "wersvc", "workfolderssvc", "wsearch", "wuauserv", "wudfsvc",
    }
    non_ms_services = {
        "aexnsclient", "altirisagentprovider", "splunkforwarder", "ovctrl",
        "intelligentextractionofficeaddinnginxservice",
        "intelligentextractionofficeaddinocrservice",
        "intelligentextractionofficeaddinadminservice",
    }
    if svc_name in ms_services: return True
    if svc_name in non_ms_services: return False

    # 2. 模式匹配（已知第三方厂商）
    if "uc4" in svc_name or "servicemanager" in svc_name: return False
    if "vmware" in svc_name or "vmtools" in svc_name: return False
    if "aex" in svc_name or "altiris" in svc_name: return False
    if "splunk" in svc_name: return False

    # 3. 路径/发布者/任务路径匹配
    for kw in ["microsoft", "windows", "\\windows\\", "c:\\windows"]:
        if kw in publisher or kw in path: return True
    if "\\microsoft\\" in task_path: return True
    if "microsoft" in display_name or "windows" in display_name: return True

    return False
```

**关键教训**：简单的关键词拼接匹配（`" ".join(values).lower()`）会误判，如 `Network List Service (netprofm)` 被错误归为非微软。必须用结构化的已知服务名集合。

### 风险等级划分

**端口风险**：
| 等级 | 端口 |
|------|------|
| HIGH | 21/22/23/25/135/139/445/1433/1521/3306/3389/5432/5900/5985/8080/8443 |
| MEDIUM | 80/88/110/143/389/443/636/993/995/1080/1723/2049/3268/3269/5060/5986/7001/8000/8001/8888/9090 |
| LOW | 其余 |

**服务风险**：
| 等级 | 服务 |
|------|------|
| HIGH | TermService, WinRM, RpcSs, DcomLaunch, SamSs, Netlogon, NTDS |
| MEDIUM | Spooler, Schedule, EventLog, CryptSvc, MsiServer, TrustedInstaller |
| LOW | 其余（含 system32/windows 路径的服务） |

**任务风险**：
| 等级 | 条件 |
|------|------|
| HIGH | Action 含 PowerShell/Cmd/Script |
| MEDIUM | TaskPath 不含 `\Microsoft\` |
| LOW | 其余 |

**软件风险**：
| 等级 | 条件 |
|------|------|
| HIGH | 软件名含 Remote/Admin/Server/Database/Backup |
| MEDIUM | Publisher 不含 Microsoft/Windows |
| LOW | 其余 |

## 交付规范（强制）
1. 脚本文件 + 使用说明文件一起交付
2. 使用说明包含：前置条件、操作步骤、输出说明、重点关注项
3. 文件存放到 `C:\Users\CZE8WX\Desktop\work\{project}\` 对应子目录
4. 修改脚本前必须经用户允许
5. 使用说明必须主动提供，不能等用户要求

## Pitfalls

### 系统端口不要过滤
迁移场景下系统端口也需要确认，保留所有端口，用 Is_System_Port 列标记而非过滤

### 修改文件前必须经用户允许（强制）
绝对不能自作主张覆盖或修改文件。修改外部路径文件前，必须先在同路径下备份源文件（如 xxx.bak），且必须经用户确认后才能覆盖。

### 交付时必须主动提供使用说明
交付工具/脚本类任务时，必须主动提供使用说明（前置条件、操作步骤、输出说明），不能等用户要求。使用说明与工具文件一起交付。

### 已安装软件必须同时采集 64 位和 32 位
```powershell
# 64 位
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*
# 32 位
Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*
```
结果需去重（按 DisplayName + DisplayVersion）

### 网络共享不要过滤默认共享
保留所有共享，用 Is_Default 列标记。迁移时可能需要确认默认共享的配置

### IIS 和 ODBC 需要判断是否存在
```powershell
$iisPath = "$env:systemroot\system32\inetsrv\appcmd.exe"
if (Test-Path $iisPath) { ... }
```
不存在时输出提示文件而非报错

### 宿主机 Python 环境
宿主机（Windows）有 Python 3.14.4 + openpyxl 3.1.5，路径 `C:\Programs\Python\python-3.14-amd64\`
公司内网有 PyPI 镜像：`rb-artifactory.bosch.com`

### Windows 控制台编码
宿主机 Python 脚本输出中文时必须修复编码：
```python
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```
