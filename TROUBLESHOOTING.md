# Troubleshooting

This guide treats the alert pipeline as a chain of independently testable boundaries. Start with the failing transaction, preserve its timestamp and alert identifier, and move outward one dependency at a time. Do not restart every service before collecting evidence.

## Standard triage sequence

1. Confirm the management VM and integration container are running.
2. Compare liveness (/health/live) with dependency readiness (/health/ready).
3. Inspect recent gateway logs for the service and sanitized category.
4. Validate the named dependency directly with its existing authenticated validator.
5. Check listener, route, DNS, certificate, credential-file metadata, and service logs in that order.
6. Correct only the isolated fault.
7. Inspect `/v1/deliveries/{key}`. Transient failures retry automatically; terminal failures require explicit analyst replay after readiness recovers.
8. Confirm the audit trail and incident disposition before closing the drill.

Useful management-VM commands:

~~~bash
docker inspect -f '{{.State.Health.Status}}' soc-integration-api
curl -fsS http://10.77.30.10:8010/health/ready | jq
docker logs --since 15m soc-integration-api
ss -lnt
ip route
~~~

The gateway records timeout, unavailable, authentication, and http_error categories. Retry logs include service, attempt number, maximum attempts, and bounded delay. They deliberately omit URLs, request bodies, credentials, and upstream response bodies.

## Failure runbooks

### P12-F01 — Threat-intelligence service unavailable

1. Identify: readiness is degraded and MISP reports unavailable; gateway logs show three bounded attempts.
2. Inspect: gateway logs, docker ps, MISP core and database health, and the telemetry listener on port 8443.
3. Isolate: call the MISP validator directly. If it fails while other dependencies pass, the fault is below the enrichment boundary.
4. Recover: restore the unhealthy MISP component and wait for its health check. The durable worker retries automatically; use analyst replay only if the record already reached terminal failed state.
5. Prevent: alert on sustained readiness degradation, retain bounded retries, and document MISP database recovery.

### P12-F02 — Malformed webhook

1. Identify: the producer receives HTTP 422 before the workflow runs.
2. Inspect: producer delivery logs and the FastAPI validation response; do not log the complete payload in production.
3. Isolate: compare required fields, timestamp timezone, value limits, and synthetic=true with the documented contract.
4. Recover: correct the producer mapping and resend with a new delivery key if the payload changed.
5. Prevent: validate fixtures in CI and version producer/consumer schemas.

### P12-F03 — API timeout

1. Identify: logs show category=timeout and the configured number of attempts.
2. Inspect: dependency latency, resource pressure, database health, and gateway timeout settings.
3. Isolate: distinguish a slow response from connection refusal by calling the dependency locally with a bounded timer.
4. Recover: remove the latency cause and replay only after readiness is healthy.
5. Prevent: measure latency percentiles, use explicit timeouts, and avoid unbounded retry storms.

### P12-F04 — Duplicate alert

1. Identify: HTTP 202 returns status=duplicate with response_action_executed=false.
2. Inspect: the delivery key, alert identifier, and webhook.received disposition in the audit log.
3. Isolate: determine whether it is a transport replay or a distinct alert that shares an incident fingerprint.
4. Recover: no platform repair is needed; retain the original receipt and close the replay.
5. Prevent: producers must reuse an idempotency key only for the exact same payload.

### P12-F05 — Incident platform unavailable

1. Identify: delivery status becomes retrying and logs show service=thehive category=unavailable.
2. Inspect: gateway logs, TheHive, Cassandra, Elasticsearch, and nginx health.
3. Isolate: validate TheHive directly. A healthy gateway and MISP with failed TheHive readiness places the fault at case handoff.
4. Recover: restore TheHive dependencies and confirm readiness. The worker releases the unfinished incident reservation before retrying; replay only a terminal failed delivery.
5. Prevent: monitor every stateful dependency, document startup ordering, and back up case data.

### P12-F06 — Endpoint disconnected

1. Identify: the last heartbeat exceeds the five-minute disconnected threshold.
2. Inspect: Velociraptor client status, Wazuh agent status, endpoint service state, telemetry interface, and host libvirt network.
3. Isolate: compare both collectors. If both are absent, investigate endpoint/network state; if one is absent, investigate that collector.
4. Recover: restore the telemetry path or restart only the approved lab collector, then confirm a fresh heartbeat.
5. Prevent: monitor heartbeat age separately from event volume and maintain service-restart procedures.

### P12-F07 — Malformed IOC

1. Identify: the candidate has a recognized IOC field name but fails IP, domain, URL, or hash validation.
2. Inspect: the normalized candidate type and invalid_format reason; avoid querying intelligence services with it.
3. Isolate: compare the value with source telemetry and parser field mapping.
4. Recover: correct the mapping or discard the candidate while retaining the source alert for analyst review.
5. Prevent: validate before enrichment and test malformed, empty, nested, and duplicate values.

### P12-F08 — Authentication failure between services

1. Identify: readiness or the pipeline reports authentication; HTTP status is retained internally as 401 or 403.
2. Inspect: credential-file ownership/mode, expected service account, recent rotation, and dependency authentication logs. Never print the secret.
3. Isolate: distinguish authentication from network failure by confirming the listener is reachable first.
4. Recover: restore or rotate the protected lab credential, restart only the consumer that loads it, and recheck readiness.
5. Prevent: monitor credential expiry, use distinct least-privilege accounts, and test rotation procedures.

## Escalation evidence

An analyst handoff should include the transaction timestamp, alert and incident identifiers, affected integration, sanitized error category, attempt count, readiness snapshot, relevant service health, actions already taken, and whether replay is safe. It must not include tokens, passwords, cookies, private keys, or raw forensic archives.

## Phase 13 monitoring checks

If the dashboard is empty, first query Prometheus target health and then the gateway metrics endpoint. A failed gateway target with a healthy container usually indicates listener, route, or scrape configuration. A healthy target with no changing counters usually indicates no new workflow traffic or a gateway restart.

If the Shuffle collection gauge is zero, inspect the gateway log and Shuffle API readiness. Collection is read-only and failure does not remove the gateway's other metrics.

If queue age grows, inspect delivery status before restarting anything. `retrying` indicates bounded automatic recovery; `failed` requires fault correction followed by `tools/soc_analyst.py replay <key>`. A Shuffle handoff held for reconciliation means the webhook may have been accepted without returning an execution identifier. Inspect Shuffle execution history by trace ID, then use `tools/soc_analyst.py reconcile-handoff`: choose `completed` with the observed execution ID, or `retry` only after confirming no execution exists. The approval-authenticated operation audits the decision and requeues the failed delivery; never trigger it blindly.

If Grafana is unhealthy, inspect Docker health and logs, verify that provisioning files are readable by the non-root container user, and confirm the Prometheus data source URL resolves on the Compose network. Do not weaken the observability secret-file mode.

If Prometheus rules are missing, validate prometheus.yml and rules.yml with promtool inside the pinned container, then restart only Prometheus. After any recovery, rerun /opt/soc-lab/observability/validate_observability.sh and confirm the management VM still has no default route.
