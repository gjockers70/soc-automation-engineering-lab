# Phase 3 completion report

Phase 3 was completed and validated on August 13, 2026. Wazuh now receives and evaluates telemetry from one Linux and one Windows endpoint over the isolated `soc-telemetry` network.

## Validated result

| Capability | Result |
|---|---|
| Wazuh manager, indexer, and dashboard | Running at version 4.14.7 |
| Linux agent | Active as `ubuntu-web-01` |
| Windows agent | Active as `win11-01` |
| Enrollment authentication | Password required; secret remains outside Git |
| Linux alert proof | 6 records matching synthetic failed-logon address |
| Windows alert proof | 13 records matching temporary synthetic account |
| Indexer state | Green |
| Dashboard response | HTTPS redirect response received |
| Active response | Disabled centrally and on endpoints |
| Default routes | Absent after provisioning |
| Reboot persistence | Passed on manager and both endpoints |

## Alert path demonstrated

```text
Endpoint source event
  -> Wazuh agent
  -> isolated 1514/TCP transport
  -> Wazuh manager decoder and built-in rule
  -> alerts.json
  -> Wazuh indexer
  -> dashboard analyst view
```

This phase establishes ingestion, not custom detection engineering. Built-in Wazuh processing was used so Phase 4 can introduce documented custom Wazuh and Sigma detections without mixing the source, transport, and detection validation boundaries.

## Operational boundary

Wazuh services restart with the management VM, and both agents reconnect after their operating systems restart. A short connection failure while the manager starts is expected; agents retry and recover without operator action. Persistent alert records survive the reboot.

Temporary provisioning access was removed immediately after package installation. The lab remains local, isolated, non-destructive, and cost-free.
