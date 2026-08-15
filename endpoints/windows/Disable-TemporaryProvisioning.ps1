$ErrorActionPreference = 'Stop'
$adapter = Get-NetAdapter | Where-Object MacAddress -eq '52-54-00-12-30-40'
if ($adapter) {
    Get-NetRoute -InterfaceIndex $adapter.ifIndex -DestinationPrefix '0.0.0.0/0' `
        -ErrorAction SilentlyContinue | Remove-NetRoute -Confirm:$false
    Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ResetServerAddresses
    Disable-NetAdapter -Name $adapter.Name -Confirm:$false
}
Write-Output 'windows_temporary_provisioning=disabled'
