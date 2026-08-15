# Known Limitations

## Availability and scale

- All major services share one management VM and one physical mini-PC.
- Datastores and orchestration workers are not clustered.
- Prometheus observes the same host it monitors, so total host failure requires an external observer.
- The lab has design targets and runbooks, not measured production SLAs or 24x7 staffing.
- SQLite provides an attended-lab durable inbox, retry schedule, terminal failure state, and replay. It is not a clustered production broker or independent dead-letter service.

## Security and identity

- Administrative access relies on the lab host and local credentials rather than enterprise SSO, MFA, PAM, or centralized secrets management.
- Role separation is modeled through credentials and code paths, not a multi-person organization.
- Shuffle backend/Orborus use the Docker socket, a high-trust boundary unsuitable for an untrusted multi-tenant environment.
- Self-signed certificates are acceptable only inside the isolated lab.
- VM recovery copies share the same physical storage and are not off-host, application-consistent backups.

## Detection and intelligence

- Three detections demonstrate the engineering lifecycle; they do not represent broad ATT&CK coverage.
- Detection status remains test because representative production baselines and false-positive measurements do not exist.
- MISP contains local synthetic indicators only. External feeds, sharing communities, expiry governance, and source licensing are not exercised.
- A local intelligence match adds context but does not prove maliciousness or authorize containment.

## Automation and response

- The gateway invokes scenario-specific authenticated Shuffle handoffs after MISP and TheHive processing. Shuffle records workflow execution and analyst handoff; the Python gateway remains the authoritative enrichment, scoring, deduplication, proposal, and response layer.
- The only executable response changes an application-level synthetic identity. There is no operating-system account disablement, Active Directory action, host quarantine, IP block, file deletion, or malware handling.
- Approval is single-approver and does not implement quorum, separation-of-duty enforcement across real people, or enterprise change tickets.
- Notifications remain local; no email, chat, pager, or ITSM integration is configured.
- A crash after Shuffle accepts a webhook but before returning its execution identifier is held for operator reconciliation rather than automatically retriggered. This favors duplicate prevention over unattended recovery from an ambiguous handoff.

## Forensics and evidence

- Velociraptor collections are live-response triage, not full forensic imaging.
- Memory acquisition, disk imaging, credential collection, packet capture, and invasive bulk collection are outside scope.
- Raw collection archives remain private and are not independently signed or stored in a forensic evidence system.
- Live administrative screenshots are excluded to avoid leaking identifiers and secrets; committed visual material is generated from versioned configuration and sanitized evidence.

## Production changes

An enterprise design would separate ingestion, orchestration, case management, intelligence, investigation, and monitoring tiers; add redundant datastores and workers; use durable queues; centralize identity and secrets; enforce egress controls; integrate external monitoring and on-call paging; use encrypted off-host backups; define retention and legal-hold policy; and test regional or site failover.
