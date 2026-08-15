# Corrective alert-lifecycle implementation

## Objective

This corrective release closes the repository gap between independently validated components and an automatic endpoint-to-analyst lifecycle. It retains the Python gateway as the authoritative processing layer and uses Shuffle for authenticated analyst handoff.

## Implemented repository path

```text
Wazuh allow-listed custom integration
  -> durable authenticated gateway intake
  -> background retry worker
  -> local MISP enrichment and deterministic score
  -> TheHive case create or reuse
  -> scenario-specific Shuffle webhook
  -> idempotent pending approval when required
  -> separately authenticated analyst decision
  -> exact synthetic response allow list
```

The Wazuh adapter accepts only the three repository-owned rule IDs and requires the `soc_lab` group. It derives a deterministic idempotency key, never places the token on a command line, and spools failed deliveries locally with restricted permissions.

The gateway persists the canonical payload before acknowledging it. A worker claims records atomically, retries bounded failures, returns interrupted work to the queue after restart, and exposes terminal failures for explicit replay. Delivery idempotency and incident deduplication remain separate controls.

Shuffle receives only the normalized handoff result: trace ID, alert ID, incident ID, scenario, score, severity, indicators, summary, and approval requirement. Account-activity processing creates one pending proposal per trace. Shuffle cannot approve its proposal and no generic response executor exists.

Bounded triage requests are analyst-initiated records tied to a TheHive incident. The API enforces endpoint-to-collection matching. Raw Velociraptor results remain outside Git and an analyst supplies only a sanitized completion summary.

## Validation boundary

Local and CI validation use synthetic fixtures, mocked vendor APIs, temporary SQLite state, and no operational credentials. This proves the repository logic but not deployment. Live completion requires the separately authorized procedure in [CORRECTIVE_LIVE_VALIDATION.md](CORRECTIVE_LIVE_VALIDATION.md).
