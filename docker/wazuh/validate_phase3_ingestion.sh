#!/usr/bin/env bash
set -euo pipefail

container="wazuh-single-node-wazuh.manager-1"
alerts="/var/ossec/logs/alerts/alerts.json"

active_agents="$(docker exec "${container}" /var/ossec/bin/agent_control -lc | grep -Ec 'ID: 00[12].*Active')"
test "${active_agents}" -eq 2

docker exec "${container}" test -s "${alerts}"
docker exec "${container}" grep -q 'ubuntu-web-01' "${alerts}"
docker exec "${container}" grep -q '198.51.100.23' "${alerts}"
docker exec "${container}" grep -q 'soc_phase3_test' "${alerts}"

linux_alerts="$(docker exec "${container}" grep -c '198.51.100.23' "${alerts}")"
windows_alerts="$(docker exec "${container}" grep -c 'soc_phase3_test' "${alerts}")"
printf 'active_agents=%s\n' "${active_agents}"
printf 'linux_synthetic_alert_records=%s\n' "${linux_alerts}"
printf 'windows_synthetic_alert_records=%s\n' "${windows_alerts}"
printf '%s\n' 'phase3_ingestion_validation=pass'
