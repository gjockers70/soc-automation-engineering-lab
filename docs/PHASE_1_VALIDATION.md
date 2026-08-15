# Phase 1 validation

Phase 1 evidence will be recorded after remote deployment and validation.

## Required checks

- management VM boots successfully;
- cloud-init completes without error;
- Docker Engine and Compose v2 respond;
- the VM has only its isolated telemetry interface after provisioning;
- the VM has no default route or Internet connectivity;
- the host can reach the VM at `10.77.30.10`;
- the management VM is not directly reachable from the physical LAN;
- the temporary provisioning network is inactive;
- existing lab VMs, disks, and recovery copies remain unchanged;
- host RAM and storage remain above operational thresholds;
- rollback instructions are verified.

## Rollback boundary

Phase 1 rollback removes only `soc-mgr-01`, its dedicated disk and seed media, and the `soc-telemetry` network. Existing defensive-lab VMs, disks, recovery copies, and networks are outside the rollback scope.
