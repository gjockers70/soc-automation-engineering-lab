# SOAR Playbooks

The corrective lifecycle defines five authenticated Shuffle workflows for gateway-to-analyst handoff. The fifth is a safe fallback for validated alerts without a narrower scenario mapping.

| Playbook | Gateway result | Workflow outcome | Safety gate |
|---|---|---|---|
| Suspicious Login | scored incident and normalized indicators | validate and record analyst handoff | notify only |
| Suspicious File | scored incident and normalized indicators | validate and record analyst handoff | recommend only |
| Suspicious Domain | scored incident and normalized indicators | validate and record analyst handoff | notify only |
| Account Activity | scored incident and approval requirement | validate, hand off, record approval requirement | explicit approval required |
| General Security Alert | validated fallback incident | validate and record analyst handoff | notify only |

## Implemented boundary

The repository candidate uses this graph: authenticated gateway webhook -> validate structured result -> record analyst handoff -> record approval requirement when applicable. The Python pipeline performs MISP enrichment, scoring, deduplication, TheHive case creation, durable retries, and proposal creation. The only response remains an application-level synthetic identity state change.

The account-activity response flow is: incident -> proposal -> pending approval -> approve/reject/escalate. Only approve enters the exact allow-listed executor. The approval and automation credentials are distinct, and every branch records an audit event.

Webhook callers must send the runtime `X-SOC-LAB-TOKEN` header. Re-running the seed script creates missing workflows and updates existing workflows by stable name through Shuffle's pinned `PUT /api/v1/workflows/{id}` route. Runtime webhook URLs are written to protected state and then assembled into the gateway environment.

These updated graphs and the gateway-triggered handoff are locally validated but are not represented as live until the procedure in [docs/CORRECTIVE_LIVE_VALIDATION.md](docs/CORRECTIVE_LIVE_VALIDATION.md) passes on the isolated lab.

See [playbooks/README.md](playbooks/README.md) for the operator workflow and [docs/PHASE_7_VALIDATION.md](docs/PHASE_7_VALIDATION.md) for evidence.
