# Phase 4 validation

Phase 4 was validated on August 13, 2026 against the isolated Linux and Windows endpoints.

## Static validation

`detections/validate.py` verifies required Sigma metadata and valid UUIDs, detection-condition references, unique Wazuh rule IDs in the custom range, Wazuh severity bounds and MITRE mappings, and one safe test event and documentation record per detection.

Wazuh accepted the XML through `wazuh-analysisd -t`. Official Sigma CLI 3.1.0 and pySigma 1.5.0 parsed all three rules with zero errors, condition errors, or validation issues. The Python and PowerShell files passed syntax parsing, and the shell files passed `bash -n` on the Ubuntu host.

## Live positive tests

After a clean manager restart, the supplied generators produced new endpoint events and the final validator reported:

```text
phase4_linux_test_events=6
phase4_windows_test_events=pass
soc1001_alert_records=2
soc1002_alert_records=13
soc1003_alert_records=4
phase4_detection_validation=pass
wazuh_manager_validation=pass
indexer_status=green
dashboard_http_status=302
default_route=absent
service_bind_address=10.77.30.10
```

Counts are cumulative matching alert records at final validation time. The minimum acceptance criterion is at least one matching record for every rule after its controlled test event.

Endpoint cleanup validators also passed: both Wazuh agents were running, neither endpoint had a default route, and neither temporary Windows validation identity remained.

Controlled negative tests also passed:

```text
soc1001_below_threshold=pass
soc1002_plain_powershell=pass
soc1003_machine_account_filter=pass
phase4_negative_validation=pass
```

These checks proved that four SSH failures remain below the correlation threshold, ordinary PowerShell without an encoded flag remains at the built-in process rule, and a machine-style account ending in `$` remains at the built-in account rule.

## Troubleshooting evidence

The first manager restart returned a running container while core Wazuh processes were incomplete and the API process had exited. This showed that container state alone was an insufficient readiness signal. Resource inspection showed ample memory and disk capacity and no kernel OOM record. A controlled restart restored all core services.

The installer was then changed to verify `wazuh-analysisd`, `wazuh-remoted`, `wazuh-db`, and `wazuh-apid` explicitly, permit one bounded recovery restart, and fail with recent logs if recovery does not succeed. A clean rerun passed on its initial start attempt.

## Negative and tuning boundary

Static fixtures and live negative controls cover the SSH threshold, machine-account exclusion, and required encoded-command structure. Broader false-positive measurement requires representative operational history; therefore all Sigma rules and detection records remain status `test` rather than claiming production maturity.
