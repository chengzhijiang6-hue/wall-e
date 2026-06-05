# -*- coding: utf-8 -*-
"""
Server Migration - Items Report (All-Items with Risk Levels)
Reads CSV files, classifies MS/non-MS items, highlights non-MS with risk levels
"""
import os
import sys
import csv
import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# === CONFIG: Update CSV_DIR for each device ===
CSV_DIR = r"C:\Users\CZE8WX\Desktop\work\server-migration\{DEVICE_IP}\raw"
OUTPUT_FILE = os.path.normpath(os.path.join(CSV_DIR, "..", "merged", f"Items_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"))

# === STYLES ===
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill("solid", fgColor="2F5496")
DATA_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
THIN_BORDER = Border(left=Side("thin"), right=Side("thin"), top=Side("thin"), bottom=Side("thin"))
NON_MS_FILL = PatternFill("solid", fgColor="FFC7CE")  # Light red for non-MS
HIGH_RISK_FILL = PatternFill("solid", fgColor="FF0000")
MEDIUM_RISK_FILL = PatternFill("solid", fgColor="FFC000")
LOW_RISK_FILL = PatternFill("solid", fgColor="92D050")

# === RISK DEFINITIONS ===
HIGH_RISK_PORTS = {21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 5985, 8080, 8443}
MEDIUM_RISK_PORTS = {20, 69, 88, 161, 162, 389, 636, 1080, 1723, 2049, 3268, 3269, 5060, 5061, 5986, 7001, 8000, 8001, 8008, 8888, 9090}


def read_csv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def is_ms(item):
    """Check if item is Microsoft-related (structured lookup > keyword matching)"""
    if "Is_Microsoft" in item:
        return item.get("Is_Microsoft", "Yes") == "Yes"

    svc_name = item.get("Name", item.get("Service_Name", "")).lower()
    display_name = item.get("DisplayName", item.get("Identity", "")).lower()
    path = item.get("PathName", item.get("Installation_Path", "")).lower()
    publisher = item.get("Publisher", "").lower()
    task_path = item.get("TaskPath", "").lower()

    # 1. Known Microsoft services (by service name - most reliable)
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
    if svc_name in ms_services:
        return True
    if svc_name in non_ms_services:
        return False

    # 2. Pattern matching (known third-party vendors)
    if "uc4" in svc_name or "servicemanager" in svc_name:
        return False
    if "vmware" in svc_name or "vmtools" in svc_name:
        return False
    if "aex" in svc_name or "altiris" in svc_name:
        return False
    if "splunk" in svc_name:
        return False

    # 3. Path/publisher/task path matching
    for kw in ["microsoft", "windows", "\\windows\\", "c:\\windows"]:
        if kw in publisher or kw in path:
            return True
    if "\\microsoft\\" in task_path:
        return True
    if "microsoft" in display_name or "windows" in display_name:
        return True

    return False


def get_port_risk(port):
    try:
        p = int(port)
        if p in HIGH_RISK_PORTS: return "HIGH"
        elif p in MEDIUM_RISK_PORTS: return "MEDIUM"
    except: pass
    return "LOW"


def get_service_risk(svc_name, path):
    svc_name = svc_name.lower()
    path = path.lower()
    high_risk = ["termservice", "winrm", "rpcss", "dcomlaunch", "samsss", "netlogon", "ntds"]
    if svc_name in high_risk: return "HIGH"
    medium_risk = ["spooler", "schedule", "eventlog", "cryptsvc", "msiserver", "trustedinstaller"]
    if svc_name in medium_risk: return "MEDIUM"
    if "system32" in path or "windows" in path: return "LOW"
    return "MEDIUM"


def get_task_risk(task_path, action):
    action = action.lower()
    if "powershell" in action or "cmd" in action or "script" in action: return "HIGH"
    if "\\microsoft\\" not in task_path.lower(): return "MEDIUM"
    return "LOW"


def get_software_risk(name, publisher):
    name = name.lower()
    publisher = publisher.lower()
    for kw in ["remote", "admin", "server", "database", "backup"]:
        if kw in name: return "HIGH"
    if "microsoft" not in publisher and "windows" not in publisher: return "MEDIUM"
    return "LOW"


