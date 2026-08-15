#!/usr/bin/env bash
set -euo pipefail

root="/opt/soc-lab/thehive-docker/prod1-thehive"
runuser -u ubuntu -- docker compose --env-file "${root}/.env" \
  -f "${root}/docker-compose.yml" -f "${root}/compose.soc-lab.yml" up -d
