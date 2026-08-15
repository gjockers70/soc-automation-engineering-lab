# Service Dependencies

## Dependency map

| Capability | Direct dependencies | Downstream impact if unavailable |
|---|---|---|
| Wazuh alerting | Manager, indexer, dashboard, endpoint agents | New detections stop or become unavailable for search |
| Integration gateway | Configuration, audit/state volume, webhook input | Normalization, enrichment, scoring, deduplication, and case automation stop |
| MISP enrichment | Core, MariaDB, Valkey, modules | Reputation becomes unknown; alerts must not be marked safe |
| TheHive cases | TheHive, Cassandra, Elasticsearch, nginx | Case creation stops; alerts remain queued for safe replay |
| Shuffle workflows | Frontend, backend, Orborus, OpenSearch, worker path | SOAR execution and history become unavailable |
| Velociraptor triage | Native server, client enrollment, datastore | Live-response gathering stops; detection continues |
| Observability | Gateway metrics, Prometheus, Grafana | Failures become less visible; processing can continue |

## Logical flow

Endpoint -> Wazuh -> gateway/Shuffle -> MISP -> scoring -> TheHive -> analyst approval -> lab-only action -> audit

Velociraptor is an analyst-invoked investigation branch. Prometheus and Grafana observe the flow and never authorize response.

## Start order

1. Management VM networking and Docker engine.
2. Datastores: Wazuh indexer, MariaDB/Valkey, Cassandra/Elasticsearch, Shuffle OpenSearch.
3. Core platforms: Wazuh, MISP, TheHive/nginx, Shuffle.
4. Integration gateway.
5. Velociraptor server and enrolled clients.
6. Prometheus and Grafana.
7. Endpoint VMs and telemetry generators.

Wait for each layer to become ready before starting consumers. Reverse shutdown order reduces incomplete writes. VM restart remains operator-controlled; the health snapshot never performs it.

## Failure behavior

| Dependency failure | Required behavior |
|---|---|
| MISP unavailable or times out | Return unknown, lower confidence, record error, retry with bounds |
| TheHive unavailable | Release unfinished reservation and retry with the same incident fingerprint |
| Shuffle unavailable | Preserve source alert and idempotency key; never bypass approval |
| Endpoint disconnected | Mark evidence stale; do not infer compromise or health |
| Prometheus/Grafana unavailable | Use logs and direct checks; repair visibility promptly |

The lab is intentionally single-node. Production would add redundant workers and datastores, durable queues, external monitoring, independent backups, and tested failover.
