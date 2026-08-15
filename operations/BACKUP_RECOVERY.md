# Backup and Recovery

## Objectives

Lab targets are RPO 24 hours for configuration/state and RTO 4 hours for the alert-to-case pipeline during an attended exercise. These are design targets, not measured production commitments.

## Scope

Back up Compose/configuration files, generated detection configuration, gateway audit/state database, Wazuh configuration and lab alerts, MISP database and attachments, TheHive datastores, Shuffle workflows/state, Velociraptor configuration/datastore, and observability configuration where reconstruction would lose evidence.

Runtime credentials require a separate encrypted backup outside Git. Raw forensic collections stay restricted. Images, caches, and reproducible packages need not be copied if immutable versions and checksums are recorded.

The VM recovery copies protect whole-disk rollback, but they are not application-consistent backups and share the physical host. Production needs encrypted off-host copies and tested datastore-native procedures.

## Backup procedure

1. Confirm capacity and record versions and UTC start time.
2. Quiesce or use each datastore's supported snapshot/export method.
3. Export configuration without secret values.
4. Store credential backups separately with restricted access.
5. Create a manifest with item, version, timestamp, size, and SHA-256.
6. Verify the archive is readable; do not rely on a successful copy alone.
7. Record retention and expiry. Never commit the archive.

## Restore procedure

1. Declare capability and restore point; preserve failed state for analysis.
2. Confirm exact target paths and free space before overwriting anything.
3. Restore datastores before consumers using the dependency order.
4. Restore secrets from the protected source and verify permissions.
5. Start one layer at a time and run component validators.
6. Run the health snapshot and one end-to-end synthetic alert.
7. Verify deduplication, case integrity, audit continuity, and approval history.
8. Document recovery time, data gap, exceptions, and follow-up.

## Test cadence

Perform a monthly configuration restore check and quarterly application-state exercise when capacity permits. A backup is not usable until restore is demonstrated without weakening isolation or approval controls.
