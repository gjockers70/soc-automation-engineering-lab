# SOC platform observability

Phase 13 monitors the automation platform itself. The FastAPI gateway exposes bounded Prometheus metrics, Prometheus retains and evaluates them locally, and Grafana provides an analyst-facing dashboard.

## Data path

~~~text
Gateway counters and timings ---> Prometheus ---> Grafana
          |
          +-- read-only Shuffle execution summary
~~~

The metrics endpoint contains operational metadata only. It does not expose webhook tokens, platform credentials, full alerts, IOC values, incident identifiers, or analyst notes.

## Metrics

| Metric | Purpose |
|---|---|
| soc_alerts_received_total | Accepted and duplicate deliveries |
| soc_alerts_processed_total | Successful and failed pipeline outcomes |
| soc_webhook_rejections_total | Authentication, schema, and conflict rejections |
| soc_duplicate_suppression_total | Delivery- and incident-layer suppression |
| soc_incidents_total | Created, reused, and failed case handoffs |
| soc_api_failures_total | Sanitized dependency failure categories |
| soc_approval_decisions_total | Approved, rejected, escalated, and conflicted decisions |
| soc_enrichment_duration_seconds | Enrichment count and cumulative latency |
| soc_workflow_duration_seconds | End-to-end gateway workflow count and cumulative latency |
| soc_dependency_healthy | Current Wazuh, Shuffle, MISP, and TheHive readiness |
| soc_playbook_executions | Read-only Shuffle success, failure, and running counts |
| soc_playbook_execution_duration_seconds | Completed Shuffle execution count and cumulative duration |

Labels are defined in code and remain low-cardinality. Alert IDs, usernames, endpoints, indicators, and case IDs are deliberately excluded.

## Dashboard and alerts

The provisioned SOC Platform Overview dashboard contains eleven panels covering ingestion, processing, incident handoff, duplicates, dependency state, API failures, enrichment latency, workflow duration, Shuffle executions, and collection health.

Prometheus evaluates five local rules:

- integration gateway unavailable;
- a dependency reporting unhealthy;
- recent pipeline failures;
- playbook failure ratio above 20 percent;
- average enrichment latency above five seconds.

These rules are visible in Prometheus but are not connected to an external notification service. Phase 16 will document escalation and notification ownership.

## Access and retention

Prometheus binds to 127.0.0.1:9090. Grafana binds to 10.77.30.10:3000 on the isolated telemetry network and requires a generated local administrator credential. Use an SSH tunnel from the administrative workstation; do not publish either interface.

Prometheus retains seven days of data. Gateway counters reset when the gateway restarts; Prometheus counter semantics handle that reset while retained samples remain available. This single-node design demonstrates monitoring concepts but does not provide high availability.

## Validation

Run on soc-mgr-01:

~~~bash
/opt/soc-lab/observability/validate_observability.sh
~~~

The validator checks container health, scrape status, rule loading, Shuffle collection, Grafana authentication and dashboard provisioning, listener bindings, credential permissions, exact versions, and the absence of a default route.
