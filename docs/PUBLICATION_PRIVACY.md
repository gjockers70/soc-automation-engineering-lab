# Publication Privacy Boundary

This public repository contains only reproducible source, synthetic examples,
sanitized evidence, and isolated-lab addressing. It does not contain the
operator's management-network configuration, physical-host identifiers,
runtime credentials, raw forensic evidence, VM disks, or private deployment
state.

The documented `10.77.30.0/24` range, `.test` identities, VM names, and virtual
service endpoints are part of the synthetic lab architecture. They do not
identify or route to the operator's physical network.

Exact operator-specific publication markers are checked locally using
`.publication-private-markers`, one literal marker per line. That file is
ignored by Git and must never be committed. CI performs complementary generic
checks and verifies that secrets, rendered configuration, raw evidence, disk
images, and environment files remain excluded.

The public Git history begins with the sanitized publication tree. Earlier
private development history and pull-request metadata are not part of this
repository.
