#!/usr/bin/env bash
set -euo pipefail

root="/opt/soc-lab/thehive-docker/prod1-thehive"
env_file="/opt/soc-lab/secrets/thehive.env"
test -f "${env_file}"
set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

runuser -u ubuntu -- docker compose --env-file "${root}/.env" \
  -f "${root}/docker-compose.yml" -f "${root}/compose.soc-lab.yml" ps --status running

curl -ksS --fail -u "${THEHIVE_USERNAME}:${THEHIVE_PASSWORD}" \
  -H "X-Organisation: ${THEHIVE_ORGANISATION}" \
  "${THEHIVE_URL}/api/v1/user/current" | jq -e '.login == env.THEHIVE_USERNAME' >/dev/null

ss -lnt | grep -q '127.0.0.1:9000'
ss -lnt | grep -q '10.77.30.10:9443'
! ss -lnt | grep -qE '0\.0\.0\.0:(9000|9443)'
[[ "$(stat -c '%a' "${env_file}")" == 640 ]]
! ip route show default | grep -q .

printf 'thehive_api=healthy\n'
printf 'thehive_direct_api=loopback-only\n'
printf 'thehive_ui=10.77.30.10:9443\n'
printf 'default_route=absent\n'
