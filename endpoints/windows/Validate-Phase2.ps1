$ErrorActionPreference = "Stop"
$started = Get-Date

& powershell.exe -NoLogo -NoProfile -NonInteractive -Command "Get-Date | Out-Null; Get-LocalUser | Out-Null"
Start-Sleep -Seconds 3

$telemetryAddress = Get-NetIPAddress -AddressFamily IPv4 -IPAddress "10.77.30.40" -ErrorAction Stop
$defaultRoutes = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue
if ($defaultRoutes) {
    throw "Unexpected IPv4 default route exists"
}

$processAudit = (& auditpol.exe /get /subcategory:"Process Creation" | Out-String)
if ($processAudit -notmatch "Success") {
    throw "Process Creation success auditing is not enabled"
}

$commandLineAudit = Get-ItemPropertyValue `
    -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\Policies\System\Audit" `
    -Name ProcessCreationIncludeCmdLine_Enabled
if ($commandLineAudit -ne 1) {
    throw "Process command-line auditing is not enabled"
}

$scriptBlockAudit = Get-ItemPropertyValue `
    -Path "HKLM:\Software\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" `
    -Name EnableScriptBlockLogging
if ($scriptBlockAudit -ne 1) {
    throw "PowerShell script-block logging is not enabled"
}

$processEvent = Get-WinEvent -FilterHashtable @{
    LogName = "Security"
    Id = 4688
    StartTime = $started
} -ErrorAction Stop | Select-Object -First 1
$powerShellEvent = Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-PowerShell/Operational"
    Id = 4104
    StartTime = $started
} -ErrorAction Stop | Select-Object -First 1

if (-not (Test-Path "C:\ProgramData\SOCLab\phase2.conf")) {
    throw "Phase 2 endpoint state file is missing"
}

Write-Output "windows_phase2_validation=pass"
Write-Output "telemetry_address=$($telemetryAddress.IPAddress)/24"
Write-Output "default_route=absent"
Write-Output "process_event_id=$($processEvent.Id)"
Write-Output "powershell_event_id=$($powerShellEvent.Id)"
