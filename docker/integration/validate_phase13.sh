#!/usr/bin/env bash
set -euo pipefail

/opt/soc-lab/integration/docker/integration/validate_phase12.sh >/dev/null
metrics="$(curl -fsS http://10.77.30.10:8010/metrics)"
required_metrics=(
  soc_alerts_received_total
  soc_alerts_processed_total
  soc_duplicate_suppression_total
  soc_incidents_total
  soc_enrichment_duration_seconds
  soc_workflow_duration_seconds
  soc_dependency_healthy
  soc_playbook_executions
  soc_api_failures_total
  soc_delivery_attempts_total
  soc_delivery_queue_items
  soc_delivery_oldest_pending_seconds
  soc_shuffle_handoffs_total
)
for required in "${required_metrics[@]}"; do
  grep -q "^# TYPE ${required} " <<<"${metrics}"
done
grep -q 'soc_metrics_collection_up{collector="shuffle"} 1' <<<"${metrics}"
! grep -Eqi 'token|password|api[_-]?key|authorization' <<<"${metrics}"
printf 'gateway_metrics=healthy\nshuffle_metrics=healthy\nresponse_action_executed=false\n'
