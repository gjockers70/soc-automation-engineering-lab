# Phase 7 playbooks

This directory contains source-controlled workflow specifications, synthetic inputs, seeding and invocation clients, tests, and sanitized execution results.

## Operator sequence

1. Deploy Shuffle with `docker/shuffle/prepare_shuffle.sh` and `start_shuffle.sh` during an approved provisioning window.
2. Run `seed_workflows.py` on `soc-mgr-01`; it creates or updates the five named workflows and starts their webhooks.
3. Invoke a workflow with `invoke_playbook.py --key <key> --inputs <file>`.
4. Confirm the negative authentication test returns 401, the authenticated call returns 200, and the execution reaches `FINISHED`.
5. Review the execution in Shuffle and confirm the trace and incident identifiers match the gateway delivery. Shuffle never supplies the analyst approval credential.

The fixture is the portable design record. Generated runtime IDs are kept in `/opt/soc-lab/state/phase7-workflows.json`, not Git. Secrets remain in `/opt/soc-lab/secrets/shuffle.env`.

## Troubleshooting

- `401`: confirm the caller uses the generated `X-SOC-LAB-TOKEN` header.
- `EXECUTING` without completion: inspect `shuffle-orborus` and worker logs. This host uses standalone worker mode because Docker live-restore is incompatible with Shuffle's automatic swarm initialization.
- duplicate workflow: rerun the seed and confirm it reports the existing stable name rather than creating another workflow.
- unavailable backend: inspect the loopback API, OpenSearch health, container state, and Compose logs before retrying.

The standalone choice is host-specific, recorded, and validated. It does not imply production availability or redundancy.
