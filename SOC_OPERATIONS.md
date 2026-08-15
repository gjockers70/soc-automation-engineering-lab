# SOC Operations

## Purpose

This document defines the end-to-end analyst and platform workflow for the isolated lab. It separates automated evidence gathering from human judgment and preserves an auditable path from alert generation to closure.

## Roles

| Role | Lab responsibility | Production separation |
|---|---|---|
| Platform operator | Service health, integrations, changes, recovery | On-call SOC platform engineering |
| Analyst | Triage, evidence review, case notes, recommendation | Tiered SOC analyst team |
| Approver | Approve, reject, or escalate the bounded proposal | Incident commander or system owner |
| Executor | Enforce the exact action and target allow list | Dedicated response connector/service account |

One person may perform several lab roles, but the credentials and workflow states remain separate. The automation credential cannot approve a proposal, and approval does not bypass the executor allow list.

## End-to-end analyst workflow

1. Generate a documented synthetic event on an owned endpoint.
2. Confirm the expected Linux or Windows source log contains the event.
3. Confirm the Wazuh agent is connected and the intended rule triggered.
4. Record alert ID, rule, endpoint, source timestamp, and test scenario.
5. Confirm the allow-listed Wazuh integration submitted the alert automatically.
6. Validate the durable delivery disposition and trace: queued, processing, retrying, completed, failed, duplicate, or rejected.
7. Review extracted IOC type and normalized value.
8. Review local MISP match, source, confidence, tags, and timestamp.
9. Review the deterministic score and each contributing factor.
10. Confirm TheHive created a case or reused the expected incident fingerprint.
11. Confirm the scenario-specific Shuffle execution carries the same trace and incident identifiers, then add analyst notes and investigation tasks.
12. If additional evidence is necessary, create an analyst-authenticated bounded triage request and run only the matching Velociraptor artifact.
13. Write a remediation recommendation; do not treat enrichment or score as authorization.
14. Create a response proposal only for the synthetic allow-listed target.
15. Use the separate approval path to approve, reject, or escalate and record the rationale.
16. Reconcile the executor result, validate the endpoint or synthetic identity state, and close with reason and lessons learned.

## Case lifecycle

~~~mermaid
stateDiagram-v2
    [*] --> New
    New --> Triage
    Triage --> Investigation
    Investigation --> ContainmentRecommendation
    ContainmentRecommendation --> Approval
    Approval --> Remediation: approved
    Approval --> Investigation: rejected or escalated
    Remediation --> Validation
    Validation --> Closed
    Closed --> [*]
~~~

Required case content:

- stable incident identifier, title, severity, status, and source;
- normalized indicators and enrichment results;
- UTC timeline, evidence references, and analyst notes;
- scoring factors and recommended remediation;
- approval identity, decision, reason, and timestamp;
- execution result, post-action validation, closure reason, and lessons learned.

## Triage decision points

| Question | Evidence | Safe outcome |
|---|---|---|
| Is the detection expected? | Source event and Wazuh rule fields | Close as authorized test or continue |
| Is the indicator valid? | Type-specific parser result | Reject malformed IOC; never query it |
| Is intelligence reliable? | Source, confidence, age, and local provenance | Treat no match as unknown, not benign |
| Is this an existing incident? | One-hour incident fingerprint | Reuse case without dropping the new alert timeline |
| Is more endpoint context needed? | Current hypothesis and case task | Run only the narrow triage artifact |
| Is response justified? | Evidence, confidence, scope, target ownership | Propose; never auto-approve |

## Platform operations

At the start and end of an attended session, run the [read-only health snapshot](operations/HEALTH_CHECKS.md). Review queue depth and age, terminal failed deliveries, failed workflow executions, pending approvals, endpoint last-seen status, dependency health, API failures, enrichment latency, duplicate volume, and disk/memory capacity.

Use the [service dependency map](operations/SERVICE_DEPENDENCIES.md) before maintenance or recovery. Use [failure recovery](operations/FAILURE_RECOVERY.md) for bounded replay and reconciliation. Changes follow [change management](operations/CHANGE_MANAGEMENT.md); backups and restore tests follow [backup recovery](operations/BACKUP_RECOVERY.md).

## Failed automation

Preserve the source alert and its idempotency key. Record the last successful step, sanitized error class, retry count, next attempt, incident fingerprint, and approval state. Retry only transient failures with bounded backoff. Authentication, validation, and allow-list failures require correction or analyst review rather than repeated execution.

If an approved action has an unknown result, inspect the target state and audit trail before retry. Never infer failure from a client timeout and execute the action again blindly.

## Shift handoff and escalation

The lab is not staffed continuously. The [shift handoff template](operations/SHIFT_HANDOFF.md) demonstrates how open cases, failed workflows, pending decisions, changes, and timed actions would transfer in a 24x7 team. Severity and attended-lab response objectives are defined in [ESCALATION.md](operations/ESCALATION.md).

## Closure quality

Close an incident only when the detection was explained, evidence was preserved, the approved outcome was validated, automation state is consistent, follow-up work has an owner, and the closure reason distinguishes true positive, benign positive, false positive, or test activity. Detection tuning becomes a reviewed change rather than an untracked edit.
