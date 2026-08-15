$ErrorActionPreference = 'Stop'

$agentRoot = 'C:\Program Files (x86)\ossec-agent'
$config = Join-Path $agentRoot 'ossec.conf'
$passwordFile = Join-Path $agentRoot 'authd.pass'
if (-not (Test-Path -LiteralPath $passwordFile)) { throw 'Enrollment password file is missing.' }

$acl = New-Object System.Security.AccessControl.FileSecurity
$acl.SetAccessRuleProtection($true, $false)
$admins = New-Object System.Security.AccessControl.FileSystemAccessRule(
    'BUILTIN\Administrators', 'FullControl', 'Allow'
)
$system = New-Object System.Security.AccessControl.FileSystemAccessRule(
    'NT AUTHORITY\SYSTEM', 'FullControl', 'Allow'
)
$acl.AddAccessRule($admins)
$acl.AddAccessRule($system)
Set-Acl -LiteralPath $passwordFile -AclObject $acl

[xml]$xml = Get-Content -LiteralPath $config
if (-not ($xml.ossec_config.localfile | Where-Object { $_.location -eq 'Microsoft-Windows-PowerShell/Operational' })) {
    $localfile = $xml.CreateElement('localfile')
    $location = $xml.CreateElement('location')
    $location.InnerText = 'Microsoft-Windows-PowerShell/Operational'
    $format = $xml.CreateElement('log_format')
    $format.InnerText = 'eventchannel'
    [void]$localfile.AppendChild($location)
    [void]$localfile.AppendChild($format)
    [void]$xml.ossec_config.AppendChild($localfile)
}
if (-not ($xml.ossec_config.'active-response' | Where-Object { $_.disabled -eq 'yes' })) {
    $activeResponse = $xml.CreateElement('active-response')
    $disabled = $xml.CreateElement('disabled')
    $disabled.InnerText = 'yes'
    [void]$activeResponse.AppendChild($disabled)
    [void]$xml.ossec_config.AppendChild($activeResponse)
}
$xml.Save($config)

$password = (Get-Content -LiteralPath $passwordFile -Raw).Trim()
try {
    & (Join-Path $agentRoot 'agent-auth.exe') -m 10.77.30.10 -A win11-01 -P $password
    if ($LASTEXITCODE -ne 0) { throw "agent-auth failed with exit code $LASTEXITCODE." }
}
finally {
    $password = $null
}
Remove-Item -LiteralPath $passwordFile -Force
Set-Service -Name WazuhSvc -StartupType Automatic
Start-Service -Name WazuhSvc
Write-Output 'windows_agent_configuration=pass'
