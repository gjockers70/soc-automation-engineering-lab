# Operations

The operations directory contains repeatable procedures for running and troubleshooting the SOC automation platform. Phase 12 added a non-destructive failure lab. Phase 16 adds:

- [Escalation and severity](ESCALATION.md)
- [Service dependencies](SERVICE_DEPENDENCIES.md)
- [Health checks](HEALTH_CHECKS.md)
- [Failure recovery and safe replay](FAILURE_RECOVERY.md)
- [Backup and restore](BACKUP_RECOVERY.md)
- [Change management](CHANGE_MANAGEMENT.md)
- [Maintenance](MAINTENANCE.md)
- [Shift handoff](SHIFT_HANDOFF.md)

The root [operator runbook](../RUNBOOK.md) routes tasks to these procedures. health_snapshot.sh provides a sanitized, non-mutating JSON snapshot on soc-mgr-01.

The failure lab uses real authenticated gateway requests only for malformed-schema and duplicate-delivery behavior. Dependency outages and latency use local httpx transports, and endpoint disconnection uses an expired synthetic heartbeat. No platform service or endpoint collector is stopped.

Run locally without a gateway:

~~~bash
PYTHONPATH=src python operations/failure-lab/run_phase12_drills.py --offline
~~~

On soc-mgr-01, docker/integration/validate_phase12.sh runs all eight scenarios inside the hardened gateway container, writes the private detailed result to the persistent integration volume, checks steady-state readiness, and proves the default route remains absent.

Prometheus scrapes the gateway every 15 seconds and evaluates seven rules, including durable-queue age and terminal failure state; Grafana provisions the SOC Platform Overview dashboard. Run `/opt/soc-lab/observability/validate_observability.sh` to verify health, scrape status, rules, dashboard provisioning, listener scope, secret permissions, versions, and isolation.
