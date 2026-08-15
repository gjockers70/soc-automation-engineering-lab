# Security

## Scope

This repository supports a private, isolated defensive-security lab. Testing is restricted to systems owned by the lab operator or deliberately created as test targets.

## Network controls

- No SOC or vulnerable guest is bridged directly to the physical LAN.
- The telemetry network has no Internet forwarding or physical uplink.
- Temporary provisioning access is removed after package installation.
- Administrative web interfaces are reached through SSH tunnels.
- Endpoint telemetry interfaces receive no default gateway.

## Secrets

- Secrets, rendered deployment files, private evidence, VM disks, and environment files are excluded from Git.
- Repository examples contain placeholders rather than operational credentials.
- No production keys, real personal information, or real credentials are used.
- Wazuh runtime credentials are generated on `soc-mgr-01`; enrollment secrets move directly between guests, are deleted from endpoints after successful enrollment, and are never stored on the virtualization host or in Git.
- Linux packages are checked against repository SHA-512 metadata, and the Windows installer must carry a valid Wazuh Authenticode signature.

## Response controls

Wazuh active response is disabled centrally and on both agents. Phase 10 implements one separately authenticated, exact-allow-list response against an application-level synthetic identity. It has no ability to change a Linux, Windows, Active Directory, or platform account.

## Reporting

Do not commit raw forensic archives, packet captures, tokens, cookies, private keys, database volumes, or unsanitized screenshots. Public evidence must use synthetic data and remove host-specific sensitive details.

## Endpoint telemetry boundary

Endpoint telemetry interfaces use static RFC 1918 addresses without gateways. The temporary NAT provisioning network is activated only for an approved package installation and is stopped immediately afterward. Collection rules use focused lab paths and synthetic validation activity; automatic containment remains prohibited.

Phase 4 detection tests use TEST-NET addresses, a harmless encoded `Write-Output` command, and a temporary local validation identity that is disabled and removed immediately. Detection matches create alerts only.

## Threat-intelligence controls

MISP runtime secrets are generated on `soc-mgr-01` and stored in `/opt/soc-lab/secrets/misp.env` with mode `0640` and ownership `root:docker`. The API key is never printed by validation, copied to the workstation, or committed. MISP uses a self-signed certificate only inside the isolated lab; production certificate verification would be mandatory.

Phase 5 intelligence is synthetic and unpublished. External feeds, synchronization servers, and automatic feed updates are disabled. Local IOC reputation is test metadata and cannot authorize blocking, account changes, quarantine, or any other consequential action.

## Incident-management controls

Operational TheHive administrator, organisation-user, and API credentials remain only in `/opt/soc-lab/secrets/thehive.env` with mode `0640`. The documented default administrator password is replaced during bootstrap. The direct application port is loopback-only; the reverse proxy is reachable only from the isolated telemetry network.

The Phase 6 case uses TEST-NET-2 and `.test` indicators. Its containment task remains approval-gated and no response action is executed by the seed workflow.

## SOAR controls

Shuffle administrator, API, encryption, OpenSearch, and webhook secrets are generated on `soc-mgr-01` and stored in `/opt/soc-lab/secrets/shuffle.env` with mode `0640`. Git contains key names and placeholders only.

Webhook triggers require an exact custom header. Negative validation confirms a missing header is rejected with 401. The backend API is loopback-only, the UI is telemetry-only, and OpenSearch is not published on the host.

Phase 7 workflows contain no containment node. They record synthetic input for analyst handoff and mark account activity as approval-required. Later phases must preserve target allow lists, dry-run defaults, recorded approval, and lab-only execution.

Shuffle launches worker and app containers through the Docker socket. Compromise of the backend or Orborus could therefore affect the management VM. The lab limits that risk through isolation, generated credentials, pinned images, and restricted administrative access; this design is not suitable as-is for multi-tenant production use.

External telemetry and chat features are disabled. The deployment does not configure paid services or external intelligence feeds.

## Integration gateway controls

The FastAPI gateway accepts only explicitly synthetic alerts and requires both a generated webhook token and an idempotency key. Authentication comparisons are constant-time. Missing credentials, malformed data, duplicate content, and conflicting key reuse receive distinct responses and audit events.

The container runs as a non-root UID with a read-only root filesystem, all capabilities dropped, `no-new-privileges`, bounded resources, and a telemetry-only listener. It uses host networking solely to reach loopback-bound lab APIs; the application binds to `10.77.30.10`, not all interfaces.

Platform credentials are copied at deployment from existing protected secret files into `/opt/soc-lab/secrets/integration.env` with mode `0640`. Logs, readiness output, API errors, fixtures, and committed evidence exclude tokens, passwords, upstream response bodies, and complete alert payloads.

