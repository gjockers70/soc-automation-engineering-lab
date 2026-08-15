# API and webhook engineering

The FastAPI gateway at `10.77.30.10:8010` separates event intake from platform credentials and downstream processing. The original Phase 8 and Phase 9 behavior is preserved in historical phase documents; the current contract uses durable asynchronous delivery.

## Implemented request contract

`POST /v1/webhooks/wazuh` requires:

- a valid Wazuh-style JSON alert;
- `synthetic: true`;
- an exact `X-SOC-LAB-TOKEN` value;
- an `Idempotency-Key` between 8 and 128 characters.

A new request is persisted before HTTP 202 is returned with `status: accepted`, `processing_status: queued`, a trace ID, and a status URL. Replaying the same key and canonical payload returns HTTP 202 with `status: duplicate`. Reusing a key for different content returns HTTP 409. Missing authentication returns HTTP 401 and malformed input returns HTTP 422.

`GET /v1/deliveries/{idempotency_key}` reports queued, processing, retrying, completed, or failed state. Only terminal failed deliveries can be explicitly replayed, using the separate analyst credential.

## Integration clients

The Wazuh, Shuffle, MISP, and TheHive clients use explicit timeouts, bounded retry attempts, capped `Retry-After` handling, and sanitized error categories. Authentication failures are distinguished from timeouts, availability failures, and other HTTP errors without returning credentials or raw upstream bodies.

`GET /health/ready` checks the authenticated APIs concurrently and reports per-service status and latency. `GET /health/live` reports process health only.

## Durable processing and audit

SQLite persists the canonical payload, delivery state, retry schedule, incident result, and Shuffle handoff reservation. Interrupted processing returns to the queue after restart. Bounded exponential retries end in a visible failed state instead of silently discarding the alert. An append-only JSON Lines file records authentication, queue, incident, Shuffle, approval, and recovery events without authentication material or full payloads.

See [docs/PHASE_8_IMPLEMENTATION.md](docs/PHASE_8_IMPLEMENTATION.md) and [src/README.md](src/README.md).

## Current composition

The background worker composes MISP and TheHive behind the durable request contract. Completed delivery status includes score, severity, incident ID, create/reuse disposition, scenario, and Shuffle execution ID. Delivery duplicates do not rerun enrichment or case creation.

After TheHive handoff, the gateway invokes the scenario-specific authenticated Shuffle webhook. A trace reservation prevents automatic duplicate workflow invocation. Account-activity completion idempotently creates a pending approval proposal; it does not approve or execute it. Upstream errors are classified, sanitized, retried, measured, and retained for analyst replay.

An ambiguous Shuffle POST is never retried automatically. After checking Shuffle execution history by trace ID, an analyst uses the approval-authenticated handoff-reconciliation endpoint to record either the observed execution ID or a verified safe-to-retry decision. The gateway audits the note and requeues the failed delivery with a fresh bounded attempt budget.

See [AUTOMATED_ENRICHMENT.md](AUTOMATED_ENRICHMENT.md) and [docs/PHASE_9_IMPLEMENTATION.md](docs/PHASE_9_IMPLEMENTATION.md).
