# Test matrix

All tests are safe to run on a disconnected workstation. Vendor calls use httpx MockTransport; persistence uses disposable temporary paths.

| File | Primary scope |
|---|---|
| test_integration_gateway.py | Webhook authentication, validation, idempotency, retry foundations |
| test_enrichment_scoring.py | IOC normalization and deterministic scoring |
| test_phase9_pipeline.py | TheHive creation and cross-alert case reuse |
| test_approvals.py | Human decision branches and credential separation |
| test_phase11_forensics.py | Sanitized forensic artifact contracts |
| test_phase12_failure_handling.py | Eight controlled failure scenarios |
| test_phase13_observability.py | Metrics exposition and Shuffle aggregation |
| test_phase13_stack.py | Prometheus/Grafana configuration and dashboard assets |
| test_phase14_configuration_contracts.py | Configuration bounds, models, all IOC types, metadata, scoring boundaries |
| test_phase14_api_clients.py | Mocked vendor request contracts and retry classifications |
| test_phase14_pipeline_resilience.py | Reservation recovery, health, audit concurrency, fail-closed approval |
| test_phase16_operations.py | Required runbooks, operating concepts, read-only health checks, isolation and capacity boundaries |
| test_phase17_portfolio.py | Required documentation, portfolio sections, commercial mapping, honest gaps, diagram consistency |
| test_misp_common.py | Standalone local-MISP helper behavior |
| test_shuffle_playbooks.py | Workflow fixtures, authentication, and no automatic response |
| test_completed_lifecycle.py | Wazuh mapping, durable retry/replay, Shuffle handoff, idempotent approval, bounded triage, and fallback routing |
| test_thehive_case.py | Synthetic case fixture and approval-gated task state |

The shared conftest supplies only synthetic alert and temporary configuration factories. It does not load a repository environment file.
