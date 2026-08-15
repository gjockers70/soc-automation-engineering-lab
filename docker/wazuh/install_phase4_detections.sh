#!/usr/bin/env bash
set -euo pipefail

container="wazuh-single-node-wazuh.manager-1"
source_file="/root/phase4_rules.xml"
target_file="/var/ossec/etc/rules/phase4_rules.xml"

test -s "${source_file}"
docker cp "${source_file}" "${container}:${target_file}"
docker exec "${container}" chown wazuh:wazuh "${target_file}"
docker exec "${container}" chmod 0640 "${target_file}"
docker exec "${container}" /var/ossec/bin/wazuh-analysisd -t

wait_for_manager() {
  local status
  for attempt in $(seq 1 45); do
    status="$(docker exec "${container}" /var/ossec/bin/wazuh-control status 2>&1 || true)"
    if grep -q 'wazuh-analysisd is running' <<<"${status}" &&
       grep -q 'wazuh-remoted is running' <<<"${status}" &&
       grep -q 'wazuh-db is running' <<<"${status}" &&
       grep -q 'wazuh-apid is running' <<<"${status}"; then
      return 0
    fi
    sleep 2
  done
  return 1
}

docker restart "${container}" >/dev/null
if wait_for_manager; then
  printf '%s\n' 'manager_start_attempt=initial'
  printf '%s\n' 'phase4_detection_install=pass'
  exit 0
fi

printf '%s\n' 'Initial manager start was incomplete; performing one bounded restart.' >&2
docker restart "${container}" >/dev/null
if wait_for_manager; then
  printf '%s\n' 'manager_start_attempt=recovery'
  printf '%s\n' 'phase4_detection_install=pass'
  exit 0
fi

docker logs --tail 80 "${container}" >&2
printf '%s\n' 'Wazuh manager core services did not become ready.' >&2
exit 1
