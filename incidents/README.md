# Incident management

TheHive is the lab's system of record for investigation work. Wazuh remains the monitoring and detection source; MISP supplies local indicator context; later phases add Shuffle orchestration and automated case creation. Phase 6 deliberately seeds one synthetic case directly through the API so case structure and lifecycle can be validated before automation is connected.

## Required case content

Every incident record must identify its source, indicators, timeline, evidence, analyst notes, automated enrichment, recommended remediation, approval history, and closure reason. Evidence belongs in the case or in a referenced, integrity-controlled location. Secrets, real credentials, and personal data do not belong in test cases.

The example fixture is safe to publish: it uses TEST-NET-2 and the reserved `.test` namespace. The live case remains on the isolated management VM.

## Lifecycle mapping

| Lab stage | TheHive representation | Exit condition |
|---|---|---|
| New | Native `New` status | Ownership and minimum fields confirmed |
| Triage | `InProgress`, triage task, lifecycle tag | Detection and severity validated |
| Investigation | Investigation tasks and case comments | Evidence supports a disposition |
| Containment Recommendation | Recommendation in case and approval task | Proposed action is specific and bounded |
| Approval | Approval task remains `Waiting` until human decision | Approve, reject, or escalate recorded |
| Remediation | Action task and audit comment | Approved lab-only action completed |
| Validation | Validation task and evidence | Control effectiveness confirmed |
| Closed | Resolved/closed native status and resolution fields | Closure reason and lessons learned recorded |

The intermediate stages are operational workflow states represented by tasks, tags, comments, and required fields; they are not falsely presented as custom native TheHive statuses.

## Commercial workflow comparison

TheHive demonstrates transferable case-management concepts: structured records, role-based access, evidence and observable association, task assignment, audit history, API-driven creation, and lifecycle governance. Commercial SOC ticketing platforms may add enterprise identity, contractual support, richer approval engines, multi-tenant controls, and vendor-specific integrations. The products are not identical.
