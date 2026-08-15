#!/usr/bin/env bash
set -euo pipefail

env_file="/opt/soc-lab/secrets/integration.env"
set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a
base="http://10.77.30.10:8010"

docker inspect -f '{{.State.Health.Status}}' soc-integration-api | grep -qx healthy
jq -e '.status == "healthy"' <<<"$(curl -fsS "${base}/health/ready")" >/dev/null

run_id="phase10-live-$(cat /proc/sys/kernel/random/uuid)"
alert="$(jq -n --arg id "${run_id}" '{id:$id,timestamp:"2026-08-13T18:00:00-05:00",rule:{id:"phase10-approval",level:12,description:"Synthetic account activity requiring approval"},agent:{id:"001",name:"ubuntu-web-01"},data:{srcip:"198.51.100.44"},synthetic:true}')"
receipt="$(curl -fsS -H "X-SOC-LAB-TOKEN: ${SOC_WEBHOOK_TOKEN}" -H "Idempotency-Key: ${run_id}" -H 'Content-Type: application/json' -d "${alert}" "${base}/v1/webhooks/wazuh")"
incident_id="$(jq -r .incident_id <<<"${receipt}")"
[[ -n "${incident_id}" && "${incident_id}" != null ]]

identity_before="$(curl -fsS -H "X-SOC-APPROVAL-TOKEN: ${SOC_APPROVAL_TOKEN}" "${base}/v1/lab-identities/soc-response-test")"
proposal="$(jq -n --arg incident "${incident_id}" '{incident_id:$incident,action:"disable_synthetic_account",target:"soc-response-test",reason:"Repeated suspicious authentication in the isolated lab.",evidence:["synthetic Wazuh alert","local MISP enrichment","score above review threshold"],confidence:0.92}')"

create_and_decide() {
  local decision="$1"
  local created approval_id result
  created="$(curl -fsS -H "X-SOC-LAB-TOKEN: ${SOC_WEBHOOK_TOKEN}" -H 'Content-Type: application/json' -d "${proposal}" "${base}/v1/approvals")"
  approval_id="$(jq -r .approval_id <<<"${created}")"
  result="$(curl -fsS -H "X-SOC-APPROVAL-TOKEN: ${SOC_APPROVAL_TOKEN}" -H 'Content-Type: application/json' -d "{\"decision\":\"${decision}\",\"analyst\":\"analyst.one\",\"note\":\"Reviewed synthetic evidence in the isolated lab.\"}" "${base}/v1/approvals/${approval_id}/decision")"
  jq -c -n --argjson created "${created}" --argjson result "${result}" '{created:$created,result:$result}'
}

rejected="$(create_and_decide reject)"
jq -e '.result.status == "reject" and .result.response_action_executed == false' <<<"${rejected}" >/dev/null
state_after_reject="$(curl -fsS -H "X-SOC-APPROVAL-TOKEN: ${SOC_APPROVAL_TOKEN}" "${base}/v1/lab-identities/soc-response-test")"
jq -e --arg expected "$(jq -r .state <<<"${identity_before}")" '.state == $expected' <<<"${state_after_reject}" >/dev/null

escalated="$(create_and_decide escalate)"
jq -e '.result.status == "escalate" and .result.response_action_executed == false' <<<"${escalated}" >/dev/null
state_after_escalate="$(curl -fsS -H "X-SOC-APPROVAL-TOKEN: ${SOC_APPROVAL_TOKEN}" "${base}/v1/lab-identities/soc-response-test")"
jq -e --arg expected "$(jq -r .state <<<"${identity_before}")" '.state == $expected' <<<"${state_after_escalate}" >/dev/null

approved_pair="$(create_and_decide approve)"
approved="$(jq -c .result <<<"${approved_pair}")"
approval_id="$(jq -r .approval_id <<<"${approved}")"
jq -e '.status == "approve" and (.execution_result == "disabled" or .execution_result == "already_disabled")' <<<"${approved}" >/dev/null
repeated="$(curl -fsS -H "X-SOC-APPROVAL-TOKEN: ${SOC_APPROVAL_TOKEN}" -H 'Content-Type: application/json' -d '{"decision":"approve","analyst":"analyst.one","note":"Reviewed synthetic evidence in the isolated lab."}' "${base}/v1/approvals/${approval_id}/decision")"
jq -e --arg id "${approval_id}" '.approval_id == $id and .status == "approve"' <<<"${repeated}" >/dev/null

identity_after="$(curl -fsS -H "X-SOC-APPROVAL-TOKEN: ${SOC_APPROVAL_TOKEN}" "${base}/v1/lab-identities/soc-response-test")"
jq -e '.state == "disabled"' <<<"${identity_after}" >/dev/null
unauthorized="$(curl -sS -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -d '{"decision":"approve","analyst":"analyst.one","note":"Unauthorized test."}' "${base}/v1/approvals/${approval_id}/decision")"
[[ "${unauthorized}" == 401 ]]
conflict="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-SOC-APPROVAL-TOKEN: ${SOC_APPROVAL_TOKEN}" -H 'Content-Type: application/json' -d '{"decision":"reject","analyst":"analyst.one","note":"Conflicting test decision."}' "${base}/v1/approvals/${approval_id}/decision")"
[[ "${conflict}" == 409 ]]
off_allowlist="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-SOC-LAB-TOKEN: ${SOC_WEBHOOK_TOKEN}" -H 'Content-Type: application/json' -d "$(sed 's/soc-response-test/real-user/' <<<"${proposal}")" "${base}/v1/approvals")"
[[ "${off_allowlist}" == 422 ]]
! getent passwd soc-response-test >/dev/null
[[ "$(stat -c '%a' "${env_file}")" == 640 ]]
! ip route show default | grep -q .

jq -n --argjson receipt "${receipt}" --argjson before "${identity_before}" --argjson rejected "${rejected}" --argjson escalated "${escalated}" --argjson approved "${approved}" --argjson repeated "${repeated}" --argjson after "${identity_after}" --arg unauthorized "${unauthorized}" --arg conflict "${conflict}" --arg off_allowlist "${off_allowlist}" '{alert_receipt:$receipt,identity_before:$before,rejected:$rejected,escalated:$escalated,approved:$approved,repeated_approval:$repeated,identity_after:$after,http_checks:{missing_approval_token:$unauthorized,conflicting_decision:$conflict,off_allowlist_target:$off_allowlist},os_account_present:false,default_route:"absent"}'
