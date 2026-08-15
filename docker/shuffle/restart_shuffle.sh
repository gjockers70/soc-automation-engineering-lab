#!/usr/bin/env bash
set -euo pipefail

root="/opt/soc-lab/shuffle"
secrets="/opt/soc-lab/secrets/shuffle.env"
runuser -u ubuntu -- docker compose --env-file "${secrets}" \
  -f "${root}/docker-compose.yml" -f "${root}/compose.soc-lab.yml" \
  up -d --force-recreate backend orborus frontend
