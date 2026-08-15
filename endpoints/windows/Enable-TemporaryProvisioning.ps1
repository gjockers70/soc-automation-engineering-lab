$ErrorActionPreference = 'Stop'
$adapter = Get-NetAdapter | Where-Object MacAddress -eq '52-54-00-12-30-40'
if (-not $adapter) { throw 'Temporary provisioning adapter was not found.' }

Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue
New-NetIPAddress -InterfaceIndex $adapter.ifIndex -IPAddress '192.168.123.140' `
    -PrefixLength 24 -DefaultGateway '192.168.123.1' | Out-Null
Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ServerAddresses '192.168.123.1'
Write-Output 'windows_temporary_provisioning=enabled'
