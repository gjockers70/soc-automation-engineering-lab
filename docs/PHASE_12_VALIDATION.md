# Phase 12 validation

Validation is complete when:

- all eight scenarios report passed;
- MISP and TheHive failure substitutes show three bounded attempts;
- authentication fails immediately without retry;
- malformed input returns HTTP 422;
- an exact replay returns duplicate without another workflow;
- malformed IOC candidates are rejected before enrichment;
- a ten-minute-old synthetic heartbeat is classified disconnected;
- every scenario records response_action_executed=false;
- the real gateway and all dependencies are healthy after the drills;
- the management VM retains no default route;
- the full repository test suite passes.

The detailed runtime result remains in the protected integration-state volume. The repository contains a sanitized copy with no tokens, payload bodies, incident identifiers, or host secrets.

## Live result

All eight scenarios passed on soc-mgr-01 on August 13, 2026 (America/Chicago). The deployed gateway reported version 0.4.0 from image soc-integration-gateway:phase12. Wazuh, Shuffle, MISP, and TheHive were healthy after the drills, both Wazuh endpoint agents were active, both endpoint VMs were running, the integration credential file remained mode 0640, and the management VM had no default route.

The initial start attempt showed that the preparation script built the image but had not installed its runtime start and Phase 12 validation scripts. The installer was corrected to deploy both with mode 0750, the image was rebuilt offline, and the actual container recreation and validation then passed. No broken deployment was committed.

The full repository suite passed 40 tests. The only workstation warning was inability to update pytest's disposable cache inside the restricted execution sandbox; it did not affect any test result.

Sanitized evidence is stored in evidence/phase12-live-validation.json.
