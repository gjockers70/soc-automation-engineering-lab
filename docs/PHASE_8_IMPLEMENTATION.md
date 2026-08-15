# Phase 8 implementation

## What was built

A containerized FastAPI integration gateway now runs on `soc-mgr-01`. It receives authenticated synthetic alerts, validates a typed Pydantic contract, suppresses duplicates in SQLite, records JSON audit events, and checks authenticated Wazuh, Shuffle, MISP, and TheHive APIs.

The container runs as UID 10001 with all Linux capabilities dropped, a read-only root filesystem, `no-new-privileges`, a bounded temporary filesystem, a 256 MiB memory limit, and telemetry-only binding. Runtime credentials are assembled from the existing protected service files into `/opt/soc-lab/secrets/integration.env`; they are not committed or printed.

## Why a SOC uses it

An integration gateway gives producers and consumers a stable contract even when vendor APIs differ. Authentication, validation, retries, rate-limit handling, error classification, idempotency, and auditing are centralized instead of being reimplemented inconsistently in each playbook.

## Alert flow in this phase

```text
Synthetic Wazuh-style alert
  -> authenticated FastAPI webhook
  -> Pydantic validation
  -> durable idempotency decision
  -> structured audit receipt
  -> safe handoff boundary
```

The clients prove connectivity and reusable API behavior. Phase 8 does not yet call MISP search, calculate risk, or create a TheHive case during webhook processing. Those workflow changes belong to Phase 9.

## Commercial platform mapping

The gateway demonstrates the API-contract, credential, retry, and webhook engineering needed when connecting SOAR and intelligence products. Shuffle supplies the open-source orchestration surface; the reusable client boundary transfers to commercial workflow products such as Tines. MISP client concepts transfer to threat-intelligence platforms such as ThreatQ, without claiming feature equivalence.
