# Phase 2 completion report

Phase 2 was validated on August 13, 2026. Two existing owned lab systems now produce security-relevant endpoint telemetry on a dedicated, isolated management network.

## Validated endpoint state

| Check | Linux endpoint | Windows endpoint |
|---|---|---|
| VM | `ubuntu-web-01` | `win11-01` |
| Telemetry address | `10.77.30.20/24` | `10.77.30.40/24` |
| Original lab address retained | `10.77.20.20/24` | `10.77.20.40/24` |
| Default route | Absent | Absent |
| Authentication source | `/var/log/auth.log` and journal | Security event log |
| Process source | Linux Audit `execve` | Security event ID 4688 with command lines |
| Privilege/account source | Audit watches for identity and sudo policy files | Account and security-group management audit categories |
| PowerShell source | Not applicable | Operational log with module and script-block logging |
| Benign validation evidence | Audit key `soc_test_file` | Event IDs 4688 and 4104 |
| Reboot persistence | Passed | Passed |

## Network and host evidence

- Both VMs have persistent second interfaces on `soc-telemetry`.
- The management VM reached the Linux endpoint with 0% packet loss.
- Windows did not answer ICMP, consistent with its firewall policy, but its telemetry MAC was `REACHABLE` in the management VM neighbor table.
- `pentest-provisioning` was stopped after the Linux `auditd` package installation.
- `dc01` and `kali-01` remained shut down and unchanged.
- Endpoint and network autostart remain disabled.
- The host retained approximately 40 GiB available memory and 266 GB free storage with the management and two endpoint VMs running.

## Security concept

Endpoint monitoring begins with trustworthy event sources. Linux records authentication and sudo activity in text and journal sources while Audit supplies syscall and file-watch records. Windows uses structured event channels and policy-controlled audit subcategories. The collection layer must preserve those platform differences while normalizing their meaning later in the alert pipeline.

No Wazuh agent or central ingestion was installed in this phase. Forwarding and manager-side validation belong to Phase 3.

## Rollback boundary

Phase 2 rollback removes only the added `soc-telemetry` interfaces, the endpoint-specific logging configuration, and the Linux `auditd` package if removal is intentionally approved. Original endpoint disks, recovery copies, `pentest-isolated` interfaces, applications, and unrelated VMs are outside the rollback scope.
