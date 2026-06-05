# 非微软项目识别规则与风险等级

## 微软服务识别（关键词匹配）

### 已知微软服务名（小写）
```
appxsvc, appinfo, bfe, brokerinfrastructure, comsysapp, certpropsvc,
coremessagingregistrar, cryptsvc, dps, dcomlaunch, dhcp, diagtrack,
dispbrokerdesktopsvc, dnscache, dssvc, eventlog, eventsystem, fontcache,
hvhost, insights, keyiso, lsm, lanmanserver, lanmanworkstation,
licensemanager, msdtc, ncbservice, netsetupsvc, netlogon, nlasvc,
pcasvc, plugplay, policyagent, power, profsvc, rpceptmapper, rpcss,
sens, samsss, schedule, securityhealthservice, sense, sessionenv,
staterepository, storsvc, sysmain, systemeventsbroker, tabletinputservice,
termservice, themes, timebrokersvc, tokenbroker, umrdpservice, usermanager,
usosvc, vgauthservice, vm3dservice, vmtools, w32time, wcmsvc,
wdnissvc, windefend, winhttpautoproxysvc, winrm, winmgmt, wpnservice,
camsvc, gpsvc, iphlpsvc, lmhosts, mpssvc, netprofm, nsi, wlidsvc,
wmiapsrv, netprofm, netman, nlasvc
```

### 已知第三方服务（明确标记为非微软）
- `aexnsclient`, `altirisagentprovider` → Symantec/Altiris
- `splunkforwarder` → Splunk
- `ovctrl` → HP OpenView
- `vgauthservice`, `vmtools`, `vm3dservice` → VMware
- `uc4.servicemanager*`, `jcs_rmj*` → UC4/Automic (Bosch)
- `intelligentextraction*` → 第三方 OCR/Office 插件

### 回退判断逻辑
1. 检查 `Is_Microsoft` 列（v4 脚本输出）
2. 检查 Publisher 包含 "microsoft" / "windows"
3. 检查 PathName 包含 "\windows\" / "c:\windows"
4. 检查 TaskPath 包含 "\microsoft\"
5. 检查 DisplayName 包含 "microsoft" / "windows"
6. 以上都不匹配 → 默认标记为非微软

## 风险等级定义

### 端口风险
- **HIGH**: 21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 5985, 8080, 8443
- **MEDIUM**: 20, 69, 88, 161, 162, 389, 636, 1080, 1723, 2049, 3268, 3269, 5060, 5061, 5986, 7001, 8000, 8001, 8008, 8888, 9090
- **LOW**: 其他

### 服务风险
- **HIGH**: termservice, winrm, rpcss, dcomlaunch, samsss, netlogon, ntds
- **MEDIUM**: spooler, schedule, eventlog, cryptsvc, msiserver, trustedinstaller
- **LOW**: 路径在 system32/windows 下的服务

### 计划任务风险
- **HIGH**: Action 包含 powershell / cmd / script
- **MEDIUM**: TaskPath 不包含 \microsoft\
- **LOW**: 其他

### 软件风险
- **HIGH**: 名称包含 remote / admin / server / database / backup
- **MEDIUM**: Publisher 不包含 microsoft / windows
- **LOW**: 其他
