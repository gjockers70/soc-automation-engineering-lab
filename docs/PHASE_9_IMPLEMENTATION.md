# Phase 9 implementation

## What was built

The FastAPI gateway now composes IOC extraction, local MISP lookup, normalized enrichment, deterministic scoring, analyst summaries, incident fingerprinting, and TheHive case/observable creation.

The Python responsibilities remain separated:

- `enrichment.py`: validation, extraction, MISP response normalization
- `scoring.py`: deterministic risk score and TheHive severity mapping
- `reporting.py`: concise analyst summary
- `incidents.py`: durable one-hour cross-alert fingerprint reservations
- `pipeline.py`: orchestration and case handoff
- `integrations/`: retrying vendor API clients

## Why a SOC uses it

Enrichment reduces repetitive lookups, consistent scoring makes triage factors visible, deduplication prevents case flooding, and a structured handoff gives analysts evidence without granting automation authority to contain an endpoint or account.

## Deployment architecture

The Phase 9 container is an offline incremental image based on the locally retained Phase 8 gateway image. The dependency set did not change, so only application source is layered into `soc-integration-gateway:phase9`. This avoids reopening Internet access in the isolated management VM and keeps rollback available through the Phase 8 image.

Runtime state remains in `/opt/soc-lab/integration-state`; credentials remain in `/opt/soc-lab/secrets/integration.env` with mode `0640`. The API binds only to `10.77.30.10:8010`.

## Safety

Only `synthetic: true` alerts are accepted. The pipeline creates or reuses a case and adds observables, but it cannot disable accounts, block addresses, quarantine hosts, or execute endpoint commands.
