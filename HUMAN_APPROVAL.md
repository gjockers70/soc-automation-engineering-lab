# Human Approval and Lab Response

Phase 10 adds a governance boundary between an automation recommendation and a consequential response. Automation may propose one response, but a separately authenticated analyst decision is required before execution.

## Implemented action

The only action is `disable_synthetic_account` against the exact target `soc-response-test`. That target is an application-level identity record in the integration gateway, not a Linux, Windows, Active Directory, TheHive, or MISP account. The response executor has no endpoint-administration credentials.

This narrow implementation demonstrates approval state, separation of duties, idempotency, auditability, and safe execution without creating a general-purpose remote administration capability.

## Decision flow

1. An authenticated automation client creates a proposal linked to a TheHive incident.
2. The proposal records action, target, reason, evidence, confidence, and a pending state.
3. An analyst uses a separate generated approval credential to approve, reject, or escalate.
4. Reject and escalate record the decision and execute nothing.
5. Approve changes the allow-listed identity from `enabled` to `disabled`.
6. Repeated identical decisions return the existing final result; conflicting decisions return HTTP 409.
7. Proposal and decision history is retained in SQLite, JSON audit events, and best-effort TheHive case comments.

The analyst name is asserted attribution inside this single-user lab. An enterprise design would use individual SSO identities, role-based access, step-up authentication, and immutable centralized audit storage.

## API boundary

| Endpoint | Credential | Purpose |
|---|---|---|
| `POST /v1/approvals` | automation webhook token | propose an allow-listed action |
| `GET /v1/approvals/{id}` | approval token | retrieve the durable record |
| `POST /v1/approvals/{id}/decision` | approval token | approve, reject, or escalate |
| `GET /v1/lab-identities/{identity}` | approval token | validate the synthetic identity state |

Pydantic literal validation rejects every other action and target before it reaches the executor. The approval token is generated separately and stored only in the protected deployment environment.

## Commercial-platform mapping

This models the governance concepts behind a Tines approval page or equivalent SOAR pause-and-resume gate: the workflow proposes a bounded action, waits for an authorized decision, records it, and continues through a controlled branch. The implementation is not a replacement for Tines and does not claim feature parity.

## Limitations

- The response changes only a local application record.
- The lab uses one shared approval credential rather than per-analyst identity.
- TheHive comments are a secondary projection; SQLite and JSON audit records are authoritative if case-note synchronization fails.
- No approval user interface, notification channel, rollback endpoint, or endpoint containment connector is implemented yet.
