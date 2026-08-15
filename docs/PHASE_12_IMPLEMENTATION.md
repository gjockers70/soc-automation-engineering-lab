# Phase 12 implementation

## What was built

Phase 12 adds a repeatable failure-drill harness, structured retry and terminal-failure logging, explicit malformed-IOC diagnostics, deterministic endpoint-heartbeat classification, eight analyst runbooks, automated tests, and a hardened Phase 12 gateway image.

Two drills use the live authenticated gateway: malformed schema rejection and duplicate-delivery suppression. Connection refusal, timeout, TheHive unavailability, and service authentication use local httpx transports. Endpoint disconnection uses a ten-minute-old synthetic heartbeat. Malformed IOCs use reserved or intentionally invalid values. This design exercises error paths without stopping any real platform service or endpoint collector.

## Why a SOC uses it

Reliable automation must fail predictably. Operators need to know whether a transaction failed at intake, validation, enrichment, incident handoff, endpoint collection, or authentication. Bounded retries prevent transient faults from becoming immediate incidents while terminal categories, readiness, and audit records make persistent faults actionable.

## Architecture

~~~text
Synthetic drill
  -> live gateway or local dependency substitute
  -> bounded retry / validation / heartbeat classifier
  -> sanitized failure category
  -> analyst isolation sequence
  -> verified recovery boundary
  -> audit evidence; no response action
~~~

The live integration image remains non-root, read-only, capability-free, resource-bounded, and telemetry-only. Persistent state and credentials remain outside Git.

## Job-skill mapping

The phase demonstrates troubleshooting across API, schema, authentication, network, dependency, idempotency, and endpoint-health boundaries. It also demonstrates repeatable failure injection, structured logging, safe replay decisions, recovery validation, and operational documentation expected when maintaining security operations integrations.
