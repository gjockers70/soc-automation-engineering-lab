# Phase 6 implementation guide

## Objective

Add incident management as a durable system of record, establish a governed lifecycle, and prove that a synthetic investigation can be created through an authenticated API without automating containment.

## Architecture

TheHive runs on `soc-mgr-01` with dedicated Cassandra and Elasticsearch services behind nginx. The VM was increased to 24 GiB RAM and 8 vCPUs before deployment. The direct TheHive listener is loopback-only; nginx binds to `10.77.30.10:9443` because Wazuh already owns port 443.

The official `StrangeBeeCorp/docker` repository is pinned to commit `c1671863c7a974a195177ab6bc32fb84f8a80834`. Its resolved versions are TheHive 5.7.3, Cassandra 4.1.11, Elasticsearch 8.19.15, and nginx 1.31.1. Images are pulled only while the temporary provisioning network is attached. Steady state returns to no default route.

## Smallest useful implementation

1. Start a healthy authenticated TheHive API and UI.
2. Replace the documented first-start administrator credential with a generated value.
3. Create an isolated `SOC-LAB` organisation and automation identity.
4. Keep credentials outside Git with restrictive permissions.
5. Create an idempotent synthetic case with two observables and four lifecycle tasks.
6. Move the case from native `New` to `InProgress` while leaving approval pending.
7. Validate port binding, API authentication, service health, isolation, and reboot recovery.

## Integration boundary

Phase 6 validates direct case creation to isolate TheHive behavior. Wazuh does not yet call TheHive automatically. Shuffle orchestration, webhook handling, retries, and deduplication across incoming alerts are later phases. The local state file only prevents the Phase 6 seed from creating repeated demonstration cases.

## License boundary

The current on-premises release includes a 14-day Platinum trial. Continued operation at $0 requires the free Community license to be requested and activated through the StrangeBee portal before the trial expires. No paid license or cloud service is provisioned by this project.
