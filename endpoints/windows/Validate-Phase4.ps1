$ErrorActionPreference = 'Stop'

if ((Get-Service WazuhSvc).Status -ne 'Running') { throw 'WazuhSvc is not running.' }
foreach ($name in @('soc_phase4_test', 'soc_phase4_machine$')) {
    if (Get-LocalUser -Name $name -ErrorAction SilentlyContinue) {
        throw "Temporary validation identity remains: $name"
    }
}
if (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue) {
    throw 'Unexpected IPv4 default route.'
}
Write-Output 'windows_phase4_validation=pass'
