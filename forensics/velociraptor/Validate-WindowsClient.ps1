$ErrorActionPreference = 'Stop'
$service = Get-Service -Name 'Velociraptor'
if ($service.Status -ne 'Running') { throw 'Velociraptor service is not running' }
$default = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue
if ($default) { throw 'Windows endpoint has a default route' }
$hash = (Get-FileHash -LiteralPath 'C:\Program Files\Velociraptor\Velociraptor.exe' -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne 'c91cf8a32731c4c45c148393bc7d2af688c392194a9fffc4535e8b583260d55e') { throw 'Installed binary hash mismatch' }
[ordered]@{
    service = 'running'
    binary_hash = $hash
    default_route = 'absent'
    synthetic_marker = (Test-Path -LiteralPath 'C:\SOC-Lab\Phase11\triage-marker.txt')
} | ConvertTo-Json -Compress
