# Artifact Selection

| Platform | Artifact | Defensive purpose |
|---|---|---|
| Linux | `Linux.Sys.Pslist` | snapshot running processes |
| Linux | `Linux.Network.Netstat` | map listening and connected sockets to processes |
| Linux | `Linux.Sys.Users` | review configured local identities |
| Linux | `Linux.Sys.LastUserLogin` | inspect recent login history |
| Linux | `Linux.Sys.Services` | review systemd startup and service state |
| Linux | `Linux.Search.FileFinder` | collect metadata and SHA-256 for `/var/lib/soc-lab/phase2.conf`; upload disabled |
| Windows | `Generic.System.Pstree` | reconstruct current parent-child process relationships |
| Windows | `Windows.Network.Netstat` | map sockets to processes |
| Windows | `Windows.Sys.Users` | review local identities and account attributes |
| Windows | `Windows.Sys.StartupItems` | review common persistence/startup locations |
| Windows | `Windows.EventLogs.Evtx` | parse only recent authentication, process, and PowerShell event IDs |
| Windows | `Windows.Search.FileFinder` | collect metadata and SHA-256 for the synthetic Phase 11 marker; upload disabled |

These artifacts collect live state or small, selected records. They do not execute remediation, dump credentials, capture memory, acquire disks, or search broad user-data paths.

## Concepts

- **Live response** queries a running endpoint for current state. It is fast and operationally useful but changes over time and can be affected by the running system.
- **Triage** is a bounded collection chosen to answer immediate investigative questions and prioritize deeper work.
- **Forensic collection** preserves a broader, methodically documented evidence set with stronger integrity and custody controls.
- **Full forensic imaging** acquires a bit-for-bit storage image, usually with specialized tooling and substantially greater time, storage, and legal-process requirements.
