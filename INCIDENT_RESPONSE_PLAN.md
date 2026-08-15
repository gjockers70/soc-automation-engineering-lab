# Incident Response Plan

## Scope

This plan governs synthetic security events and owned systems inside the isolated SOC lab. It does not authorize action against public infrastructure, third-party systems, or real user accounts.

## Roles

- The analyst validates the alert, evidence, severity, and proposed response.
- The approver approves, rejects, or escalates consequential actions.
- The platform operator maintains service health, access, backups, and auditability.
- Automation may collect context, enrich indicators, score alerts, and draft recommendations. It may not disable accounts, block addresses, quarantine endpoints, or delete data without human approval.

## Lifecycle

1. **New:** Record source, title, time, severity, and ownership.
2. **Triage:** Validate the detection, scope, false-positive possibilities, and immediate risk.
3. **Investigation:** Correlate endpoint events, identity context, observables, and local intelligence.
4. **Containment Recommendation:** Document the proposed lab-only action, evidence, confidence, blast radius, and rollback.
5. **Approval:** A human approves, rejects, or escalates. The decision and identity are recorded.
6. **Remediation:** Execute only the approved bounded action.
7. **Validation:** Confirm the threat condition ended and the affected service remains healthy.
8. **Closed:** Record disposition, closure reason, evidence, and lessons learned.

Phase 10 implements steps 4 through 6 for one synthetic application identity. Rejection and escalation preserve the identity state. Approval records the analyst decision before the bounded state change, and identical retries do not execute the action again.

## Severity

Severity is based on demonstrated impact and confidence, not merely the presence of an indicator. A synthetic IOC match can increase context but cannot independently prove compromise. Analysts downgrade false positives and escalate cases with confirmed privileged access, lateral movement, persistence, or material service impact.

## Evidence handling

Preserve original timestamps, event identifiers, host names, collection method, and relevant hashes. Record analysis separately from raw evidence. Phase 6 uses case comments and observables; a later forensics phase expands collection and chain-of-custody guidance.

## Closure requirements

A case cannot close until its alert disposition, approval outcome, response result, validation evidence, and closure reason are recorded. Rejected containment is not a failed incident; it is a governed decision that must remain in the audit trail.
