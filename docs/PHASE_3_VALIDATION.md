# Phase 3 validation procedure

Phase 3 was validated on August 13, 2026 before and after a controlled reboot of the manager and both endpoints.

## Manager checks

`docker/wazuh/validate_wazuh_manager.sh` verifies:

- all three Wazuh containers are running;
- the indexer cluster reports green;
- the dashboard responds over HTTPS;
- expected ports bind to `10.77.30.10` rather than all interfaces;
- no default route is present.

Expected result: `wazuh_manager_validation=pass`.

## Endpoint checks

The Linux and Windows Phase 3 validators verify the agent service, manager address, required log source, disabled active response, removal of the temporary endpoint enrollment-secret copy, and absence of a default route.

Expected results:

- `linux_phase3_validation=pass`
- `windows_phase3_validation=pass`

## Ingestion checks

`docker/wazuh/validate_phase3_ingestion.sh` requires both endpoint agents to be active and checks manager alert records for both supplied synthetic test markers.

Validated post-reboot result:

```text
active_agents=2
linux_synthetic_alert_records=6
windows_synthetic_alert_records=13
phase3_ingestion_validation=pass
wazuh_manager_validation=pass
indexer_status=green
dashboard_http_status=302
default_route=absent
service_bind_address=10.77.30.10
```

Counts describe matching JSON alert records at validation time, not unique incidents. Deduplication and incident creation are later workflow responsibilities.

## Isolation checks

- `pentest-provisioning` is inactive after installation.
- Each endpoint has only its original isolated workload NIC and persistent telemetry NIC.
- `dc01` and `kali-01` remained shut down.
- No endpoint, Wazuh service, or dashboard is exposed to the public Internet.
