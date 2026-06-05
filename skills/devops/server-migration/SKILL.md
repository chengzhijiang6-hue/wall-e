---
name: server-migration
description: Windows Server migration asset inventory — collect, analyze, and report server services, ports, tasks, software, shares for seamless migration
triggers:
  - user asks about server migration
  - user asks to inventory or audit a Windows server
  - user asks to identify non-Microsoft services on a server
  - user asks about CAS IP filter or network traffic analysis
  - user mentions migrating servers or moving workloads
  - user says 整理表格 or 分析连接表 (connection table CSVs from CAS firewall)
  - user has Connection Table CSV files to organize or summarize
---

# Server Migration — Asset Inventory & Analysis

Collect running services, scheduled tasks, installed software, network shares, and port usage from Windows servers. Identify non-Microsoft items with risk levels for migration planning.

## File Organization (STRICT)

All work data: `C:\Users\CZE8WX\Desktop\work\server-migration\`
All filenames and folders MUST be in English.

```
work/
├── server-migration/
│   └── <DEVICE_IP>/
│       ├── CAS IP Filter/
│       │   ├── raw/          # CAS traffic CSVs
│       │   └── merged/       # Combined Excel
│       ├── raw/              # Script output CSVs
│       └── merged/           # Analysis reports
├── scripts/                  # All scripts
└── <other-projects>/         # Other work categories
```

**Multi-device**: Each device gets its own `<DEVICE_IP>/` subdirectory.
**Merging rule**: NEVER delete or modify source data during merge operations.

## Workflow

### Step 1: Collect Data (on target server)

Script: `All-in-One Migration Script.txt` → rename to `.ps1` on target server

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\All-in-One_Migration_Script.ps1
```

Output (8 files):
| File | Content |
|------|---------|
| 1_Port_App_Mapping.csv | TCP+UDP listening ports with service/process mapping |
| 2_All_Services.csv | All services (running + stopped) with Is_Microsoft flag |
| 3_Scheduled_Tasks.csv | Non-disabled scheduled tasks with Is_Microsoft flag |
| 4_Installed_Software.csv | 64-bit + 32-bit software with Is_Microsoft flag |
| 5_Network_Shares.csv | All SMB shares with Is_Default flag |
| 6_IIS_Sites.csv (or .txt) | IIS websites (if IIS installed) |
| 7_ODBC_DataSources.csv | ODBC DSN (64-bit + 32-bit) |
| 8a_Env_Variables.csv | Environment variables |
| 8b_Hosts_File.txt | Hosts file entries |

### Step 2: Copy CSVs to raw/ folder

