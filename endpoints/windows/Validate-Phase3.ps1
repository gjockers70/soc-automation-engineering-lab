$ErrorActionPreference = 'Stop'
$agentRoot = 'C:\Program Files (x86)\ossec-agent'
$config = Join-Path $agentRoot 'ossec.conf'
$passwordFile = Join-Path $agentRoot 'authd.pass'

if ((Get-Service WazuhSvc).Status -ne 'Running') { throw 'WazuhSvc is not running.' }
$text = Get-Content -LiteralPath $config -Raw
if ($text -notmatch '<address>10\.77\.30\.10</address>') { throw 'Manager address is not configured.' }
if ($text -notmatch 'Microsoft-Windows-PowerShell/Operational') { throw 'PowerShell channel is not configured.' }
if ($text -notmatch '<disabled>yes</disabled>') { throw 'Active response is not disabled.' }
if (Test-Path -LiteralPath $passwordFile) { throw 'Enrollment password file remains after enrollment.' }
if (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue) { throw 'Unexpected IPv4 default route.' }
Write-Output 'windows_phase3_validation=pass'
