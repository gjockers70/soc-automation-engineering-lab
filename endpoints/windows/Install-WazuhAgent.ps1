$ErrorActionPreference = 'Stop'

$version = '4.14.7-1'
$work = 'C:\ProgramData\SOCLab'
$msi = Join-Path $work "wazuh-agent-$version.msi"
New-Item -ItemType Directory -Path $work -Force | Out-Null

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$base = 'https://packages.wazuh.com/4.x/windows'
Invoke-WebRequest -UseBasicParsing -Uri "$base/wazuh-agent-$version.msi" -OutFile $msi
$signature = Get-AuthenticodeSignature -LiteralPath $msi
if ($signature.Status -ne 'Valid') { throw "Wazuh MSI signature status is $($signature.Status)." }
if ($signature.SignerCertificate.Subject -notmatch 'Wazuh') { throw 'Unexpected Wazuh MSI publisher.' }

$arguments = @(
    '/i', $msi, '/qn',
    'WAZUH_MANAGER=10.77.30.10',
    'WAZUH_REGISTRATION_SERVER=10.77.30.10',
    'WAZUH_AGENT_NAME=win11-01'
)
$process = Start-Process -FilePath msiexec.exe -ArgumentList $arguments -Wait -PassThru
if ($process.ExitCode -notin @(0, 3010)) { throw "Wazuh MSI failed with exit code $($process.ExitCode)." }

Stop-Service -Name WazuhSvc -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $msi -Force
Write-Output 'windows_agent_install=pass'
