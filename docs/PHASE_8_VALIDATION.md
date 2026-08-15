# Phase 8 validation

Validation used only a synthetic alert and reserved TEST-NET data.

| Check | Result |
|---|---|
| Local repository tests | 21 passed |
| Container health | Healthy |
| Wazuh authenticated API | Healthy |
| Shuffle authenticated API | Healthy |
| MISP authenticated API | Healthy |
| TheHive authenticated API | Healthy |
| Missing webhook token | HTTP 401 |
| Valid synthetic alert | HTTP 202, accepted |
| Exact replay | HTTP 202, duplicate |
| Key reused for different payload | HTTP 409 in unit test |
| Malformed payload | HTTP 422 |
| Response action | Not present or executed |
| Secret file permissions | `0640` |
| API binding | `10.77.30.10:8010` only |
| Default route after deployment | Absent |

The first test run exposed SQLite connections that were not explicitly closed. Windows retained the database handle during test cleanup. The store was corrected to close each connection deterministically, and the full suite then passed.

Live readiness reports only service status, latency, and sanitized failure categories. It does not expose credentials or upstream response bodies.

The reboot check also showed that a fixed validation idempotency key made the validator non-repeatable. It now generates a unique synthetic run identifier, then repeats that identifier within the same run to prove accepted-then-duplicate behavior.

After reboot, liveness recovered before every dependency was ready: Wazuh and MISP were healthy while Shuffle and TheHive databases were still starting, so readiness correctly returned `degraded`. All four integrations converged to `healthy` within the subsequent validation window, and a post-reboot accepted-then-duplicate test passed.
