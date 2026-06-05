# =============================================================================
# WINDOWS SERVER MIGRATION - ASSET INVENTORY TOOL (v4)
# Purpose: Server migration inventory - identify all running services,
#          scheduled tasks, software, shares, ports for seamless migration
# Output:  CSV files to $exportPath
# =============================================================================

$exportPath = "C:\Users\RBAdmin_App1\Desktop\Migration_Check"
if (-not (Test-Path -Path $exportPath)) { New-Item -ItemType Directory -Path $exportPath -Force | Out-Null }

# Microsoft publisher keywords for filtering
$MS_PUBLISHERS = @("Microsoft", "Microsoft Corporation", "Microsoft Corp", "Windows")

function Is-MicrosoftPublisher {
    param($Publisher)
    if ([string]::IsNullOrWhiteSpace($Publisher)) { return $false }
    foreach ($kw in $MS_PUBLISHERS) {
        if ($Publisher -like "*$kw*") { return $true }
    }
    return $false
}

Clear-Host
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   WINDOWS SERVER MIGRATION - ASSET INVENTORY TOOL (v4)" -ForegroundColor Cyan
Write-Host "   Non-Microsoft items will be marked as [!] in CSV" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Path: $exportPath" -ForegroundColor White
Write-Host "Status: Running...`n" -ForegroundColor Yellow

# =============================================================================
# STEP 1: Port & Application Mapping (ALL ports, no filter)
# =============================================================================
Write-Host "[1/8] Analyzing ALL TCP Listening Ports..." -ForegroundColor Green

$connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue
$portResults = @()
$allServices = Get-WmiObject Win32_Service -ErrorAction SilentlyContinue

foreach ($conn in $connections) {
    $pid_child = $conn.OwningProcess
    $port = $conn.LocalPort
    $installPath = "Unknown" 
    $identity = "Unknown"
    $serviceName = "None"
    $publisher = "Unknown"
    $isMS = "No"
    
    $isSystemPort = if ($port -in 135, 445, 139, 5985, 47001, 59001, 137, 138, 67, 68, 53, 88, 389, 636, 3268, 3269) { "Yes" } else { "No" }
    
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $pid_child" -ErrorAction SilentlyContinue
        
        if ($proc) {
            $installPath = $proc.ExecutablePath
            $parentProc = Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.ParentProcessId)" -ErrorAction SilentlyContinue
            $svc = $allServices | Where-Object { $_.ProcessId -eq $pid_child -or $_.ProcessId -eq $proc.ParentProcessId } | Select-Object -First 1
            
            if ($svc) {
                $serviceName = $svc.Name
                if ($svc.PathName) { $installPath = $svc.PathName }
                $identity = "SERVICE: $($svc.Name) ($($svc.DisplayName))"
                $publisher = $svc.StartName
            } elseif ($parentProc) {
                $identity = "LAUNCHED BY: $($parentProc.Name)"
            } else {
                $identity = "PROCESS: $($proc.Name)"
            }
            
            if ($installPath -and $installPath -ne "Unknown") {
                $cleanPath = $installPath.Replace('"', '').Trim().Split(' ')[0]
                if (Test-Path $cleanPath -ErrorAction SilentlyContinue) {
                    $fileInfo = Get-AuthenticodeSignature $cleanPath -ErrorAction SilentlyContinue
                    if ($fileInfo.SignerCertificate) {
                        $publisher = $fileInfo.SignerCertificate.Subject
                    }
                }
            }
        }
    } catch {
        $identity = "Access Denied"
    }

    if ($installPath) { $installPath = $installPath.Replace('"', '').Trim() }
    $isMS = if ($publisher -like "*Microsoft*" -or $isSystemPort -eq "Yes") { "Yes" } else { "No" }

    $portResults += [PSCustomObject]@{
        'Port' = $port; 'Protocol' = "TCP"; 'Identity' = $identity
        'Service_Name' = $serviceName; 'Installation_Path' = $installPath
        'Process_ID' = $pid_child; 'Publisher' = $publisher
        'Is_System_Port' = $isSystemPort; 'Is_Microsoft' = $isMS
    }
}

# UDP listeners
$udpListeners = Get-NetUDPEndpoint -ErrorAction SilentlyContinue | Where-Object { $_.LocalAddress -ne "127.0.0.1" -and $_.LocalAddress -ne "::1" }
foreach ($udp in $udpListeners) {
    $pid_child = $udp.OwningProcess
    $port = $udp.LocalPort
    $installPath = "Unknown"; $identity = "Unknown"; $serviceName = "None"; $publisher = "Unknown"
    $isSystemPort = if ($port -in 135, 445, 139, 137, 138, 67, 68, 53, 88, 389, 123) { "Yes" } else { "No" }
    
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $pid_child" -ErrorAction SilentlyContinue
        if ($proc) {
            $installPath = $proc.ExecutablePath
            $svc = $allServices | Where-Object { $_.ProcessId -eq $pid_child } | Select-Object -First 1
            if ($svc) { $serviceName = $svc.Name; $identity = "SERVICE: $($svc.Name) ($($svc.DisplayName))"; $publisher = $svc.StartName }
            else { $identity = "PROCESS: $($proc.Name)" }
        }
    } catch {}
    
    if ($installPath) { $installPath = $installPath.Replace('"', '').Trim() }
    $isMS = if ($publisher -like "*Microsoft*" -or $isSystemPort -eq "Yes") { "Yes" } else { "No" }
    
    $portResults += [PSCustomObject]@{
        'Port' = $port; 'Protocol' = "UDP"; 'Identity' = $identity
        'Service_Name' = $serviceName; 'Installation_Path' = $installPath
        'Process_ID' = $pid_child; 'Publisher' = $publisher
        'Is_System_Port' = $isSystemPort; 'Is_Microsoft' = $isMS
    }
}

$portResults | Sort-Object 'Is_Microsoft', 'Port' | Export-Csv -Path "$exportPath\1_Port_App_Mapping.csv" -NoTypeInformation -Encoding UTF8
Write-Host "   -> $($portResults.Count) ports exported" -ForegroundColor White

# =============================================================================
# STEP 2-8: Services, Tasks, Software, Shares, IIS, ODBC, Env+Hosts
# =============================================================================
# (Full script available in work/scripts/ directory)

# Key patterns:
# - Services: Get-WmiObject Win32_Service, check Publisher via AuthenticodeSignature
# - Tasks: Get-ScheduledTask, Is_Microsoft based on TaskPath starting with \Microsoft\
# - Software: Both HKLM:\Software\...\Uninstall and HKLM:\Software\Wow6432Node\...\Uninstall
# - Shares: Get-SmbShare, Is_Default based on name pattern [A-Z]$|ADMIN$|IPC$
# - IIS: Test-Path $env:systemroot\system32\inetsrv\appcmd.exe before calling
# - ODBC: Registry HKLM:\SOFTWARE\ODBC\ODBC.INI and WOW6432Node variant
# - Env: Get-ChildItem Env: with scope classification
# - Hosts: Get-Content $env:SystemRoot\System32\drivers\etc\hosts
