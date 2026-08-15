# Phase 5 implementation guide

## Objective

Add a local threat-intelligence platform and a consistent enrichment contract without introducing paid APIs, public exposure, or automatic response.

## Architecture

MISP runs beside Wazuh on `soc-mgr-01` because the 12 GiB management VM had sufficient measured headroom for the reduced lab profile. The official Compose project supplies MariaDB, Redis, MISP core, MISP modules, and local mail support. A repository-owned override reduces MISP to one worker in each queue.

The deployment is pinned to official MISP 2.5.44 images and the official `misp-docker` commit `223b675c4480730832f928e113b6f2e5260b450d`. Container ports bind to `10.77.30.10`, not all interfaces. Temporary NAT is used only for clone/image pulls and is removed afterward.

## Smallest useful implementation

1. Deploy a healthy local MISP API.
2. Create protected generated credentials on the management VM.
3. Seed one unpublished event with IP, domain, URL, and SHA-256 attributes.
4. Reject malformed indicators before lookup.
5. Query MISP through its REST API.
6. Normalize matches and misses to one JSON contract.
7. Prove the seed is idempotent and the steady state has no default route.

## IOC safety

The address `198.51.100.44` is from TEST-NET-2. Domains use the reserved `.test` suffix. The file hash is derived from the benign text `SOC-LAB-BENIGN-FILE-SIMULATION`; no malware or executable sample is stored or run.

## Operator sequence

The scripts under `docker/misp/` implement source pinning, secret preparation, startup, and validation. The scripts under `threat-intel/scripts/` implement idempotent fixture creation and normalized lookup. Operational credentials remain only in `/opt/soc-lab/secrets/misp.env`.

External feeds and synchronization are deliberately excluded. Their reliability, licensing, distribution, expiry, and network dependencies require a later explicit design decision.
