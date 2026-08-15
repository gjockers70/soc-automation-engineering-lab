#!/usr/bin/env bash
set -euo pipefail

container="wazuh-single-node-wazuh.manager-1"
alerts="/var/ossec/logs/alerts/alerts.json"
rules="/var/ossec/etc/rules/phase4_rules.xml"

docker exec "${container}" test -s "${rules}"
docker exec "${container}" /var/ossec/bin/wazuh-analysisd -t

for rule_id in 100100 100101 100102; do
  docker exec "${container}" grep -q "\"id\":\"${rule_id}\"" "${alerts}"
done

ssh_count="$(docker exec "${container}" grep -c 'SOC1001:' "${alerts}")"
powershell_count="$(docker exec "${container}" grep -c 'SOC1002:' "${alerts}")"
account_count="$(docker exec "${container}" grep -c 'SOC1003:' "${alerts}")"

printf 'soc1001_alert_records=%s\n' "${ssh_count}"
printf 'soc1002_alert_records=%s\n' "${powershell_count}"
printf 'soc1003_alert_records=%s\n' "${account_count}"
printf '%s\n' 'phase4_detection_validation=pass'
