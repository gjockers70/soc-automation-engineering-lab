# Container infrastructure

Docker Engine and the Docker Compose v2 plugin are installed inside `soc-mgr-01`. No security platform containers are deployed in Phase 1.

Operational defaults established in this phase:

- bounded JSON log rotation;
- Docker enabled at VM boot;
- unprivileged administrative user added to the Docker group;
- `/opt/soc-lab` reserved for later Compose projects;
- no container ports exposed to the physical LAN.


## Shuffle profile

`docker/shuffle/` overlays the pinned upstream Shuffle 2.2.1 Compose file with telemetry-only bindings, resource limits, generated secrets, and standalone worker mode. The upstream source is pinned by commit during preparation but is not vendored into this repository.

Run preparation only during an approved provisioning window. `start_shuffle.sh`, `restart_shuffle.sh`, and `validate_shuffle.sh` operate the resulting local deployment. The validator requires an authenticated API response, restricted bindings, protected secret permissions, and no default route.

The management VM must retain sufficient RAM and disk for Wazuh, MISP, TheHive, Shuffle, and their databases. These single-node profiles demonstrate integration engineering, not production high availability.

## Integration gateway profile

`docker/integration/` builds and runs the Phase 8 FastAPI gateway. Preparation creates a protected consolidated runtime environment from the existing platform secret files; no credential values are stored in the repository. The service uses host networking to access loopback APIs but binds only to `10.77.30.10:8010`.

The validation script checks authenticated platform readiness, webhook authentication, malformed input, duplicate suppression, protected secret permissions, restricted binding, and the absence of a default route.

Phase 12 rebuilds the gateway from the Phase 10 image with structured integration-failure logging and the safe failure-drill harness. The validator runs eight non-destructive scenarios, checks restored readiness, and leaves the management VM without a default route.

Phase 13 rebuilds the gateway from the Phase 12 image and adds the /metrics endpoint plus a read-only Shuffle execution collector. validate_phase13.sh first preserves all Phase 12 safety checks, then verifies required metric families, collector health, and the absence of credential-like content.
