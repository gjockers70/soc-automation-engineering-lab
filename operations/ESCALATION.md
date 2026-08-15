# Escalation

Response targets are exercise objectives, not a production SLA or evidence of 24x7 staffing.

## Severity model

| Severity | Lab definition | Acknowledge target | Escalation trigger |
|---|---|---:|---|
| SEV-1 | Safety boundary crossed, suspected secret exposure, destructive action, or integrity loss | 15 minutes when attended | Stop affected automation; notify lab owner |
| SEV-2 | Alert pipeline unavailable, cases cannot be created, or multiple critical services fail | 30 minutes | Owner after 15 minutes unresolved |
| SEV-3 | One integration degraded with a safe manual path available | 4 hours | Owner if not recovered during session |
| SEV-4 | Documentation defect, cosmetic issue, or maintenance finding | Next window | Track as backlog/change request |

## Roles

The lab owner is incident commander, platform operator, and final approval authority. An analyst role may triage evidence and recommend action, but cannot approve its own consequential proposal. Production should separate on-call engineer, SOC lead, incident commander, system owner, and approver duties.

## Workflow

1. Record UTC detection time and first observable symptom.
2. Assign severity from impact, not the loudest log message.
3. Pause affected playbooks if execution could duplicate incidents or actions.
4. Preserve audit IDs, timestamps, container states, and sanitized errors.
5. Escalate when the acknowledgement or recovery threshold is reached.
6. Record owner, decision, next update, and approval separately.
7. Downgrade only after impact is bounded; close only after validation.

## Communication template

~~~text
Severity / UTC opened:
Affected capability:
User or alert impact:
Current evidence:
Safety boundary status:
Actions attempted:
Decision or approval needed:
Owner / next update:
~~~

Do not include tokens, passwords, real personal data, or unrestricted forensic output. No external paging or chat integration is configured in this $0 lab.
