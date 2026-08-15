# Maintenance

## Before maintenance

Announce the attended window, identify affected capabilities, finish or safely pause synthetic workflows, record pending approvals, confirm capacity, create the required backup, and capture a health snapshot. Do not perform maintenance while a response result is unknown.

## Schedule

| Cadence | Tasks |
|---|---|
| Each session | Health snapshot, pending approval review, capacity check, end-of-session audit review |
| Weekly | Review rules, failed workflows, duplicate rate, API errors, endpoint last-seen, certificate horizon |
| Monthly | Review pinned releases, planned credential rotation, configuration restore, documentation links |
| Quarterly | Full alert-to-closure exercise, application-state restore, access review, recovery walkthrough |

## Patching

Review official release notes and advisories at maintenance time. Update immutable image or binary versions in Git, verify checksum/signature where available, test on synthetic data, deploy in dependency order, and retain a rollback version. Do not use unattended major-version upgrades.

## Capacity

Keep at least 75–100 GB free on the mini-PC before another VM recovery copy. The management VM warns at 85% root-disk use and 1024 MiB available memory. Investigate audit logs, search retention, databases, and raw forensic output before deleting anything; apply documented retention only after verifying exact paths.

## Completion

Run the affected validator, health snapshot, and end-to-end synthetic transaction. Confirm no unexpected route, exposed listener, duplicate case, unauthorized action, or secret in logs or Git. Record versions, evidence, exceptions, and next maintenance date.