## Automated enrichment controls

Phase 9 accepts only validated IOC formats and queries only the local MISP service. A missing intelligence match remains unknown rather than being treated as safe. The deterministic score records its factors and cannot authorize containment.

The incident fingerprint contains a one-way SHA-256 digest of rule, endpoint, and normalized indicators. TheHive cases are tagged `approval:required` and `response:not-executed`. Failed enrichment or case creation releases unfinished reservations for safe retry, while audit records exclude credentials and full upstream bodies.

## Approval controls

The automation token can create a proposal but cannot decide it. A separately generated approval token is required to retrieve or finalize approval records. Secrets remain in `/opt/soc-lab/secrets/integration.env` with mode `0640` and are never returned by the API or committed.

Pydantic literal types and an independent executor check constrain the only action to `disable_synthetic_account` and the only target to `soc-response-test`. Reject and escalate branches perform no state change. Final decisions are immutable except for an identical idempotent replay; conflicting decisions return HTTP 409. SQLite and structured JSON logs preserve the decision and execution result.

## Forensic-triage controls

Velociraptor server configuration, internal PKI, API certificate, administrator credential, datastore, and raw collections remain outside Git. The credential file uses mode `0640`. The GUI and client frontend listen only on the isolated telemetry address, the API is loopback-only, and no system has a default route.

Official 0.77.1 binaries are accepted only after exact SHA-256 validation. Triage collections use CPU and timeout limits, select narrow artifacts and event IDs, and disable file uploads. Raw archives are permission-restricted on `soc-mgr-01`; the repository contains only a sanitized coverage summary. No memory capture, credential collection, packet capture, bulk home-directory search, remediation, or full-disk acquisition is authorized in Phase 11.

## Failure-drill controls

Phase 12 does not stop real services, disconnect endpoints, corrupt data, or replace operational credentials. Unavailable, timeout, and authentication conditions use local transports; endpoint disconnection uses stale synthetic heartbeat data. Live calls are limited to malformed-schema rejection and exact duplicate suppression with synthetic alert content.

Failure logs contain service name, category, attempt count, bounded delay, and status code where useful. They exclude URLs, request bodies, credentials, and upstream response bodies. Detailed results remain in the protected integration-state volume; only sanitized evidence is committed. Every drill asserts response_action_executed=false.

## Observability controls

Prometheus is bound to loopback and Grafana is bound only to the isolated telemetry address. Grafana anonymous access and user registration are disabled, and its generated administrator credential remains in /opt/soc-lab/secrets/observability.env with mode 0640.

Metrics use fixed, low-cardinality labels and exclude alert payloads, IOC values, usernames, endpoints, case identifiers, credentials, and analyst notes. Prometheus and Grafana use digest-pinned images, read-only root filesystems, dropped capabilities, no-new-privileges, resource limits, and local persistent volumes.

No external telemetry, analytics destination, public dashboard, paid service, or external notification channel is configured. Prometheus health rules cannot authorize or execute a response action.

## Automated-test controls

Phase 14 API tests use httpx mock transports and reserved synthetic values. They do not contact Wazuh, Shuffle, MISP, TheHive, Grafana, Prometheus, the Internet, or an endpoint. Test credentials are obvious synthetic placeholders and never match runtime secrets.

Configuration tests verify secret redaction and unsafe-bound rejection. Pipeline tests prove failed deliveries and incident reservations can be retried safely. Approval tests include direct database tampering and confirm the independent executor allow list fails closed without changing the synthetic identity.

## CI/CD controls

GitHub Actions receives only contents: read permission. Checkout and Python setup actions are pinned to full commit SHAs, checkout credentials are not persisted, and actionlint is downloaded at a fixed version with an official SHA-256 checksum.

The workflow does not use repository secrets, a self-hosted runner, pull_request_target, a deployment environment, artifact upload, cloud credentials, or any route to the private lab. All API tests are mocked. A repository validator fails CI if an action becomes mutable or a forbidden privileged capability is added.

## Operational controls

The Phase 16 health snapshot is read-only and emits only aggregate service, capacity, and isolation state. It does not read secret files, print payloads, restart services, alter firewall or route state, or execute response actions. An unexpected default route is treated as a degraded security boundary.

Recovery procedures preserve idempotency keys, incident fingerprints, audit events, and approval state. Unknown enrichment remains unknown, and an uncertain response result must be reconciled before retry. Backup archives, manifests containing sensitive paths, raw logs, and runtime credentials remain outside Git.
