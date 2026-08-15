# Portfolio Evidence

## Evidence policy

Every implemented claim should be traceable to versioned configuration, an automated test, or a sanitized live validation record. Evidence files contain synthetic identifiers and aggregate results only. Operational credentials, complete payloads, raw endpoint output, internal PKI, and database exports are excluded.

## Claim matrix

| Claim | Implementation | Validation evidence |
|---|---|---|
| Linux and Windows security monitoring | endpoints directory and Wazuh deployment | Phase 2–4 completion/validation documents |
| Three detection-as-code use cases | detections/sigma and detections/wazuh | Native validator, pySigma parser, synthetic events |
| Five authenticated SOAR handoff playbooks | playbooks fixtures and seed scripts | Corrective local validation plus playbooks/example-results |
| IP, domain, URL, and hash normalization | threat-intel and enrichment modules | Unit tests and Phase 5 documentation |
| Authenticated/validated webhook intake | FastAPI gateway | [Phase 8 live result](../evidence/phase8-live-validation.json) |
| Retry, timeout, rate-limit, and error classification | integration clients | Mocked API tests and Phase 12 drills |
| Delivery and incident deduplication | idempotency and incidents modules | [Phase 9 live result](../evidence/phase9-live-validation.json) |
| Automated TheHive case handoff | pipeline and TheHive client | Phase 9 case creation/reuse evidence |
| Approval-gated bounded response | approvals module and executor | [Phase 10 live result](../evidence/phase10-live-validation.json) |
| Linux and Windows endpoint triage | forensics/velociraptor | Sanitized Phase 11 summary |
| Eight safe failure scenarios | operations/failure-lab | [Phase 12 live result](../evidence/phase12-live-validation.json) |
| Platform metrics and health rules | observability directory | [Phase 13 live result](../evidence/phase13-live-validation.json) |
| Mocked regression and safety tests | tests directory | Phase 14–17 validation records |
| Restricted CI | GitHub Actions workflow | [Phase 15 CI result](../evidence/phase15-ci-validation.json) |
| Operational health and recovery model | operations directory | [Phase 16 live result](../evidence/phase16-operations-validation.json) |
| Automatic durable Wazuh delivery and Shuffle handoff | corrective adapter, queue, worker, playbooks, and analyst client | [Corrective local validation](../evidence/corrective-integration-local-validation.json), [corrective live validation](../evidence/corrective-integration-live-validation.json), and CI |

## Reproduction levels

- Static: inspect committed configuration, fixtures, documentation, and sanitized results.
- Local: install pinned development dependencies and run the lint, repository, detection, and pytest validators.
- Lab: run component validators on soc-mgr-01 and generate only the documented synthetic endpoint activity.

The corrective lifecycle must begin with an endpoint event. A manually posted Wazuh-style fixture cannot satisfy its live acceptance requirement.

Lab reproduction requires owned infrastructure and locally generated runtime credentials. CI intentionally performs only static and mocked validation and cannot connect to the lab.