User copies CSVs to `work\server-migration\<DEVICE_IP>\raw\`

### Step 3: Analyze Non-Microsoft Items

Script: `Analyze_Non_MS_Simple.py`

```bash
python C:\Users\CZE8WX\Desktop\work\scripts\Analyze_Non_MS_Simple.py
```

Output: `Non_MS_Simple_Report_<timestamp>.xlsx`
- Sheet "All Ports": all ports + Is_Microsoft + Risk_Level
- Sheet "All Services": all services + Is_Microsoft + Risk_Level
- Sheet "All Tasks": all tasks + Is_Microsoft + Risk_Level
- Sheet "All Software": all software + Is_Microsoft + Risk_Level

Non-MS items highlighted in light red. Risk levels:
- HIGH (red): high-risk ports (3389/22/445/135), critical services, PowerShell tasks
- MEDIUM (orange): moderate-risk items
- LOW (green): low-risk items

### Step 4: Merge CSVs to Multi-Sheet Excel

Script: `Merge_CSV_to_Excel.py`

Output: `Migration_Report.xlsx` with 5 sheets (one per CSV)

## Script Configuration

Scripts use hardcoded paths. Before running on a new device, update BOTH scripts:

**Analyze_Non_MS_Simple.py** (line ~17):
```python
CSV_DIR = r"C:\Users\CZE8WX\Desktop\work\server-migration\<DEVICE_IP>\raw"
# OUTPUT_FILE auto-resolves to ../merged/ relative to CSV_DIR — no change needed
```

**Merge_CSV_to_Excel.py** (line ~19):
```python
CSV_DIR = r"C:\Users\CZE8WX\Desktop\work\server-migration\<DEVICE_IP>\raw"
OUTPUT_FILE = os.path.normpath(os.path.join(CSV_DIR, "..", "merged", "Migration_Report.xlsx"))
```

Replace `<DEVICE_IP>` with the actual server IP. Both scripts must point to the same `raw/` folder.

**Run order**: Analyze first (generates Non_MS report), then Merge (generates full report).
**Runner**: Use Windows Python — `C:\Programs\Python\python-3.14-amd64\python.exe <script>.py`
**Backup**: Always `.bak` the script before modifying paths.

## CAS IP Filter (Network Traffic)

Separate workflow for CAS (network firewall) traffic data. Two paths:
- **路径A 快速汇总**：用户说"整理表格"时，生成 Markdown 分类报告（按 AD/AGV/PLC/SSH/邮件/其他 功能分类）
- **路径B 完整报告**：用户说"合并 Excel"时，生成多 Sheet Excel（明细+多维度汇总）

CSV 文件可能在 `<DEVICE_IP>/` 根目录或 `<DEVICE_IP>/CAS IP Filter/raw/`，两种都需支持。
- **详细工作流**：`references/cas_ip_filter_workflow.md`

## Pitfalls

### Script v4 vs v3
- v4 includes Is_Microsoft flag in CSVs (preferred)
- v3 does NOT have Is_Microsoft flag — analysis script uses fallback heuristics
- Always use v4 when possible; fallback heuristics are less accurate

### Non-Microsoft Service Identification
The `is_ms()` function in the analysis script uses:
1. Known Microsoft service name list (extensive)
2. Known third-party service patterns (VMware, Symantec, Splunk, UC4, etc.)
3. Publisher/path keywords (microsoft, windows)
4. Task path patterns (\\Microsoft\\)

**When user reports false positives** (e.g., "Network List Service" classified as non-MS):
- The service name `netprofm` must be in the known MS services list
- Update the `ms_services` set in the script
- Re-run and verify

### IIS Sites File Format Inconsistency
The migration script may output IIS sites as `6_IIS_Sites.txt` (plain text) instead of `6_IIS_Sites.csv`. The `Merge_CSV_to_Excel.py` script only processes `.csv` files — a `.txt` IIS file will be silently skipped. This is expected behavior (IIS may not be installed, or the output format varies by script version). Verify IIS data was captured by checking the file content manually if needed.

### Duplicate Service Files
The migration script v4 outputs `2_All_Services.csv` (all services with Is_Microsoft flag). Some older runs may also produce `2_Running_Services.csv` (running-only, without Is_Microsoft). The analysis script (`Analyze_Non_MS_Simple.py`) reads `2_Running_Services.csv` — if only `2_All_Services.csv` exists, either rename it or update the script's filename reference.

### File Permission Errors
If Excel file is open in Windows, Python cannot write to it. Solution:
- Use timestamp in filename: `Report_YYYYMMDD_HHMMSS.xlsx`
- Or ask user to close the file first

### PowerShell Encoding
Windows console uses cp1252 by default. Python scripts must add:
```python
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

### UNC Path Access from WSL
WSL cannot directly access UNC paths. Use PowerShell:
```powershell
Copy-Item -LiteralPath '\\server\share\path' -Destination 'C:\local\path' -Force
```
- Use `-LiteralPath` to prevent backslash escaping
- Copy to local first, then read with WSL tools

### Host Machine Environment
- Python 3.14.4 + pip 26.0.1 + openpyxl 3.1.5
- Path: `C:\Programs\Python\python-3.14-amd64\`
- PyPI mirror: `rb-artifactory.bosch.com` (internal)

### High Port Preference
Always use ports 59000+ for local services (Web GUI, dev servers, etc.) to avoid conflicts with system services and Docker containers.

## User Preferences (MANDATORY)

1. **Permission before modification**: NEVER modify files without explicit user approval
2. **Backup before change**: Always backup source files (e.g., xxx.bak) before modifying
3. **Usage documentation**: Always provide usage docs when delivering tools/scripts
4. **English naming**: All files and folders must use English names
5. **No data deletion**: Merging must NEVER delete or modify source data
6. **All items in report**: Reports must include ALL items (MS + non-MS), not just non-MS
7. **Highlight non-MS**: Non-MS items must be highlighted with risk levels
8. **Progress display**: Show [N/M] progress for all multi-step tasks

## References

- `references/ms_service_identification.md` — Microsoft vs third-party service classification lists and rules
- `references/risk_level_definitions.md` — Risk level criteria for ports, services, tasks, software
- `references/cas_ip_filter_workflow.md` — CAS 防火墙连接表数据整合详细工作流

## Host Commands Reference

```powershell
# List services
Get-CimInstance Win32_Service | Where-Object {$_.State -eq 'Running'}

# List TCP listeners
Get-NetTCPConnection -State Listen

# List scheduled tasks
Get-ScheduledTask | Where-Object {$_.State -ne 'Disabled'}

# List installed software (64-bit)
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*

# List installed software (32-bit)
Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*

# List SMB shares
Get-SmbShare

# List IIS sites
%systemroot%\system32\inetsrv\appcmd.exe list site

# List ODBC DSN
Get-ItemProperty HKLM:\SOFTWARE\ODBC\ODBC.INI\*
```
