# Corrective live validation

## Result

The separately authorized deployment completed on August 14, 2026. Endpoint-originated Linux and Windows traces, durable retry recovery, delivery/case idempotency, approval-gated synthetic response, observability, isolation, and post-reboot recovery passed. The sanitized result is recorded in [corrective-integration-live-validation.json](../evidence/corrective-integration-live-validation.json).

After the final healthy runtime check, the operator gracefully shut down `soc-mgr-01` on August 14, 2026. A subsequent `virsh domstate soc-mgr-01` check returned `shut off`. This intentional offline state does not alter the saved live-validation result.

## Authorization gate

Do not execute this procedure from repository approval alone. It changes the owned `soc-mgr-01` Wazuh, gateway, and Shuffle deployment and requires separate infrastructure authorization.

## Deployment order

1. Capture a read-only health snapshot and protected backups of gateway state and Wazuh configuration.
2. Seed or update all five Shuffle workflows and confirm their protected webhook state file.
3. Build and start the corrected gateway image with the five webhook URLs.
4. Confirm the gateway worker, dependencies, metrics, restricted listeners, and absence of a default route.
5. Install the allow-listed Wazuh gateway integration and validate manager recovery.
6. Generate one harmless endpoint event for an owned detection scenario.

## Required evidence

One trace must show all of the following without manually posting a gateway fixture:

- endpoint event and Wazuh rule `100100`, `100101`, or `100102`;
- automatic authenticated gateway receipt and durable queued state;
- completed MISP lookup, score, and TheHive case;
- completed Shuffle handoff with the same trace and incident identifiers;
- pending approval for account activity, with no response before a decision;
- separately authenticated analyst approve, reject, or escalate result;
- only `soc-response-test` changes when approval is selected;
- replayed Wazuh delivery creates neither a duplicate delivery nor case;
- a safely simulated dependency failure enters retry state and completes after recovery;
- Prometheus exposes queue age/state and Grafana can distinguish quiet from broken;
- no default route, public listener, secret disclosure, or non-synthetic action.

## Rollback

Stop the corrected gateway, restore the prior gateway image and SQLite backup, restore the saved Wazuh configuration if required, restart the manager, and rerun the pre-change health snapshot. Do not describe the corrective path as live until every required item passes after reboot.
