#!/usr/bin/env bash
set -euo pipefail

cd /opt/soc-lab/misp-docker
docker compose up -d

for attempt in $(seq 1 90); do
  if curl --silent --show-error --fail --insecure \
      https://10.77.30.10:8443/users/heartbeat >/dev/null 2>&1; then
    printf '%s\n' 'misp_start=pass'
    exit 0
  fi
  sleep 5
done

docker compose ps >&2
docker compose logs --tail 100 misp-core >&2
printf '%s\n' 'MISP did not become healthy.' >&2
exit 1
