# Phase 4 implementation

## What was built

Phase 4 adds a detection-as-code layer with three documented behaviors, Wazuh runtime rules, Sigma equivalents, safe test fixtures, endpoint event generators, structural validation, and live alert verification.

## Why a SOC uses it

Default SIEM content provides broad coverage, but each environment needs hypotheses tied to its own event sources and risk. Version-controlled rules make detection changes reviewable, testable, repeatable, and easier to troubleshoot. Per-rule documentation supports analyst triage and future tuning.

## Architecture

```text
Endpoint security event
  -> Wazuh agent
  -> built-in decoder and parent rule
  -> Phase 4 child rule or temporal correlation
  -> labeled alert with severity and MITRE mapping
  -> analyst triage guidance
```

Custom rule IDs use Wazuh's recommended 100000–120000 range. The implementation inherits already validated built-in rules instead of duplicating Windows event parsing or SSH decoding.

## Detection set

| ID | Source | Logic | Severity |
|---|---|---|---|
| `SOC1001` | Linux `sshd` | Five invalid-user attempts from one IP within 60 seconds | Wazuh 10 |
| `SOC1002` | Windows 4688 | PowerShell command line contains an encoded-command switch and payload | Wazuh 10 |
| `SOC1003` | Windows 4720 | Created account name does not end in `$` | Wazuh 9 |

The Sigma version of `SOC1001` models the base invalid-user event. Wazuh supplies the live temporal correlation because correlation syntax and backend support differ across Sigma consumers.

## Deployment

`docker/wazuh/install_phase4_detections.sh` copies the XML into the manager's persistent rules directory, sets restrictive ownership and permissions, runs the Wazuh analysis configuration test, restarts the manager, and waits for analysis, transport, database, and API processes. One bounded restart is allowed if the initial start is incomplete; a second failure blocks deployment and prints recent logs.

## Safety boundary

- SSH events are synthetic log messages using TEST-NET address `198.51.100.44`.
- Encoded PowerShell decodes only to a harmless `Write-Output` statement.
- The Windows validation identity receives a random lab-only password and is disabled and deleted immediately.
- Active response remains disabled; rules create alerts only.
