# Failure Recovery

## Recovery principles

Diagnose before restarting. Preserve the source alert, idempotency key, incident fingerprint, audit event, and approval state. Never convert an enrichment failure into a benign verdict. Never replay a consequential action solely because a workflow timed out.

## Standard sequence

1. Run the health snapshot and note UTC time and failed checks.
2. Bound impact: ingestion, enrichment, case creation, workflow, triage, or observability.
3. Check dependencies in [service order](SERVICE_DEPENDENCIES.md).
4. Inspect only recent, relevant logs and redact sensitive fields.
5. Correct the narrow root cause or restore a known-good configuration.
6. Run the component validator and health snapshot.
7. Replay one synthetic item with its original idempotency key.
8. Confirm no duplicate case, decision, or response action was produced.
9. Record recovery, residual risk, and prevention action.

## Failure procedures

| Symptom | Isolate | Recover and validate |
|---|---|---|
| Malformed webhook | Compare schema error and sender version; do not edit in transit | Correct sender mapping; replay a synthetic fixture |
| Authentication failure | Confirm permissions and key name without printing the value | Rotate locally; verify rejected old and accepted new credential |
| MISP timeout/unavailable | Check core, database, cache, and bounded error | Restore dependency; retry; retain unknown until success |
| TheHive unavailable | Check proxy, app, Cassandra, Elasticsearch | Restore in order; replay same fingerprint; verify one case |
| Duplicate alert | Compare idempotency key and content digest | Accept exact replay; reject conflicting key reuse |
| Shuffle execution fails | Inspect execution ID and failing node | Fix node; replay once; verify downstream deduplication |
| Endpoint disconnected | Check VM, telemetry interface, agent, and last-seen time | Restore collection; do not fabricate backfill evidence |
| Observability unavailable | Use direct health endpoints and logs | Restore Prometheus before Grafana; verify targets and rules |

## Failed-playbook queue

The lab uses durable local state and idempotent replay rather than a production message broker. Record failed execution ID, source alert ID, idempotency key, last completed step, error class, retry count, next attempt, and approval state. Apply bounded exponential backoff. After the retry limit, move the item to manual review; never loop indefinitely.

An approved response with an unknown execution result must be reconciled against the lab target and audit log before retry. Reject and escalate branches are never converted to approval.

## Recovery boundaries

Restart commands and data restores are manual, scoped changes requiring prechecks and rollback. Do not delete volumes, reset databases, regenerate credentials, or restore a VM recovery copy merely to clear an error. Follow [backup and recovery](BACKUP_RECOVERY.md) for integrity failures.
