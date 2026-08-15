# Phase 10 Validation

Validation covers the approval controls at three levels:

- automated tests verify non-executing reject/escalate branches, single execution, identical-decision idempotency, conflict handling, schema allow lists, and credential separation;
- live API validation creates a real synthetic alert and incident, then records reject, escalate, and approve decisions;
- reboot validation confirms the disabled synthetic identity and audit database survive service restart.

The live run must prove HTTP 401 without the approval credential, HTTP 409 for a conflicting final decision, HTTP 422 for an off-allow-list target, absence of an operating-system account named `soc-response-test`, protected secret-file permissions, and absence of a default route.

Sanitized machine-readable results are saved in `evidence/phase10-live-validation.json`. Credentials, upstream response bodies, and complete raw audit logs are not committed.
