# TheHive deployment

Phase 6 uses the official StrangeBee Docker project pinned to commit `c1671863c7a974a195177ab6bc32fb84f8a80834`. The pinned stack resolves to TheHive 5.7.3, Cassandra 4.1.11, Elasticsearch 8.19.15, and nginx 1.31.1.

The management VM is sized at 24 GiB RAM and 8 vCPUs for this profile. The direct application port binds only to loopback. The reverse-proxy UI/API binds only to `10.77.30.10:9443`, avoiding Wazuh's existing port 443.

## Operator order

1. Attach the temporary provisioning interface.
2. Run `bootstrap_thehive.sh`.
3. Copy `thehive-compose.override.yml` to `/root/thehive-compose.override.yml`.
4. Run `prepare_thehive.sh` and `start_thehive.sh`.
5. Create `/root/thehive-bootstrap.env` with mode `0600` and the key `THEHIVE_INITIAL_ADMIN_PASSWORD`; supply the current first-start value out of band.
6. Run `bootstrap_access.sh` to rotate that credential and create the lab organisation, generated credentials, and API key.
7. Seed the synthetic case from `incidents/scripts/seed_case.py`.
8. Remove the provisioning interface and stop its network.
9. Run `validate_thehive.sh` and the full platform validation.

Runtime credentials remain in `/opt/soc-lab/secrets/thehive.env` with mode `0640`. The repository contains key names only.

## Licensing boundary

The current on-premises release starts with a 14-day Platinum trial. Continued $0 use requires a free Community license requested and activated through StrangeBee. The deployment does not purchase or provision a paid license.
