# Endpoint monitoring baseline

Phase 2 uses two owned lab endpoints:

- `ubuntu-web-01` at `10.77.30.20/24` for Linux authentication, privilege, process, and selected file-change telemetry;
- `win11-01` at `10.77.30.40/24` for Windows authentication, account-management, process-creation, and PowerShell telemetry.

Each endpoint retains its original `pentest-isolated` interface and receives a second interface on `soc-telemetry`. Neither telemetry interface has a default gateway. The domain controller and Kali VM are outside Phase 2 scope.

Wazuh 4.14.7 agents now forward these sources to `soc-mgr-01` over the isolated telemetry network. Password-authenticated enrollment and agent connectivity were validated before and after reboot.
