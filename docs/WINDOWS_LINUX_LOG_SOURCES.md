# Windows and Linux log-source comparison

| Security question | Linux source | Windows source |
|---|---|---|
| Who authenticated? | `/var/log/auth.log`, SSH and PAM journal records | Security 4624, 4625, and related logon events |
| Was privilege used? | `sudo` records plus Audit watches | Special-logon and privilege-use categories |
| Was an account changed? | Audit watches on `/etc/passwd` and `/etc/group` | Security account-management events |
| What process ran? | Audit `execve` records for interactive users | Security 4688 with command-line auditing |
| What PowerShell ran? | Not applicable | Operational 4103/4104 events |
| Was a selected file changed? | Audit watch keys | Object Access auditing when explicitly scoped |
| What network state exists? | Kernel interfaces, routes, sockets, and later Wazuh inventory | Network adapters, routes, connections, and later Wazuh inventory |

Linux commonly distributes security context across files, the system journal, and Audit records. Windows centralizes much of the equivalent context in structured event channels whose usefulness depends on audit policy. A SIEM should retain original host, channel, event ID or audit key, user, process, timestamp, and raw event while adding normalized fields for cross-platform investigation.

Broad process or object-access auditing can be noisy. The lab starts with focused rules, validates expected events, records false-positive considerations during detection development, and expands collection only when an investigation or detection requires it.
