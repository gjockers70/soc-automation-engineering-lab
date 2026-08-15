$ErrorActionPreference = 'Stop'
$testUser = 'soc_phase4_test'

$payload = [Text.Encoding]::Unicode.GetBytes("Write-Output 'SOC_PHASE4_BENIGN_ENCODED_COMMAND'")
$encoded = [Convert]::ToBase64String($payload)
$process = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -ArgumentList '-NoProfile', '-NonInteractive', '-EncodedCommand', $encoded -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Benign encoded PowerShell exited with $($process.ExitCode)." }

if (Get-LocalUser -Name $testUser -ErrorAction SilentlyContinue) {
    Remove-LocalUser -Name $testUser
}
$password = ConvertTo-SecureString ([Guid]::NewGuid().ToString() + 'aA1!') -AsPlainText -Force
New-LocalUser -Name $testUser -Password $password -AccountNeverExpires `
    -UserMayNotChangePassword -Description 'Temporary SOC Phase 4 validation user' | Out-Null
Disable-LocalUser -Name $testUser
Remove-LocalUser -Name $testUser

Write-Output 'phase4_windows_test_events=pass'
