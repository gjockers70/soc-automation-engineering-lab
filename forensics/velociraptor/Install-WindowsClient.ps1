$ErrorActionPreference = 'Stop'
$Stage = 'C:\SOC-Lab\Phase11'
$ExpectedHash = 'c91cf8a32731c4c45c148393bc7d2af688c392194a9fffc4535e8b583260d55e'

$actual = (Get-FileHash -LiteralPath "$Stage\velociraptor.exe" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $ExpectedHash) { throw 'Velociraptor binary hash mismatch' }
New-Item -ItemType Directory -Path $Stage -Force | Out-Null
Set-Content -LiteralPath "$Stage\triage-marker.txt" -Value 'Synthetic Phase 11 filesystem metadata marker.' -Encoding Ascii
$service = Get-Service -Name 'Velociraptor' -ErrorAction SilentlyContinue
if ($service) {
    Stop-Service -Name 'Velociraptor' -Force -ErrorAction SilentlyContinue
    & sc.exe delete Velociraptor | Out-Null
    Start-Sleep -Seconds 2
}
& "$Stage\velociraptor.exe" --config "$Stage\client.config.yaml" service install -v
if ($LASTEXITCODE -ne 0) { throw 'Velociraptor service installation failed' }
Write-Output 'velociraptor_windows_client=installed'
