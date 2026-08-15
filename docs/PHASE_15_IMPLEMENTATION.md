# Phase 15 implementation

## Objective

Turn the local quality gates into a repeatable GitHub Actions workflow while preserving the zero-cost goal, private-lab isolation, least privilege, and a strict no-deployment boundary.

## Workflow design

The workflow uses one Ubuntu job with a 15-minute timeout. actions/checkout and actions/setup-python are pinned to full release SHAs. Dependencies are exact-version pinned and pip caching uses the three requirements files.

Ruff checks Python syntax, undefined names, import correctness, and import ordering. A repository-owned validator parses JSON, YAML including Docker Compose override tags, Wazuh XML, requirement pins, relative Markdown links, action pins, token permission, and forbidden CI capabilities.

Detection validation runs both the repository's structural validator and pySigma. actionlint is downloaded from the official 1.7.12 release, verified using its published Linux archive checksum, and run before pytest.

## Security boundary

The workflow has contents: read permission and does not persist checkout credentials. It has no secret context, write permission, deployment environment, artifact upload, self-hosted runner, pull_request_target trigger, public deployment, or private-lab access.

## Local validation

The full sequence passed locally before publication. The validator counted 25 JSON files, 16 YAML files, one Wazuh XML file, 84 Markdown files, three requirement files, and one workflow. All detection checks and all 86 tests passed.
