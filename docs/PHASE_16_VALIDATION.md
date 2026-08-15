# Phase 16 Validation

## Validation plan

1. Run shell syntax validation and the Phase 16 pytest controls.
2. Install the read-only snapshot on soc-mgr-01.
3. Run it against the live isolated stack.
4. Confirm healthy service, capacity, and no-default-route results.
5. Run the full repository lint, configuration, detection, link, and test suite.
6. Scan changed content for credential material and prohibited attribution.

Committed evidence is sanitized and contains only the snapshot's aggregate state. Runtime credentials, alert payloads, raw logs, and forensic data remain outside Git.
