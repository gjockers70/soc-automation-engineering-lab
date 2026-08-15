# Automated testing

The current suite is designed around operational boundaries rather than implementation trivia. It uses mocked HTTP transports, temporary SQLite databases, temporary audit files, synthetic alerts, TEST-NET addresses, and reserved `.test` domains.

## Test layers

| Layer | What is verified |
|---|---|
| Webhook contract | Authentication, schema validation, timezone, synthetic-only scope, idempotency, conflict handling, and safe receipts |
| IOC processing | Nested extraction, IP/domain/URL/hash validation, deduplication, malformed candidates, MISP shapes, bounded metadata, and unknown results |
| Scoring and reporting | Deterministic factors, severity thresholds, score caps, TheHive severity mapping, and analyst safety language |
| API clients | Exact Wazuh, Shuffle, MISP, and TheHive request methods, paths, authentication, bodies, response normalization, timeouts, rate limits, retries, and errors |
| Incident handling | Fingerprints, reservation state, release after failure, existing-case reuse, observable creation, and missing case identifiers |
| Approval control | Separate credentials, schema allow lists, immutable decisions, idempotent approval, reject/escalate behavior, and fail-closed stored-record validation |
| Operations | Concurrent audit integrity, dependency health states, failure drills, metrics exposition, dashboard assets, and forensic evidence structure |
| Configuration | Required secrets, redacted representation, URL and numeric bounds, TLS parsing, and safe defaults |
| Completed lifecycle | Native Wazuh mapping, durable queue recovery, Shuffle handoff, idempotent proposals, bounded triage, replay, and queue observability |

## Run locally

Create a virtual environment, install the pinned runtime and development requirements, then run:

~~~bash
python -m pytest
~~~

Collect the inventory without executing tests:

~~~bash
python -m pytest --collect-only
~~~

The pytest configuration enables strict configuration and strict marker validation. The suite must not require network access or operational credentials. Phase 15 runs these same tests in GitHub Actions using mocks only.

## Failure interpretation

A test failure blocks the phase or change being validated. Do not rewrite an assertion merely to make a failure disappear. Determine whether the failure represents a product defect, an outdated contract, a bad fixture, or an environment problem; correct the appropriate layer and rerun the complete suite.

Generated coverage and JUnit files are excluded from Git. Sanitized completion evidence records only the test count, duration class, categories, and result.
