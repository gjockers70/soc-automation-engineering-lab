#!/usr/bin/env bash
set -euo pipefail
docker compose -f /opt/soc-lab/integration/docker/integration/compose.yml up -d
