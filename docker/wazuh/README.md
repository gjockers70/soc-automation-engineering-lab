# Wazuh single-node deployment

This directory contains the reproducible Phase 3 deployment boundary for Wazuh 4.14.7. The scripts clone the matching upstream Docker release, create local-only credentials, bind published ports to `10.77.30.10`, enable password-authenticated enrollment, generate lab TLS certificates, disable active response, and validate the running manager, indexer, and dashboard.

Operational secrets and the rendered upstream deployment live under `/opt/soc-lab` on `soc-mgr-01`; they are not repository artifacts. `.env.example` documents required variable names without usable values.

## Script order

1. `bootstrap_manager.sh`
2. `prepare_wazuh_stack.sh`
3. `start_wazuh_stack.sh`
4. `configure_phase3_manager.sh`
5. `validate_wazuh_manager.sh`
6. `validate_phase3_ingestion.sh` after endpoint enrollment and test-event generation
7. `install_phase4_detections.sh` to validate and load custom rules
8. `validate_phase4_detections.sh` after controlled Phase 4 test events
9. Seed or update all Shuffle workflows and prepare the corrected gateway image
10. Stage `integrations/` plus a private `soc-gateway.env`, then run `install_gateway_integration.sh`

The gateway integration accepts only rules `100100`, `100101`, and `100102` when the Wazuh alert also carries the `soc_lab` group. It uses a protected token file rather than command-line credentials. Gateway failures are written atomically to `/var/ossec/queue/soc-gateway-spool` and retried on the next invocation. The installer backs up `ossec.conf`, validates the resulting manager configuration, and restores the prior file if validation fails.

Do not run the installer without separate authorization to change `soc-mgr-01`.

The dashboard is reachable only through an administrative SSH tunnel to `10.77.30.10:443`. No Wazuh service is bound to the mini-PC's physical-LAN address.
