# Phase 17 Validation

## Static validation

The final validation pipeline checks:

1. Ruff linting across source, tests, and tools.
2. JSON, YAML, XML, requirement pins, workflow security, and documentation links.
3. Native Wazuh/Sigma repository validation.
4. Independent pySigma parsing of every Sigma rule.
5. The complete mocked pytest suite.
6. Final documentation presence and README portfolio sections.
7. Tines, ThreatQ, and Andesite non-equivalence language.
8. Dashboard SVG titles against the provisioned Grafana JSON.
9. Exclusion of prohibited attribution.

## Live validation

The existing read-only management-VM snapshot is rerun after documentation changes to confirm that portfolio cleanup did not alter the deployed platform. The result records aggregate service, capacity, and network-isolation state only.

## Publication validation

After push, GitHub Actions must pass on the final commit. Local HEAD, origin/main, and the private remote branch must identify the same commit, and the working tree must be clean.
