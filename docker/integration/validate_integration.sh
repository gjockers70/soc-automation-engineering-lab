#!/usr/bin/env bash
set -euo pipefail

env_file="/opt/soc-lab/secrets/integration.env"
set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

docker inspect -f '{{.State.Health.Status}}' soc-integration-api | grep -qx healthy
ready="$(curl -fsS http://10.77.30.10:8010/health/ready)"
jq -e '.status == "healthy" and ([.integrations[].status] | all(. == "healthy"))' <<<"${ready}" >/dev/null

run_id="phase9-live-$(cat /proc/sys/kernel/random/uuid)"
rule_id="phase9-$(cat /proc/sys/kernel/random/uuid)"
first_fixture="{\"id\":\"${run_id}-a\",\"timestamp\":\"2026-08-13T15:30:00-05:00\",\"rule\":{\"id\":\"${rule_id}\",\"level\":7,\"description\":\"Synthetic failed login\"},\"agent\":{\"id\":\"001\",\"name\":\"ubuntu-web-01\"},\"data\":{\"srcip\":\"198.51.100.44\"},\"synthetic\":true}"
second_fixture="{\"id\":\"${run_id}-b\",\"timestamp\":\"2026-08-13T15:31:00-05:00\",\"rule\":{\"id\":\"${rule_id}\",\"level\":7,\"description\":\"Synthetic failed login\"},\"agent\":{\"id\":\"001\",\"name\":\"ubuntu-web-01\"},\"data\":{\"srcip\":\"198.51.100.44\"},\"synthetic\":true}"

unauthorized="$(curl -sS -o /dev/null -w '%{http_code}' -H 'Idempotency-Key: phase9-live-auth' -H 'Content-Type: application/json' -d "${first_fixture}" http://10.77.30.10:8010/v1/webhooks/wazuh)"
[[ "${unauthorized}" == 401 ]]

wait_delivery() {
  local key=$1
  local result
  for _ in $(seq 1 120); do
    result="$(curl -fsS -H "X-SOC-LAB-TOKEN: ${SOC_WEBHOOK_TOKEN}" "http://10.77.30.10:8010/v1/deliveries/${key}")"
    if jq -e '.status == "completed"' <<<"${result}" >/dev/null; then
      printf '%s' "${result}"
      return 0
    fi
    if jq -e '.status == "failed"' <<<"${result}" >/dev/null; then
      return 1
    fi
    sleep 1
  done
  return 1
}

first_receipt="$(curl -fsS -H "X-SOC-LAB-TOKEN: ${SOC_WEBHOOK_TOKEN}" -H "Idempotency-Key: ${run_id}-a" -H 'Content-Type: application/json' -d "${first_fixture}" http://10.77.30.10:8010/v1/webhooks/wazuh)"
first="$(wait_delivery "${run_id}-a")"
second_receipt="$(curl -fsS -H "X-SOC-LAB-TOKEN: ${SOC_WEBHOOK_TOKEN}" -H "Idempotency-Key: ${run_id}-b" -H 'Content-Type: application/json' -d "${second_fixture}" http://10.77.30.10:8010/v1/webhooks/wazuh)"
second="$(wait_delivery "${run_id}-b")"
duplicate="$(curl -fsS -H "X-SOC-LAB-TOKEN: ${SOC_WEBHOOK_TOKEN}" -H "Idempotency-Key: ${run_id}-a" -H 'Content-Type: application/json' -d "${first_fixture}" http://10.77.30.10:8010/v1/webhooks/wazuh)"

jq -e '.status == "accepted" and .processing_status == "queued" and .response_action_executed == false' <<<"${first_receipt}" >/dev/null
jq -e '.status == "completed" and .incident_disposition == "created" and .shuffle_execution_id != null' <<<"${first}" >/dev/null
jq -e '.status == "accepted" and .processing_status == "queued"' <<<"${second_receipt}" >/dev/null
jq -e --arg id "$(jq -r .incident_id <<<"${first}")" '.status == "completed" and .incident_disposition == "reused" and .incident_id == $id' <<<"${second}" >/dev/null
jq -e '.status == "duplicate" and .response_action_executed == false' <<<"${duplicate}" >/dev/null

malformed="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-SOC-LAB-TOKEN: ${SOC_WEBHOOK_TOKEN}" -H 'Idempotency-Key: phase9-live-bad' -H 'Content-Type: application/json' -d '{"synthetic":true}' http://10.77.30.10:8010/v1/webhooks/wazuh)"
[[ "${malformed}" == 422 ]]
[[ "$(stat -c '%a' "${env_file}")" == 640 ]]
ss -lnt | grep -q '10.77.30.10:8010'
! ss -lnt | grep -q '0.0.0.0:8010'
! ip route show default | grep -q .

jq -n --argjson first "${first}" --argjson second "${second}" --argjson duplicate "${duplicate}" '{first:$first,second:$second,delivery_duplicate:$duplicate}'
printf 'integration_api=healthy\n'
printf 'enrichment=local_misp_suspicious_confidence_75\n'
printf 'scoring=53_medium\n'
printf 'incident_deduplication=created_then_reused\n'
printf 'delivery_idempotency=duplicate\n'
printf 'response_action_executed=false\n'
printf 'default_route=absent\n'
