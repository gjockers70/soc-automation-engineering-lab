# MISP deployment

Phase 5 uses the official `MISP/misp-docker` project, pinned to commit `223b675c4480730832f928e113b6f2e5260b450d` and MISP 2.5.44.
Upstream references: [MISP project](https://www.misp-project.org/), [official MISP Docker repository](https://github.com/MISP/misp-docker), and [MISP 2.5.44 release](https://github.com/MISP/MISP/releases/tag/v2.5.44).


## Deployment order

Run these scripts as root on `soc-mgr-01` only while the temporary provisioning interface is attached:

1. `bootstrap_misp.sh` clones and checks out the pinned source.
2. Copy `misp-compose.override.yml` to `/root/misp-compose.override.yml`.
3. `prepare_misp.sh` creates protected runtime secrets, installs the reduced-worker override, validates image tags, and pulls images.
4. `start_misp.sh` starts the official Compose services.
5. Seed the local fixtures from `threat-intel/`.
6. Remove the provisioning interface and stop the provisioning network.
7. `validate_misp.sh` confirms services, API version, address binding, secret mode, and absence of a default route.

The scripts are intentionally separate so operators can distinguish source acquisition, secret generation/image preparation, startup, and steady-state validation.

## Access

The service listens only on the telemetry address:

- HTTPS API/UI: `https://10.77.30.10:8443`
- HTTP redirect: `http://10.77.30.10:8080`

Use an SSH tunnel through the Ubuntu virtualization host for administrative UI access. Do not expose either port on the physical LAN.

## Secrets

Copy `.env.example` only as a key-name reference. Operational values are generated in `/opt/soc-lab/secrets/misp.env`; the file is not transferred back to the workstation and is excluded from Git.

The reduced-worker override is part of the documented mini-PC sizing decision. It runs one default, priority, email, update, and cache worker instead of the upstream higher-throughput defaults.
