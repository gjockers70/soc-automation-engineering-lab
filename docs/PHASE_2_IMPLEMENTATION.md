# Phase 2 implementation

## Why the SOC needs this layer

A SIEM cannot detect behavior that endpoints do not record. Phase 2 establishes the source events and a dedicated transport network before installing a collector. Separating source configuration from ingestion makes troubleshooting explicit: an analyst can first prove that the endpoint generated an event, then prove that the agent forwarded it, and finally prove that the manager decoded and evaluated it.

## Endpoint network pattern

Each monitored endpoint keeps its original workload interface and receives one persistent interface on `soc-telemetry`:

| Domain | Model | Telemetry MAC | Address |
|---|---|---|---|
| `ubuntu-web-01` | `virtio` | `52:54:00:77:30:20` | `10.77.30.20/24` |
| `win11-01` | `e1000e` | `52:54:00:77:30:40` | `10.77.30.40/24` |

No gateway or DNS server is configured on either telemetry interface. The Linux combined netplan file replaces the earlier provisioning-aware boot configuration so an absent provisioning NIC cannot cause startup warnings.

## Linux source configuration

Deploy these files as root:

- `50-soc-endpoint.yaml` to `/etc/netplan/50-cloud-init.yaml` with mode `0600`;
- `soc-lab-tmpfiles.conf` to `/etc/tmpfiles.d/soc-lab.conf`;
- `configure_logging.sh`, then execute it once.

The `auditd` package is installed through the temporary provisioning path. The provisioning interface, route, DNS state, and libvirt network are removed immediately after installation.

## Windows source configuration

Execute `Configure-Phase2.ps1` as Local System through the QEMU guest agent. The script is idempotent: it reuses the telemetry address and forces required policy values without creating accounts or changing firewall rules.

## Troubleshooting order

1. Confirm the persistent libvirt interface and expected MAC.
2. Confirm the guest static address and absence of a default route.
3. Confirm the operating-system audit policy or Audit rules.
4. Generate only the supplied benign validation event.
5. Confirm the raw event locally before investigating forwarding in Phase 3.

This sequence distinguishes network, source-policy, event-generation, collection, and SIEM failures instead of treating the entire alert pipeline as one opaque integration.
