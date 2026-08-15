# Windows endpoint

`win11-01` retains its isolated workload address and adds `10.77.30.40/24` for SOC telemetry. The configuration enables focused authentication, account-management, security-group, process-creation, and PowerShell logging. Process command lines are included for investigation context.

The configuration does not disable accounts, change endpoint firewall policy, or perform containment. Phase 2 validation launches only a harmless PowerShell child process and reads the resulting local event records.

The Phase 3 Wazuh agent collects standard Windows event channels plus Microsoft-Windows-PowerShell/Operational. Enrollment uses a temporarily transferred ACL-protected password file that is deleted after success, active response is disabled, and the supplied validation identity is removed immediately after its native account-management events are generated.

Phase 4 validation launches only a harmless encoded Write-Output command and creates a temporary local validation identity that is disabled and removed immediately. The generator performs no containment or persistence.
