# Microsoft Service Identification Reference

## Known Microsoft Services (by service name)

These are confirmed Windows built-in services. The `is_ms()` function checks against this list.

### Core Windows Services
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
wmiapsrv
```

### Additional Windows Services
```
aelookupsvc, autotimesvc, axinstsv, bdesvc, bthserv, cdpsvc, cdpstsvc,
clipsvc, cloudidsvc, cmsystem, coremessaging, dcsvc, devquerybroker,
dhcpxsvc, dmwappushsvc, dot3svc, embeddedmode, entappsvc, fdpHost,
fdrespub, hidserv, icssvc, lfsvc, lltdsvc, msiscsi, msiexec,
naturalauthentication, ncsi, netprofmsvc, nfsv3, nfsvc, pnrpauto,
pnrpsvc, printnotify, qwave, rasauto, rasman, rdpbus, rdpcorets,
rdpvideortp, remoteregistry, retokencertsvc, rpclocator, scardsvr,
scdeviceenum, scpolicysvc, sdrsvc, seclogon, sensordataservice,
sensorservice, sensrsvc, shsvcs, smphost, smpsvc, spectrum, sppsvc,
svsvc, swprv, tapisrv, tieringengineservice, trkwks, tzautoupdate,
uhssvc, umbus, umpass, unistore, userdataaccess, vds, vmcompute,
vmms, vmvss, vmworkstation, vss, wbiosrvc, wcncsvc, webclient,
webthreatdefsvc, wfdsconmgrsvc, wia, wercplink, wersvc, wmiapsrv,
workfolderssvc, wpcmonsvc, wsearch, wuauserv, wudfsvc
```

## Known Third-Party Services (NOT Microsoft)

```
aexnsclient, altirisagentprovider       # Symantec/Altiris
splunkforwarder                         # Splunk
ovctrl                                  # HP OpenView
vgauthservice, vmtools, vm3dservice     # VMware
intelligentextractionofficeaddin*       # Third-party OCR/extraction
uc4.servicemanager                      # UC4/Automic (Broadcom)
jcs_rmj                                 # Bosch/Bosch RunMyJobs
```

## Classification Rules

1. Check service name against known MS list → return True
2. Check service name against known non-MS list → return False
3. Pattern match: `uc4` or `servicemanager` → non-MS
4. Pattern match: `vmware` or `vmtools` → non-MS
5. Pattern match: `aex` or `altiris` → non-MS
6. Pattern match: `splunk` → non-MS
7. Check publisher/path for "microsoft", "windows", "\windows\" → MS
8. Check task path for "\microsoft\" → MS
9. Check display name for "microsoft" or "windows" → MS
10. Default: return False (unknown = non-MS, safer for migration)

## False Positive Fix Process

When user reports a service incorrectly classified:
1. Find the service name in the CSV
2. Research the service (Microsoft docs, web search)
3. Add to `ms_services` set if confirmed Microsoft
4. Re-run analysis script
5. Update this reference file

### Fixed False Positives
- `netprofm` (Network List Service) — added to ms_services
