# SOC Lab Operations Runbook

This is the operator entry point for the isolated SOC automation lab. It describes a production-style operating model, but it does not claim that the single-node lab is staffed or available 24x7.

## Start of session

1. Confirm the mini-PC and soc-mgr-01 are reachable through the approved administration path.
2. Run sudo /opt/soc-lab/operations/health_snapshot.sh on soc-mgr-01.
3. Treat a nonzero result as degraded and use the named failed checks to select a recovery procedure.
4. Review Prometheus rules and the Grafana SOC Platform Overview dashboard.
5. Confirm no response proposal is awaiting an analyst decision before maintenance.
6. Confirm `soc_delivery_queue_items{status="failed"}` is zero and the oldest pending delivery is below the documented threshold.

## Operating procedures

| Need | Procedure |
|---|---|
| Determine impact and priority | [Escalation](operations/ESCALATION.md) |
| Understand dependency order | [Service dependencies](operations/SERVICE_DEPENDENCIES.md) |
| Interpret health and thresholds | [Health checks](operations/HEALTH_CHECKS.md) |
| Recover a failed integration | [Failure recovery](operations/FAILURE_RECOVERY.md) |
| Protect and restore lab state | [Backup and recovery](operations/BACKUP_RECOVERY.md) |
| Plan and record a change | [Change management](operations/CHANGE_MANAGEMENT.md) |
| Perform scheduled care | [Maintenance](operations/MAINTENANCE.md) |
| Transfer investigation context | [Shift handoff](operations/SHIFT_HANDOFF.md) |
| Rehearse known failure modes | [Failure scenario register](operations/FAILURE_SCENARIOS.md) |
| Operate approvals and bounded triage | `tools/soc_analyst.py` with environment-provided credentials |
| Deploy and validate the corrective lifecycle | [Corrective live validation](docs/CORRECTIVE_LIVE_VALIDATION.md) |

## Stop conditions

Stop automation and preserve evidence when an action lacks approval, the target is outside the lab allow list, a secret may have been exposed, data integrity is uncertain, or an unexpected default route appears. Do not improvise containment. Escalate, record the decision, and recover from a known-good state.

## Records

Operational records capture UTC time, operator, affected service, symptoms, commands run, decision or approval, result, and follow-up owner. Never copy credentials, raw forensic archives, complete alert payloads, or real personal data into Git.
