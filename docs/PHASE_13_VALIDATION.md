# Phase 13 validation

Validation is complete when:

- Prometheus and Grafana report healthy;
- Prometheus reports the gateway target as up;
- at least five platform rules are loaded;
- the gateway exports every required metric family;
- the read-only Shuffle collector reports healthy;
- Grafana requires authentication and exposes the provisioned dashboard through its API;
- Prometheus is loopback-only and Grafana is telemetry-only;
- the generated Grafana credential file remains mode 0640;
- the management VM has no default route;
- exact deployed versions are recorded;
- the full repository test suite passes.

## Live result

Live validation passed on soc-mgr-01 on August 14, 2026 (America/Chicago). Prometheus 3.13.2 and Grafana 13.1.3 were healthy. The gateway target and Shuffle collector were up, five rules loaded, and the soc-platform-overview dashboard was provisioned.

Prometheus listened on 127.0.0.1:9090, Grafana listened on 10.77.30.10:3000, the Grafana secret file remained mode 0640, and the management VM had no default route.

The image preparation flow initially required registry access even after the digest-pinned images were cached. It was corrected to inspect each exact image locally and pull only a missing image. A pre-start review also corrected provisioning-file permissions for the containers' non-root users while retaining restrictive secret permissions. The corrected deployment and validator passed; no broken deployment was committed.

The full repository suite passed 49 tests. Sanitized evidence is stored in evidence/phase13-live-validation.json.
