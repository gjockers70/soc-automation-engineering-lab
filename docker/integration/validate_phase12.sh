#!/usr/bin/env bash
set -euo pipefail

private_result="/var/lib/soc-integration/phase12-failure-drills.json"
docker inspect -f '{{.State.Health.Status}}' soc-integration-api | grep -qx healthy
report="$(docker exec soc-integration-api python /app/failure-lab/run_phase12_drills.py --output "${private_result}")"
jq -e '
  .phase == 12 and
  .summary.passed == 8 and
  .summary.failed == 0 and
  ([.scenarios[].id] | sort == ["P12-F01","P12-F02","P12-F03","P12-F04","P12-F05","P12-F06","P12-F07","P12-F08"]) and
  ([.scenarios[].response_action_executed] | all(. == false))
' <<<"${report}" >/dev/null
curl -fsS http://10.77.30.10:8010/health/ready | jq -e '.status == "healthy"' >/dev/null
! ip route show default | grep -q .
printf '%s\n' "${report}"
