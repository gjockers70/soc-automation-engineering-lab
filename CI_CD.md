# Continuous integration

Phase 15 provides a validation-only GitHub Actions workflow. It does not deploy infrastructure, publish images, contact the SOC lab, or perform response actions.

## Pipeline

One Ubuntu runner performs these steps:

1. check out the repository with credentials disabled after checkout;
2. install Python 3.12 and pinned dependencies;
3. lint src, tests, and tools with Ruff;
4. validate JSON, YAML, Wazuh XML, requirement pins, relative documentation links, and workflow security boundaries;
5. validate three Sigma rules, three Wazuh rules, and three test events;
6. parse every Sigma rule through pySigma;
7. download actionlint 1.7.12 and verify its official SHA-256 before execution;
8. run all 86 mocked tests.

## Triggers

The workflow runs on pushes to main, pull requests, and manual dispatch. It has a 15-minute timeout and one job to limit consumption. It does not run on a schedule.

## Supply-chain controls

actions/checkout 7.0.1 and actions/setup-python 7.0.0 are pinned to full release commit SHAs rather than mutable major-version tags. Python packages use exact versions. The actionlint Linux archive is accepted only when its SHA-256 matches the published 1.7.12 checksum.

These pins make updates deliberate. A dependency update should be reviewed, validated locally, and committed as an explicit maintenance change.

## Permissions and isolation

The workflow token receives contents: read only. Checkout persistence is disabled. No secrets, write permission, deployment environment, artifact publication, self-hosted runner, or lab address is present.

The CI runner exists on GitHub-hosted infrastructure and cannot reach the isolated 10.77.30.0/24 network. Test clients use mock transports and temporary local files.

## Cost boundary

The workflow uses one short Linux job on GitHub-hosted infrastructure and provisions no paid cloud resource. Repository Actions and billing settings should remain capped and be reviewed periodically rather than enabling paid capacity.

## Local parity

Run the same checks before pushing:

~~~bash
ruff check src tests tools
python tools/validate_repository.py
python detections/validate.py
python detections/validate_with_pysigma.py
actionlint
python -m pytest
~~~

The actionlint binary must be obtained from its official release and verified against the published checksum.
