#!/usr/bin/env bash
set -euo pipefail

runtime_root="/opt/soc-lab/wazuh-single-node"
cd "${runtime_root}"

docker compose config --quiet
docker compose up -d

echo "wazuh_stack_start=requested"
docker compose ps
