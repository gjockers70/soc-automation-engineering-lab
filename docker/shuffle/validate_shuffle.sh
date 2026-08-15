#!/usr/bin/env bash
set -euo pipefail

root="/opt/soc-lab/shuffle"
secrets="/opt/soc-lab/secrets/shuffle.env"
set -a
# shellcheck disable=SC1090
source "${secrets}"
set +a

runuser -u ubuntu -- docker compose --env-file "${secrets}" \
  -f "${root}/docker-compose.yml" -f "${root}/compose.soc-lab.yml" ps --status running
curl -fsS -H "Authorization: Bearer ${SHUFFLE_DEFAULT_APIKEY}" \
  http://127.0.0.1:5001/api/v1/workflows >/tmp/shuffle-workflows.json
jq -e 'type == "array" or .success == true' /tmp/shuffle-workflows.json >/dev/null

ss -lnt | grep -q '127.0.0.1:5001'
ss -lnt | grep -q '10.77.30.10:3001'
! ss -lnt | grep -qE '0\.0\.0\.0:(3001|5001|9200)'
[[ "$(stat -c '%a' "${secrets}")" == 640 ]]
! ip route show default | grep -q .

printf 'shuffle_api=healthy\n'
printf 'shuffle_backend=loopback-only\n'
printf 'shuffle_ui=10.77.30.10:3001\n'
printf 'shuffle_opensearch=internal-only\n'
printf 'default_route=absent\n'
