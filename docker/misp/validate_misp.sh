#!/usr/bin/env bash
set -euo pipefail

root="/opt/soc-lab/misp-docker"
env_file="/opt/soc-lab/secrets/misp.env"
set -a
source "${env_file}"
set +a

cd "${root}"
for container in misp-docker-db-1 misp-docker-redis-1 misp-docker-misp-modules-1 misp-docker-misp-core-1; do
  test "$(docker inspect --format '{{.State.Running}}' "${container}")" = "true"
done

response_file="$(mktemp)"
trap 'rm -f "${response_file}"' EXIT
api_ready=false
for _ in {1..30}; do
  if curl --silent --fail --insecure \
    --header "Authorization: ${ADMIN_KEY}" \
    --header 'Accept: application/json' \
    --output "${response_file}" \
    https://10.77.30.10:8443/servers/getVersion.json; then
    api_ready=true
    break
  fi
  sleep 2
done
test "${api_ready}" = "true"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1], encoding="utf-8")); assert d.get("version", "").startswith("2.5."); print("misp_version=" + d["version"])' "${response_file}"

for port in 8080 8443; do
  ss -lnt | grep -q "10.77.30.10:${port}"
done
! ip -4 route show default | grep -q .
test "$(stat -c '%a' "${env_file}")" = "640"
printf '%s\n' 'misp_validation=pass'
printf '%s\n' 'default_route=absent'
printf '%s\n' 'service_bind_address=10.77.30.10'
