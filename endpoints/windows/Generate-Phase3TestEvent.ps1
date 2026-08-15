$ErrorActionPreference = 'Stop'
$marker = 'SOC_PHASE3_BENIGN_POWERSHELL'
$testUser = 'soc_phase3_test'

Write-Output $marker
Get-Date | Out-Null

if (Get-LocalUser -Name $testUser -ErrorAction SilentlyContinue) {
    Remove-LocalUser -Name $testUser
}
$password = ConvertTo-SecureString ([Guid]::NewGuid().ToString() + 'aA1!') -AsPlainText -Force
New-LocalUser -Name $testUser -Password $password -AccountNeverExpires `
    -UserMayNotChangePassword -Description 'Temporary SOC Phase 3 validation identity' | Out-Null
Disable-LocalUser -Name $testUser
Remove-LocalUser -Name $testUser
Write-Output 'windows_synthetic_account_lifecycle=pass'
