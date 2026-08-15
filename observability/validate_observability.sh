#!/usr/bin/env bash
set -euo pipefail

deploy_root="/opt/soc-lab/observability"
env_file="/opt/soc-lab/secrets/observability.env"
set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

docker inspect -f '{{.State.Health.Status}}' soc-prometheus | grep -qx healthy
docker inspect -f '{{.State.Health.Status}}' soc-grafana | grep -qx healthy
curl -fsS http://127.0.0.1:9090/-/ready | grep -q 'Prometheus Server is Ready'
targets="$(curl -fsS http://127.0.0.1:9090/api/v1/targets)"
jq -e '[.data.activeTargets[] | select(.labels.job == "soc-integration" and .health == "up")] | length == 1' <<<"${targets}" >/dev/null
rules="$(curl -fsS http://127.0.0.1:9090/api/v1/rules)"
jq -e '[.data.groups[].rules[]] | length >= 7' <<<"${rules}" >/dev/null
query="$(curl -fsS -G --data-urlencode 'query=soc_metrics_collection_up{collector="shuffle"}' http://127.0.0.1:9090/api/v1/query)"
jq -e '.data.result | length == 1 and .[0].value[1] == "1"' <<<"${query}" >/dev/null
curl -fsS http://10.77.30.10:3000/api/health | jq -e '.database == "ok"' >/dev/null
search="$(curl -fsS -u "${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}" 'http://10.77.30.10:3000/api/search?query=SOC%20Platform%20Overview')"
jq -e 'map(select(.uid == "soc-platform-overview")) | length == 1' <<<"${search}" >/dev/null
[[ "$(stat -c '%a' "${env_file}")" == 640 ]]
ss -lnt | grep -q '127.0.0.1:9090'
! ss -lnt | grep -q '0.0.0.0:9090'
ss -lnt | grep -q '10.77.30.10:3000'
! ss -lnt | grep -q '0.0.0.0:3000'
! ip route show default | grep -q .

prometheus_version="$(docker exec soc-prometheus prometheus --version 2>&1 | head -n1)"
grafana_version="$(docker exec soc-grafana grafana server -v 2>&1 | head -n1)"
jq -n --arg prometheus "${prometheus_version}" --arg grafana "${grafana_version}" '{status:"healthy",prometheus:$prometheus,grafana:$grafana,gateway_target:"up",shuffle_collector:"up",rules:7,dashboard:"soc-platform-overview",listeners:{prometheus:"127.0.0.1:9090",grafana:"10.77.30.10:3000"},secret_mode:"0640",default_route:"absent"}'
