# Phase 7 validation

Validation was performed on the live isolated management VM with synthetic input only.

| Check | Result |
|---|---|
| Shuffle API with bearer authentication | Pass |
| Backend bound only to `127.0.0.1:5001` | Pass |
| UI bound only to `10.77.30.10:3001` | Pass |
| OpenSearch has no host-published port | Pass |
| Runtime secret file mode | `0640` |
| Unauthenticated webhook request | Rejected with 401 for all four playbooks |
| Authenticated webhook request | Accepted with 200 for all four playbooks |
| Suspicious Login execution | `FINISHED` |
| Suspicious File execution | `FINISHED` |
| Suspicious Domain execution | `FINISHED` |
| Account Activity execution | `FINISHED` |
| Consequential response action | None present or executed |
| Synthetic fixture tests | 4 passed |
| Post-reboot account workflow and authentication checks | `FINISHED`, 401/200 boundary retained |

An initial execution remained in `EXECUTING`. Orborus logs showed automatic swarm creation failed because Docker live-restore was enabled. The deployment was corrected to standalone worker mode and every playbook then completed. This resolved failure is retained as troubleshooting evidence rather than hidden.

Validation results in `playbooks/example-results/` omit tokens and payload content. Runtime workflow IDs are evidence of this deployment only and are not portable configuration.
