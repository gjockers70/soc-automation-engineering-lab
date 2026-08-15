$ErrorActionPreference = 'Stop'
$passwordFile = 'C:\Program Files (x86)\ossec-agent\authd.pass'
if (Test-Path -LiteralPath $passwordFile) {
    Remove-Item -LiteralPath $passwordFile -Force
}
if (Test-Path -LiteralPath $passwordFile) { throw 'Enrollment password cleanup failed.' }
Write-Output 'windows_enrollment_secret_cleanup=pass'
