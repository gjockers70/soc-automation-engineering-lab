# Phase 15 validation

Validation is complete when:

- Ruff passes for src, tests, and tools;
- repository JSON, YAML, XML, requirement pins, and Markdown links validate;
- all actions use immutable full commit SHAs;
- the workflow token is read-only and checkout credentials do not persist;
- forbidden secret, deployment, self-hosted, and pull_request_target capabilities are absent;
- actionlint passes after checksum verification;
- native detection validation reports three Sigma rules, three Wazuh rules, and three test events;
- pySigma parses all three Sigma rules;
- all 86 mocked tests pass;
- no workflow step deploys or contacts the lab;
- the pushed GitHub Actions run succeeds.

## Local result

The complete local pipeline passed on August 14, 2026 (America/Chicago). Ruff and actionlint reported no errors. Repository validation passed for 25 JSON, 16 YAML, one XML, 84 Markdown, three requirement, and one workflow file. Both detection validators passed, and all 86 tests passed.

The initial rehearsal failed safely. The repository validator did not yet understand Docker Compose's valid !override tag or list-form workflow action syntax, and Ruff found legacy import ordering. The validator was corrected, import ordering was fixed mechanically, and the complete pipeline then passed. No failing workflow was committed.

The final result also requires the GitHub-hosted run triggered by the Phase 15 push to succeed.
