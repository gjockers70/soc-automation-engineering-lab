# Phase 9 validation

Validated on the isolated `soc-mgr-01` Ubuntu Server VM on 2026-08-13.

## Automated tests

`python -m pytest -q` completed with 26 passing tests. Coverage includes nested IOC extraction, malformed IOC rejection, MISP normalization, unknown results, scoring, same-hour incident reuse, later-hour incident creation, webhook authentication, payload validation, delivery idempotency, rate-limit retry, timeout classification, and existing Phase 5–8 fixtures.

## Live integration

A synthetic failed-login alert containing RFC 5737 TEST-NET-2 address `198.51.100.44` produced:

- local-MISP reputation `suspicious`, confidence `75`;
- score `53`, severity `medium`;
- one TheHive case with an approval-required tag and one IP observable;
- `incident_disposition=created` for the first alert;
- `incident_disposition=reused` and the same case ID for a distinct matching alert;
- `status=duplicate` for a replay using the same delivery key and payload;
- `response_action_executed=false` throughout.

The authenticated readiness endpoint reported Wazuh, Shuffle, MISP, and TheHive healthy. The API was reachable only at `10.77.30.10:8010`, the secret file remained mode `0640`, and no default route was present.

## Recovery validation

The management VM was rebooted. Docker restarted the integration and platform containers. After stateful dependencies recovered, the complete live validation passed again, proving persistent gateway state, service restart behavior, MISP enrichment, TheHive creation, both duplicate controls, and continued network isolation.

Sanitized machine-readable evidence is stored in [`evidence/phase9-live-validation.json`](../evidence/phase9-live-validation.json).
