# Phase 5 validation record

Validation date: August 13, 2026

## Platform evidence

| Check | Observed result | Status |
|---|---|---|
| Official source pin | `223b675c4480730832f928e113b6f2e5260b450d` | Pass |
| MISP API version | `2.5.44` | Pass |
| Core services | DB, Redis, MISP modules, and MISP core running | Pass |
| Worker profile | One default, priority, email, update, and cache worker | Pass |
| Bind address | `10.77.30.10:8080` and `10.77.30.10:8443` | Pass |
| Runtime secret mode | `0640`, `root:docker` | Pass |
| Steady-state default route | Absent | Pass |
| Provisioning network | Stopped after image pull | Pass |
| Management VM headroom | 8.1 GiB memory available; 55 GiB disk free | Pass |
| Existing monitoring continuity | Linux and Windows Wazuh agents active | Pass |

Final validator output:

```text
misp_version=2.5.44
misp_validation=pass
default_route=absent
service_bind_address=10.77.30.10
```

## Intelligence evidence

The first seed created event ID 1 and four attributes:

```json
{"created": 4, "event_id": "1", "existing": 0}
```

The immediate repeat suppressed duplicates:

```json
{"created": 0, "event_id": "1", "existing": 4}
```

Live enrichment returned local-MISP matches for the IP, domain, URL, and SHA-256 fixtures with the expected controlled confidence values. A lookup of `unknown.test` returned no sources, unknown reputation, and confidence zero.

## Negative controls

- A malformed domain is rejected before network access.
- An invalid-length hash is rejected before network access.
- A valid but absent indicator is not treated as benign.
- The fixture metadata cannot claim reputation unless MISP returns a matching attribute.
- No external feed, public service, paid API, block action, account action, or quarantine action was used.

## Unit evidence

Five local unit tests passed for indicator validation, hash-type mapping, known-result normalization, and unknown-result normalization. Python bytecode compilation also passed for all three Phase 5 scripts.
