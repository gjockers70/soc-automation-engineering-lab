# Phase 7 implementation

## What was built

Shuffle 2.2.1 was deployed on `soc-mgr-01` with pinned frontend, backend, Orborus, worker, and OpenSearch images. The UI binds to `10.77.30.10:3001`; the backend binds to loopback; OpenSearch is container-internal.

Four idempotently seeded workflows cover suspicious login, suspicious file, suspicious domain, and account activity. Each begins with an authenticated webhook and captures the synthetic execution argument for analyst handoff. The account workflow carries a mandatory approval requirement, and no workflow contains a response action.

## Why a SOC uses it

SOAR provides a controlled coordination layer between alert sources, enrichment services, case systems, and analysts. Phase 7 establishes the trigger, execution history, authentication, repeatability, and governance boundary before integrations add consequential complexity.

## Architecture decision

The host Docker daemon enables live-restore, which cannot enter swarm mode. Shuffle's default swarm initialization therefore failed. The deployment explicitly sets standalone worker mode, which creates an isolated worker container per execution and was validated with all four workflows. This single-node lab design is not production high availability.

The Compose deployment mounts the Docker socket because Shuffle launches worker and app containers. Anyone controlling the Shuffle backend or Orborus therefore crosses a high-trust boundary; access is restricted to the isolated management VM and generated credentials.

## Deferred integration

Wazuh webhook delivery, MISP lookup, alert scoring, deduplication, TheHive API calls, analyst approval records, and lab-only response execution are intentionally deferred to Phases 8-10. Phase 7 does not claim those connections are live.
