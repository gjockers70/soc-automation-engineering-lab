# Collection Plan

## Objective

Collect enough volatile and recent host context to support an analyst’s first triage decision without performing full acquisition or changing endpoint security state.

## Scope

| Endpoint | Included evidence | Excluded evidence |
|---|---|---|
| `ubuntu-web-01` | processes, sockets, users, recent logins, services, one selected file’s metadata and hash | home-directory contents, browser data, memory, packet capture, bulk logs |
| `win11-01` | process tree, sockets, local users, startup items, selected recent authentication/process/PowerShell events, one synthetic file’s metadata and hash | registry hives, memory, browser data, credentials, full event-log export |

Collections run with a 20% CPU limit, five-minute timeout, and two-minute no-progress timeout. File-finder artifacts keep uploads disabled. The Windows event query is limited to the prior day, two channels, and event IDs 4624, 4625, 4688, and 4104.

## Preservation and handling

Velociraptor records client ID, flow metadata, timestamps, artifact names, and returned results. Raw ZIP containers remain permission-restricted on `soc-mgr-01`. Analysts record collection hashes before moving evidence, preserve source timestamps, and keep interpretation separate from collected facts.

This lab does not implement legal evidence custody, write blockers, memory capture, deleted-file recovery, or full-disk imaging.

## Operational sequence

1. Confirm the alert and endpoint are in the owned lab scope.
2. Confirm the client is online and the server has no default route.
3. Run only the listed artifacts.
4. Review collection completion and errors before interpreting results.
5. Correlate timestamps with Wazuh and TheHive.
6. Record findings and gaps in the investigation notes.
7. Propose any response separately through the Phase 10 approval gate.
