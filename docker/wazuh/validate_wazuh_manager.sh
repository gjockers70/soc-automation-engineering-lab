#!/usr/bin/env bash
set -euo pipefail

runtime_root="/opt/soc-lab/wazuh-single-node"
secrets_file="/opt/soc-lab/secrets/wazuh.env"

set -a
source "${secrets_file}"
set +a

cd "${runtime_root}"
expected_services=(wazuh.manager wazuh.indexer wazuh.dashboard)
for service in "${expected_services[@]}"; do
  container_id="$(docker compose ps -q "${service}")"
  test -n "${container_id}"
  test "$(docker inspect --format '{{.State.Running}}' "${container_id}")" = "true"
done

cluster_status="$(
  curl --silent --show-error --fail --insecure \
    --user "admin:${WAZUH_INDEXER_ADMIN_PASSWORD}" \
    https://10.77.30.10:9200/_cluster/health |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])'
)"
case "${cluster_status}" in
  green|yellow) ;;
  *) echo "unexpected indexer status: ${cluster_status}" >&2; exit 1 ;;
esac

dashboard_code="$(
  curl --silent --output /dev/null --write-out '%{http_code}' --insecure \
    https://10.77.30.10/
)"
case "${dashboard_code}" in
  200|302) ;;
  *) echo "unexpected dashboard status: ${dashboard_code}" >&2; exit 1 ;;
esac

if ip -4 route show default | grep -q .; then
  echo "unexpected default route" >&2
  exit 1
fi

for port in 443 1514 1515 55000 9200; do
  ss -lnt | grep -q "10.77.30.10:${port}"
done

test "$(stat -c '%a' "${secrets_file}")" = "640"
test "$(stat -c '%a' /opt/soc-lab/secrets/authd.pass)" = "640"

echo "wazuh_manager_validation=pass"
echo "indexer_status=${cluster_status}"
echo "dashboard_http_status=${dashboard_code}"
echo "default_route=absent"
echo "service_bind_address=10.77.30.10"
