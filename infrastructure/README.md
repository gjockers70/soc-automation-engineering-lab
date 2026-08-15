# Phase 1 infrastructure

This directory contains the reproducible definitions used to establish the isolated SOC management plane.

## Components

- `libvirt/soc-telemetry.xml`: isolated `10.77.30.0/24` network definition.
- `cloud-init/user-data.yaml`: base packages and Docker configuration.
- `cloud-init/60-soc-telemetry.yaml`: steady-state management VM address.
- `scripts/qga_exec.py`: bounded guest-agent command runner.
- `scripts/qga_write.py`: guest-agent file transfer helper.
- `scripts/finalize_guest_network.sh`: persistent telemetry-interface configuration.
- `scripts/validate_phase1_guest.sh`: repeatable guest validation.

## Provisioning sequence

1. Verify host capacity and confirm existing lab VMs are stopped.
2. Define and start `soc-telemetry` without autostart.
3. Create the `soc-lab` directory storage pool without autostart.
4. Download Ubuntu Server 24.04 from the official cloud-image service and verify its published SHA-256 digest.
5. Create an 80 GiB sparse volume and import the verified image.
6. Start `soc-mgr-01` with temporary provisioning NAT as its first interface and `soc-telemetry` as its second interface.
7. Allow cloud-init to install the guest agent, Docker Engine, Compose, and operational defaults.
8. Configure `10.77.30.10/24` on the telemetry interface.
9. Remove the temporary NAT interface and eject cloud-init media.
10. Stop the provisioning network.
11. Reboot and execute the validation script.

## Steady state

The VM has one NIC, no default route, no Internet route, and no direct physical-LAN exposure. Administration occurs from the virtualization host over `soc-telemetry`. Security platform containers are not deployed until their assigned phases.

## Rollback order

Rollback is deliberately scoped to Phase 1 objects:

1. Gracefully stop `soc-mgr-01`.
2. Undefine `soc-mgr-01`.
3. Delete only `soc-lab/soc-mgr-01.qcow2`.
4. Stop and undefine `soc-telemetry`.
5. Stop and undefine the `soc-lab` pool after verifying it contains no other volumes.

Never include the existing `pentest-lab` pool, its active disks, recovery copies, or existing networks in a Phase 1 rollback command.
