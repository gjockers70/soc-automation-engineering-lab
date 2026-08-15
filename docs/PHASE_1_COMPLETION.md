# Phase 1 completion report

Phase 1 was validated on August 12, 2026. The deployment remains local to the Ubuntu virtualization host and is not publicly exposed.

## Validated state

| Check | Observed result |
|---|---|
| Management VM | `soc-mgr-01` running; 4 vCPUs; 12 GiB RAM; autostart disabled |
| Operating system | Ubuntu Server 24.04 |
| Virtual disk | 80 GiB sparse QCOW2; 1.35 GiB host allocation after provisioning |
| Guest filesystem | 77 GiB usable; 75 GiB available; 3% used |
| Telemetry interface | `10.77.30.10/24` only |
| Default/external route | None |
| Container runtime | Docker 29.1.3; daemon enabled and active; `overlayfs` storage driver |
| Compose | Docker Compose 2.40.3 |
| Guest agent | Connected and able to run bounded validation commands |
| Host-to-guest SSH | Successful over `soc-telemetry` |
| Reboot persistence | VM returned to running state; isolated address, Docker, and SSH remained available |
| Provisioning access | NAT interface removed; `pentest-provisioning` inactive |
| Cloud-init media | Ejected from the VM |
| Existing lab VMs | All four remained shut down and unchanged |
| Host memory after deployment | 49 GiB available; swap effectively unused |
| Host storage after deployment | 267 GB available; 41% used; inode use 1% |

## Isolation evidence

The persistent VM definition contains one interface connected to `soc-telemetry`. The network XML has no forwarding mode or physical bridge. Inside the guest, the route table contains only `10.77.30.0/24` and the inactive Docker bridge route. Validation fails if a default route or route to an external address is present.

The host exposes no new SOC application port to its physical management interface. Libvirt DNS listens only on `10.77.30.1:53`, inside the telemetry network.

## Operational state

- `soc-mgr-01` is running.
- `soc-telemetry` is active and does not autostart.
- The VM does not autostart.
- Existing lab networks remain inactive.
- No SIEM, SOAR, threat-intelligence, incident-management, or endpoint-monitoring product is installed yet.

## Known limitation

The host SSH service prohibits TCP forwarding. Administration is therefore performed from the virtualization host to the isolated VM. No host SSH policy was weakened during Phase 1.

## Rollback boundary

Phase 1 rollback removes only `soc-mgr-01`, its dedicated disk and seed media, the `soc-lab` storage pool, and the `soc-telemetry` network. Existing defensive-lab VMs, disks, recovery copies, and networks are outside the rollback scope.