def write_header(ws, headers):
    for c, h in enumerate(headers, 1):
        cell = ws.cell(1, c, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = DATA_ALIGN
        cell.border = THIN_BORDER


def write_rows(ws, data, headers, risk_func=None):
    write_header(ws, headers)
    for r, row in enumerate(data, 2):
        is_non_ms = row.get("Is_Microsoft", "Yes") == "No"
        risk_level = risk_func(row) if (risk_func and is_non_ms) else None

        for c, h in enumerate(headers, 1):
            cell = ws.cell(r, c, value=row.get(h, ""))
            cell.alignment = DATA_ALIGN
            cell.border = THIN_BORDER

            if is_non_ms:
                if h == "Risk_Level" and risk_level:
                    cell.value = risk_level
                    if risk_level == "HIGH":
                        cell.fill = HIGH_RISK_FILL
                        cell.font = Font(bold=True, color="FFFFFF")
                    elif risk_level == "MEDIUM":
                        cell.fill = MEDIUM_RISK_FILL
                        cell.font = Font(bold=True)
                    else:
                        cell.fill = LOW_RISK_FILL
                elif h != "Risk_Level":
                    cell.fill = NON_MS_FILL


def auto_width(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 4, 40)


def main():
    print("=" * 50)
    print("  Server Migration - Items Report")
    print("=" * 50)

    print("\n[1/3] Reading CSV files...")
    ports = read_csv(os.path.join(CSV_DIR, "1_Port_App_Mapping.csv"))
    services = read_csv(os.path.join(CSV_DIR, "2_Running_Services.csv"))
    tasks = read_csv(os.path.join(CSV_DIR, "3_Scheduled_Tasks.csv"))
    software = read_csv(os.path.join(CSV_DIR, "4_Installed_Software.csv"))

    print("[2/3] Classifying items...")
    ms_ports = [p for p in ports if is_ms(p)]
    non_ms_ports = [p for p in ports if not is_ms(p)]
    ms_services = [s for s in services if is_ms(s)]
    non_ms_services = [s for s in services if not is_ms(s)]
    ms_tasks = [t for t in tasks if is_ms(t)]
    non_ms_tasks = [t for t in tasks if not is_ms(t)]
    ms_software = [sw for sw in software if is_ms(sw)]
    non_ms_software = [sw for sw in software if not is_ms(sw)]

    print(f"  Ports: {len(ms_ports)} MS + {len(non_ms_ports)} non-MS = {len(ports)} total")
    print(f"  Services: {len(ms_services)} MS + {len(non_ms_services)} non-MS = {len(services)} total")
    print(f"  Tasks: {len(ms_tasks)} MS + {len(non_ms_tasks)} non-MS = {len(tasks)} total")
    print(f"  Software: {len(ms_software)} MS + {len(non_ms_software)} non-MS = {len(software)} total")

    print("[3/3] Generating report...")
    wb = Workbook()
    wb.remove(wb.active)

    # Sheet 1: All Ports
    ws1 = wb.create_sheet(title="All Ports")
    port_headers = ["Port", "Identity", "Service_Name", "Installation_Path", "Process_ID", "Is_Microsoft", "Risk_Level"]
    all_ports = ms_ports + non_ms_ports
    for p in all_ports:
        p["Is_Microsoft"] = "Yes" if is_ms(p) else "No"
    write_rows(ws1, all_ports, port_headers, risk_func=lambda x: get_port_risk(x.get("Port", "")))
    auto_width(ws1)

    # Sheet 2: All Services
    ws2 = wb.create_sheet(title="All Services")
    svc_headers = ["Name", "DisplayName", "State", "StartMode", "ProcessId", "PathName", "Is_Microsoft", "Risk_Level"]
    all_services = ms_services + non_ms_services
    for s in all_services:
        s["Is_Microsoft"] = "Yes" if is_ms(s) else "No"
    write_rows(ws2, all_services, svc_headers, risk_func=lambda x: get_service_risk(x.get("Name", ""), x.get("PathName", "")))
    auto_width(ws2)

    # Sheet 3: All Tasks
    ws3 = wb.create_sheet(title="All Tasks")
    task_headers = ["TaskName", "TaskPath", "State", "Action", "Is_Microsoft", "Risk_Level"]
    all_tasks = ms_tasks + non_ms_tasks
    for t in all_tasks:
        t["Is_Microsoft"] = "Yes" if is_ms(t) else "No"
    write_rows(ws3, all_tasks, task_headers, risk_func=lambda x: get_task_risk(x.get("TaskPath", ""), x.get("Action", "")))
    auto_width(ws3)

    # Sheet 4: All Software
    ws4 = wb.create_sheet(title="All Software")
    sw_headers = ["DisplayName", "DisplayVersion", "Publisher", "InstallLocation", "Is_Microsoft", "Risk_Level"]
    all_software = ms_software + non_ms_software
    for sw in all_software:
        sw["Is_Microsoft"] = "Yes" if is_ms(sw) else "No"
    write_rows(ws4, all_software, sw_headers, risk_func=lambda x: get_software_risk(x.get("DisplayName", ""), x.get("Publisher", "")))
    auto_width(ws4)

    wb.save(OUTPUT_FILE)
    print(f"\nDone: {OUTPUT_FILE}")
    print(f"  4 sheets, {len(all_ports) + len(all_services) + len(all_tasks) + len(all_software)} items total")
    print(f"  Microsoft: {len(ms_ports) + len(ms_services) + len(ms_tasks) + len(ms_software)}")
    print(f"  Non-Microsoft: {len(non_ms_ports) + len(non_ms_services) + len(non_ms_tasks) + len(non_ms_software)}")


if __name__ == "__main__":
    main()
