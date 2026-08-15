# SOC Engineer Requirement Mapping

## Demonstrated requirements

| Job requirement | Project implementation | Evidence |
|---|---|---|
| Design and maintain security operations systems | Isolated multi-platform architecture with explicit dependencies and operating boundaries | ARCHITECTURE.md and operations/SERVICE_DEPENDENCIES.md |
| Security alert ingestion | Linux/Windows agents feeding Wazuh and authenticated webhook intake | Phase 2, 3, and 8 validation |
| Detection engineering | Wazuh/Sigma rules, test events, false positives, tuning, and lifecycle | detections directory |
| Security automation | Python modules, Bash/PowerShell administration, REST clients, and Shuffle workflows | src, endpoints, docker, and playbooks |
| APIs and webhooks | Authentication, schema validation, timeouts, retries, rate limits, idempotency | API_INTEGRATIONS.md and mocked tests |
| Threat-intelligence integration | MISP IOC lifecycle, normalization, confidence, provenance, and enrichment | THREAT_INTELLIGENCE.md |
| Incident response and investigation | TheHive case lifecycle, analyst tasks, timeline, evidence, and Velociraptor triage | INCIDENT_RESPONSE_PLAN.md and forensics |
| Safe remediation | Separate proposal, approval, decision, executor allow list, audit, and validation | HUMAN_APPROVAL.md |
| Windows and Linux administration | Audit policy, event logging, agents, service validation, and isolated interfaces | endpoints directory |
| Basic IT forensics | Running processes, connections, users, logins, startup items, selected events, metadata | forensics directory |
| Complex integration troubleshooting | Eight reproducible failures with signals, root cause, recovery, and prevention | TROUBLESHOOTING.md and failure lab |
| Reliable operations concepts | Health checks, dependency order, retries, escalation, backup, change, maintenance, handoff | RUNBOOK.md and operations directory |
| Observability | Processing, failure, latency, incident, duplicate, workflow, and dependency metrics | OBSERVABILITY.md |
| Automated testing and CI | Mocked regression suite, lint, detection parsing, asset/link validation, restricted CI | TESTING.md and CI_CD.md |
| Documentation and repeatability | Architecture, implementation, validation, completion, runbook, and security documents | Repository documentation set |
| Commercial-tool transfer | Explicit Tines, ThreatQ, and Andesite concept mapping | COMMERCIAL_PLATFORM_MAPPING.md |

## Remaining experience gaps

| Gap | Why the lab cannot honestly claim it | Enterprise development path |
|---|---|---|
| Direct Tines, ThreatQ, or Andesite administration | None of those commercial products is deployed | Vendor community edition/training, employer sandbox, or authorized trial |
| Production incident volume and on-call duty | Synthetic events and attended operation only | Supervised SOC operations with real SLAs and shift ownership |
| High availability and disaster recovery | Single host and single-node services | Clustered datastores/workers, site failover, off-host restore exercises |
| Enterprise IAM and multi-team governance | Local identities and modeled role separation | SSO/MFA/PAM, RBAC design, periodic access review, separation of duties |
| Real threat-feed operations | Local synthetic intelligence only | Licensed/open feed evaluation, source contracts, lifecycle/expiry, sharing policy |
| Enterprise endpoint containment | One application-level synthetic action | Authorized EDR/IAM response design with multi-stage approvals and rollback |
| Full digital forensics | Bounded live triage only | Chain of custody, imaging, memory acquisition, legal hold, specialist tooling |
| Cloud-scale security telemetry | Local VMs and container services | Cloud logging, identity, network, and managed-service integrations |
| Formal detection performance | No representative production baseline | Precision/recall measurement, detection QA, exception handling, content promotion |
| Organizational leadership | One-person lab roles | Cross-team design reviews, incident command, stakeholder reporting, service ownership |

The project should be described as a self-built portfolio lab. It supports discussion of implemented engineering decisions, validation, and troubleshooting but does not substitute for professional production-SOC experience.
