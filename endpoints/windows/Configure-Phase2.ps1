$ErrorActionPreference = "Stop"

$telemetryMac = "525400773040"
$adapter = Get-NetAdapter | Where-Object {
    ($_.MacAddress -replace '-', '') -eq $telemetryMac
}
if (-not $adapter) {
    throw "SOC telemetry adapter was not found"
}

$existingAddress = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -eq "10.77.30.40" }
if (-not $existingAddress) {
    Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.PrefixOrigin -ne "WellKnown" } |
        Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue
    New-NetIPAddress -InterfaceIndex $adapter.ifIndex -IPAddress "10.77.30.40" -PrefixLength 24 | Out-Null
}

Set-NetIPInterface -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -Dhcp Disabled
Set-NetIPInterface -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -InterfaceMetric 50

$auditPolicies = @(
    "Logon",
    "Logoff",
    "Account Lockout",
    "User Account Management",
    "Security Group Management",
    "Process Creation"
)
foreach ($subcategory in $auditPolicies) {
    & auditpol.exe /set /subcategory:"$subcategory" /success:enable /failure:enable | Out-Null
}

$auditKey = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Policies\System\Audit"
New-Item -Path $auditKey -Force | Out-Null
New-ItemProperty -Path $auditKey -Name ProcessCreationIncludeCmdLine_Enabled -PropertyType DWord -Value 1 -Force | Out-Null

$powerShellPolicy = "HKLM:\Software\Policies\Microsoft\Windows\PowerShell"
$scriptBlockKey = Join-Path $powerShellPolicy "ScriptBlockLogging"
$moduleKey = Join-Path $powerShellPolicy "ModuleLogging"
$moduleNamesKey = Join-Path $moduleKey "ModuleNames"
New-Item -Path $scriptBlockKey -Force | Out-Null
New-ItemProperty -Path $scriptBlockKey -Name EnableScriptBlockLogging -PropertyType DWord -Value 1 -Force | Out-Null
New-Item -Path $moduleNamesKey -Force | Out-Null
New-ItemProperty -Path $moduleKey -Name EnableModuleLogging -PropertyType DWord -Value 1 -Force | Out-Null
New-ItemProperty -Path $moduleNamesKey -Name "*" -PropertyType String -Value "*" -Force | Out-Null

& wevtutil.exe sl Microsoft-Windows-PowerShell/Operational /e:true

$statePath = "C:\ProgramData\SOCLab"
New-Item -ItemType Directory -Path $statePath -Force | Out-Null
@"
endpoint_role=windows
telemetry_address=10.77.30.40/24
log_sources=Security,System,PowerShell
"@ | Set-Content -Path (Join-Path $statePath "phase2.conf") -Encoding ASCII

Write-Output "telemetry_adapter=$($adapter.Name)"
Write-Output "telemetry_address=$((Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 | Where-Object IPAddress -eq '10.77.30.40').IPAddress)"
Write-Output "powershell_operational=$((Get-WinEvent -ListLog 'Microsoft-Windows-PowerShell/Operational').IsEnabled)"
& auditpol.exe /get /subcategory:"Logon","Account Lockout","User Account Management","Security Group Management","Process Creation"
