# Risk Level Definitions for Migration Items

## Port Risk Levels

### HIGH Risk Ports
```
21 (FTP), 22 (SSH), 23 (Telnet), 25 (SMTP), 53 (DNS), 80 (HTTP),
110 (POP3), 135 (RPC), 139 (NetBIOS), 143 (IMAP), 443 (HTTPS),
445 (SMB), 993 (IMAPS), 995 (POP3S), 1433 (MSSQL), 1521 (Oracle),
3306 (MySQL), 3389 (RDP), 5432 (PostgreSQL), 5900 (VNC),
5985 (WinRM HTTP), 8080 (HTTP Alt), 8443 (HTTPS Alt)
```

### MEDIUM Risk Ports
```
20 (FTP Data), 69 (TFTP), 88 (Kerberos), 161 (SNMP), 162 (SNMP Trap),
389 (LDAP), 636 (LDAPS), 1080 (SOCKS), 1723 (PPTP), 2049 (NFS),
3268 (AD LDAP), 3269 (AD LDAPS), 5060 (SIP), 5061 (SIP TLS),
5986 (WinRM HTTPS), 7001 (WebLogic), 8000 (HTTP Alt),
8001 (HTTP Alt), 8008 (HTTP Alt), 8888 (HTTP Alt), 9090 (HTTP Alt)
```

### LOW Risk Ports
All other ports not in HIGH or MEDIUM lists.

## Service Risk Levels

### HIGH Risk Services
- `termservice` (RDP)
- `winrm` (Remote Management)
- `rpcss` (RPC)
- `dcomlaunch` (DCOM)
- `samsss` (Security Accounts Manager)
- `netlogon` (Network Logon)
- `ntds` (Active Directory)

### MEDIUM Risk Services
- `spooler` (Print Spooler)
- `schedule` (Task Scheduler)
- `eventlog` (Event Log)
- `cryptsvc` (Cryptography)
- `msiserver` (Windows Installer)
- `trustedinstaller` (Windows Modules Installer)

### LOW Risk Services
- Services with paths in `system32` or `windows` directories
- All other services

## Task Risk Levels

### HIGH Risk Tasks
- Tasks with `powershell` in action
- Tasks with `cmd` in action
- Tasks with `script` in action

### MEDIUM Risk Tasks
- Tasks NOT under `\Microsoft\` path (third-party tasks)

### LOW Risk Tasks
- Tasks under `\Microsoft\` path

## Software Risk Levels

### HIGH Risk Software
- Software names containing: `remote`, `admin`, `server`, `database`, `backup`

### MEDIUM Risk Software
- Software with non-Microsoft publisher

### LOW Risk Software
- Software with Microsoft/Windows publisher

## Excel Color Coding

| Risk Level | Background Color | Font |
|------------|-----------------|------|
| HIGH | Red (#FF0000) | Bold White |
| MEDIUM | Orange (#FFC000) | Bold |
| LOW | Green (#92D050) | Default |
| Non-MS (no risk) | Light Red (#FFC7CE) | Default |
