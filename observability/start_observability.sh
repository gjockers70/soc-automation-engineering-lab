#!/usr/bin/env bash
set -euo pipefail

docker compose -f /opt/soc-lab/observability/compose.yml up -d --force-recreate
