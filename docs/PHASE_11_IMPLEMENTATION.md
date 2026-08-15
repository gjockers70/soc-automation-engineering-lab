# Phase 11 Implementation

Phase 11 deploys Velociraptor 0.77.1 as a native service on `soc-mgr-01` and as clients on `ubuntu-web-01` and `win11-01`. The Linux and Windows binaries are pinned to SHA-256 values published on the official Velociraptor downloads page and are staged through the Ubuntu virtualization host before the isolated VMs receive them.

The frontend and GUI bind only to `10.77.30.10`; the automation API remains on loopback. Generated server configuration, internal PKI, API certificate, and administrator credential stay outside Git with restricted permissions. The native server uses a file datastore and a 1.5 GiB systemd memory ceiling, avoiding another database service on the resource-constrained management VM.

The Linux client runs as root because several forensic sources require privileged operating-system access. Its systemd unit applies `NoNewPrivileges`, a CPU quota, memory ceiling, filesystem protection, and narrow write exceptions for client identity state. The Windows client uses Velociraptor's supported self-installing service mechanism and runs as Local System.

The scripted triage run collects six artifacts from each endpoint with a 20% collection CPU limit, five-minute timeout, and two-minute progress timeout. File uploads remain disabled. Raw collection containers stay on the private management VM.
