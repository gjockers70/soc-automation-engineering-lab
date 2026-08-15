# Change Management

## Change classes

| Class | Examples | Approval |
|---|---|---|
| Standard | Documented detection test or repeatable validation | Lab owner; pre-authorized when procedure is unchanged |
| Normal | Image/version update, rule tuning, workflow or configuration change | Lab owner after risk, test, and rollback review |
| Emergency | Active integrity, secret, or safety-boundary issue | Record reason before action when possible; review afterward |

## Change record

Record purpose, owner, affected services, security impact, dependencies, backup/rollback point, validation plan, maintenance window, approval, UTC start/end, result, and evidence path. Exclude secrets and raw sensitive artifacts.

## Procedure

1. Confirm clean Git state and capture a pre-change health snapshot.
2. Identify dependency and capacity effects.
3. Test with mocks or synthetic data.
4. Define a rollback condition and known-good version.
5. Approve and schedule; pause affected playbooks when needed.
6. Change one layer at a time. Do not combine credential rotation, migration, and unrelated rule tuning.
7. Run targeted validation, the full snapshot, and synthetic alert path.
8. Commit documentation/configuration changes with no secrets.
9. Close the record or roll back. Review emergency changes during the next attended session.

Detection changes require log source, logic, severity, false positives, validation, response recommendation, and history. Response workflow changes must prove reject/escalate remain non-mutating and approval remains separate from execution.
