$ErrorActionPreference = 'Stop'
$machineLikeUser = 'soc_phase4_machine$'

$plain = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -ArgumentList '-NoProfile', '-NonInteractive', '-Command', `
    "Write-Output 'SOC_PHASE4_NEGATIVE_PLAIN'" -Wait -PassThru
if ($plain.ExitCode -ne 0) { throw "Plain PowerShell exited with $($plain.ExitCode)." }

if (Get-LocalUser -Name $machineLikeUser -ErrorAction SilentlyContinue) {
    Remove-LocalUser -Name $machineLikeUser
}
$password = ConvertTo-SecureString ([Guid]::NewGuid().ToString() + 'aA1!') -AsPlainText -Force
New-LocalUser -Name $machineLikeUser -Password $password -AccountNeverExpires `
    -UserMayNotChangePassword -Description 'Temporary Phase 4 negative test' | Out-Null
Disable-LocalUser -Name $machineLikeUser
Remove-LocalUser -Name $machineLikeUser

Write-Output 'phase4_windows_negative_events=pass'
