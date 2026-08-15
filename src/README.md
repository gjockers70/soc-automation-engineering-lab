# Python integration service

`soc_integration` is split by responsibility:

- `models.py`: validated alert and response contracts;
- `config.py`: typed environment configuration and secret fields;
- `integrations/`: retrying Wazuh, Shuffle, MISP, and TheHive clients;
- `idempotency.py`: durable duplicate suppression;
- `deliveries.py`: durable inbox, retry, replay, and Shuffle handoff reservations;
- `enrichment.py`: IOC extraction and normalized MISP results;
- `scoring.py`: deterministic triage score and severity;
- `reporting.py`: analyst-facing summaries;
- `incidents.py`: cross-alert incident fingerprint persistence;
- `pipeline.py`: enrichment-to-TheHive orchestration;
- `audit.py`: append-only structured audit events;
- `health.py`: concurrent dependency checks;
- `diagnostics.py`: deterministic endpoint-heartbeat health classification;
- `metrics.py`: bounded, dependency-free Prometheus exposition;
- `observability.py`: read-only Shuffle execution aggregation;
- `worker.py`: restart-safe MISP, TheHive, Shuffle, and approval processing;
- `triage.py`: analyst-initiated bounded triage records;
- `app.py`: authenticated FastAPI routes;
- `main.py`: deployment entry point.

Run locally with an ignored environment containing a generated `SOC_WEBHOOK_TOKEN`:

```bash
uvicorn soc_integration.main:app --app-dir src --host 127.0.0.1 --port 8010
```

Never place operational platform credentials in a command, fixture, log, or committed environment file.

The /metrics route is intentionally unauthenticated for local Prometheus scraping but is reachable only on the telemetry-bound gateway listener. Metric label names and values are constrained in code; event-specific and secret data is excluded.

## Approval service

`soc_integration.approvals` stores incident-linked proposals and analyst decisions in SQLite. The API uses a separate approval token and exact Pydantic action/target literals. Only approval can invoke the application-level synthetic identity state change; rejection and escalation are audit-only outcomes.

Use `tools/soc_analyst.py` with `SOC_APPROVAL_TOKEN` supplied through the environment to list proposals, decide them, replay terminal failed deliveries, and record bounded triage requests. The credential is never accepted as a command-line argument.
