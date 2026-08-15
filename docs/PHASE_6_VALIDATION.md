# Phase 6 validation record

Validation date: 2026-08-13

## Platform evidence

- `soc-mgr-01` was increased offline from 12 GiB/4 vCPUs to 24 GiB/8 vCPUs.
- The official Docker source was pinned to commit `c1671863c7a974a195177ab6bc32fb84f8a80834`.
- The resolved images were TheHive 5.7.3, Cassandra 4.1.11, Elasticsearch 8.19.15, and nginx 1.31.1.
- Cassandra, Elasticsearch, and TheHive reported healthy; nginx remained running.
- The authenticated API succeeded with the generated `soc-automation@lab.test` identity in `SOC-LAB`, restricted to the `analyst` profile.
- The documented default administrator password was replaced with a generated value.
- Runtime secrets remained in `/opt/soc-lab/secrets/thehive.env` with mode `0640`.

## Network and capacity evidence

- Direct API: `127.0.0.1:9000` only.
- Reverse proxy: `10.77.30.10:9443` only.
- No TheHive service listened on `0.0.0.0`.
- The provisioning interface was detached and its libvirt network stopped after image pulls.
- `soc-mgr-01` had no default route in steady state.
- After recovery validation, the guest had approximately 11 GiB available memory and 52 GiB free disk.

## Incident evidence

The live case was case number 1 with internal ID `~4329568`. It contained:

- title `SOC-LAB-INC-0001 - Repeated failed logins from synthetic source`;
- severity 2 and native status `InProgress`;
- two reserved synthetic observables;
- four lifecycle tasks;
- triage, evidence, enrichment, recommendation, approval, and closure-requirement context;
- pending approval and no executed response action.

Running the seed again returned the same case ID, two observables, and four tasks. No duplicate case, observable, or task was created.

## Recovery and regression evidence

After rebooting `soc-mgr-01`, TheHive and its data services returned healthy. Wazuh validation passed with a green indexer, MISP returned version 2.5.44, and both Wazuh agents were active. The management guest still had no default route.

## Troubleshooting evidence

Two integration faults were found during the live run:

1. The loopback container mapping serves HTTP, while TLS terminates at nginx. An initial HTTPS request to port 9000 produced protocol errors. The internal URL was corrected to `http://127.0.0.1:9000`; external telemetry access remains HTTPS on port 9443.
2. Observable creation returns a list, and collection reads use TheHive's query endpoint. The seed client was corrected to accept list responses and use `listCase`, `observables`, and `tasks` queries. It then recovered the partially created case without deleting evidence or creating a duplicate.

These corrections are included in the committed implementation and covered by local fixture tests.
