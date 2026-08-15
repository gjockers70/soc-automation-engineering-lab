# Phase 3 implementation

## Why the SOC needs this layer

Phase 2 proved that each operating system creates useful security records. Phase 3 adds the collection and SIEM boundary: endpoint agents securely enroll with a central manager, forward selected sources, and allow Wazuh decoders and built-in rules to turn events into searchable alert records.

This separation supports a practical troubleshooting sequence: source event, agent health, transport, manager decoding, rule match, index state, and dashboard access.

## Component layout

| Component | Location | Responsibility |
|---|---|---|
| Wazuh manager 4.14.7 | `soc-mgr-01` container | Agent enrollment, event decoding, rule evaluation, alert creation |
| Wazuh indexer 4.14.7 | `soc-mgr-01` container | Alert storage and search |
| Wazuh dashboard 4.14.7 | `soc-mgr-01` container | Analyst interface |
| Wazuh Linux agent 4.14.7 | `ubuntu-web-01` | Authentication and Linux Audit collection |
| Wazuh Windows agent 4.14.7 | `win11-01` | Security and PowerShell event-channel collection |

All published service ports bind only to `10.77.30.10`. The management VM and both endpoints have no default route in steady state.

## Supply-chain and secret controls

- The Docker deployment and both agents are pinned to 4.14.7.
- The Linux package is checked against SHA-512 metadata published by the Wazuh package repository.
- The Windows MSI must have a valid Authenticode signature from a publisher containing `Wazuh`.
- Manager, indexer, dashboard, API, and enrollment credentials are generated on the management VM.
- The enrollment password is copied directly between guests through QEMU Guest Agent file APIs. It is not printed, placed on the virtualization host, or committed, and the endpoint copy is deleted after successful enrollment.
- Default credential strings are rejected by the preparation validator.

## Enrollment and collection

Enrollment uses port 1515/TCP with password authentication. Agent event transport uses port 1514/TCP. The Linux agent adds `/var/log/audit/audit.log` using Wazuh's `audit` log format; its default configuration also collects relevant system and authentication sources. The Windows agent retains the standard Security, System, and Application channels and adds `Microsoft-Windows-PowerShell/Operational` as an `eventchannel` source.

Active response is disabled at the manager and on each endpoint. Phase 3 produces alerts but cannot disable accounts, block addresses, or run containment commands.

## Safe validation events

- Linux emits six synthetic `sshd` failure messages using documentation-only address `198.51.100.23`.
- Windows executes a harmless PowerShell marker and creates, disables, and immediately removes a temporary local identity named `soc_phase3_test` with a random lab-only password.

The temporary Windows identity exists only long enough to generate native account-management telemetry. The resulting records prove the complete endpoint-to-manager alert path without malware, public targets, or real credentials.

## Troubleshooting order

1. Confirm the source event exists on the endpoint.
2. Confirm the Wazuh agent service is running and its manager address is `10.77.30.10`.
3. Inspect endpoint `ossec.log` for enrollment or transport errors.
4. Confirm 1514/TCP and 1515/TCP bind only to the telemetry address.
5. Use `agent_control -lc` inside the manager container to confirm agent state.
6. Inspect manager `ossec.log` and `alerts.json` for decoder or rule results.
7. Check container health, indexer cluster state, then dashboard access.

This order isolates failures instead of restarting the entire stack before identifying the broken layer.
