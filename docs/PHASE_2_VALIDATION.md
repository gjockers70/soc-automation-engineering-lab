# Phase 2 validation procedure

## Linux

Run `endpoints/linux/validate_phase2.sh` as root through the guest agent. It verifies:

- the `10.77.30.20/24` address and absence of a default route;
- active and enabled `auditd`;
- identity, privilege, selected-file, and user-execution audit rules;
- readable authentication and audit logs;
- creation and retrieval of one benign file-write event.

Expected terminal result: `linux_phase2_validation=pass`.

## Windows

Run `endpoints/windows/Validate-Phase2.ps1` as Local System through the guest agent. It verifies:

- the `10.77.30.40/24` address and absence of a default route;
- Process Creation success auditing and command-line inclusion;
- PowerShell script-block logging;
- one benign child PowerShell execution;
- resulting Security 4688 and PowerShell Operational 4104 events.

Expected terminal result: `windows_phase2_validation=pass`.

## Persistence and isolation

Reboot each endpoint, rerun its validator, inspect persistent libvirt interfaces, and confirm that `pentest-provisioning` is inactive. A failed address, default-route, audit-policy, source-log, or synthetic-event check blocks phase completion.
