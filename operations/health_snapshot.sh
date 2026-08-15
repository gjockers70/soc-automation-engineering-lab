#!/usr/bin/env bash
set -euo pipefail

# Read-only operational snapshot for the isolated SOC management VM.
DISK_WARN_PERCENT="${SOC_DISK_WARN_PERCENT:-85}"
MEMORY_WARN_MIB="${SOC_MEMORY_WARN_MIB:-1024}"
failures=()
checks=0

record_failure() { failures+=("$1"); }
check_http() {
  local name="$1" url="$2"
  checks=$((checks + 1))
  curl --fail --silent --show-error --max-time 5 --output /dev/null "$url" || record_failure "$name"
}

check_http "integration_gateway" "http://10.77.30.10:8010/health/ready"
check_http "prometheus" "http://127.0.0.1:9090/-/ready"
check_http "grafana" "http://10.77.30.10:3000/api/health"

expected_containers=(
  soc-integration-api soc-prometheus soc-grafana
  wazuh-single-node-wazuh.manager-1 wazuh-single-node-wazuh.indexer-1
  wazuh-single-node-wazuh.dashboard-1 misp-docker-misp-core-1
  thehive shuffle-backend shuffle-frontend
)
for container in "${expected_containers[@]}"; do
  checks=$((checks + 1))
  state="$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || true)"
  [[ "$state" == "running" ]] || record_failure "container:$container"
done

checks=$((checks + 1))
velociraptor_state="$(systemctl is-active velociraptor-server.service 2>/dev/null || true)"
[[ "$velociraptor_state" == "active" ]] || record_failure "velociraptor_server"

disk_percent="$(df -P / | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
checks=$((checks + 1))
(( disk_percent < DISK_WARN_PERCENT )) || record_failure "root_disk"

memory_available_mib="$(awk '/MemAvailable:/ {printf "%d", $2 / 1024}' /proc/meminfo)"
checks=$((checks + 1))
(( memory_available_mib >= MEMORY_WARN_MIB )) || record_failure "available_memory"

default_route_present=false
checks=$((checks + 1))
if ip route show default | grep -q .; then
  default_route_present=true
  record_failure "unexpected_default_route"
fi

status="healthy"
exit_code=0
if (( ${#failures[@]} > 0 )); then status="degraded"; exit_code=1; fi

failures_json='[]'
if (( ${#failures[@]} > 0 )); then
  failures_json="$(printf '%s\n' "${failures[@]}" | jq --raw-input . | jq --slurp .)"
fi

jq --null-input --compact-output \
  --arg timestamp "$(date --utc +%Y-%m-%dT%H:%M:%SZ)" \
  --arg host "$(hostname)" --arg status "$status" \
  --argjson checks "$checks" --argjson failed "${#failures[@]}" \
  --argjson failures "$failures_json" --argjson disk "$disk_percent" \
  --argjson memory "$memory_available_mib" \
  --argjson default_route "$default_route_present" \
  '{schema_version:"1.0",timestamp:$timestamp,host:$host,status:$status,checks:$checks,failed:$failed,failures:$failures,root_disk_used_percent:$disk,memory_available_mib:$memory,default_route_present:$default_route}'
exit "$exit_code"
