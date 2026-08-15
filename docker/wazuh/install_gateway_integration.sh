#!/usr/bin/env bash
set -euo pipefail

source_dir=${1:-/root/soc-gateway-integration}
runtime_env=${2:-/root/soc-gateway.env}
container=${WAZUH_MANAGER_CONTAINER:-wazuh-single-node-wazuh.manager-1}
manager_config="/var/ossec/etc/ossec.conf"
manager_backup="/var/ossec/etc/ossec.conf.pre-soc-gateway"

test -f "${source_dir}/custom-soc-gateway"
test -f "${source_dir}/soc_gateway_adapter.py"
test -f "${source_dir}/ossec-integration.xml"
test -f "${runtime_env}"
grep -Eq '^SOC_WEBHOOK_TOKEN=.{32,}$' "${runtime_env}"

docker cp "${source_dir}/custom-soc-gateway" "${container}:/var/ossec/integrations/custom-soc-gateway"
docker cp "${source_dir}/soc_gateway_adapter.py" "${container}:/var/ossec/integrations/soc_gateway_adapter.py"
docker cp "${runtime_env}" "${container}:/var/ossec/etc/soc-gateway.env"
docker cp "${source_dir}/ossec-integration.xml" "${container}:/tmp/soc-gateway-integration.xml"
docker exec "${container}" chown root:wazuh \
  /var/ossec/integrations/custom-soc-gateway \
  /var/ossec/integrations/soc_gateway_adapter.py \
  /var/ossec/etc/soc-gateway.env
docker exec "${container}" chmod 0750 /var/ossec/integrations/custom-soc-gateway
docker exec "${container}" chmod 0640 \
  /var/ossec/integrations/soc_gateway_adapter.py \
  /var/ossec/etc/soc-gateway.env

if ! docker exec "${container}" grep -q '<name>custom-soc-gateway</name>' "${manager_config}"; then
  docker exec "${container}" cp "${manager_config}" "${manager_backup}"
  docker exec "${container}" python3 -c '
from pathlib import Path
config = Path("/var/ossec/etc/ossec.conf")
snippet = Path("/tmp/soc-gateway-integration.xml").read_text().replace(
    "<!-- Merge into the Wazuh manager ossec.conf after local review. -->", ""
).strip()
text = config.read_text()
closing = "</ossec_config>"
if closing not in text:
    raise SystemExit("missing ossec_config closing tag")
config.write_text(text.replace(closing, snippet + "\n" + closing, 1))
'
fi
docker exec "${container}" rm -f /tmp/soc-gateway-integration.xml

if ! docker exec "${container}" /var/ossec/bin/wazuh-analysisd -t; then
  docker exec "${container}" cp "${manager_backup}" "${manager_config}"
  printf '%s\n' 'Wazuh validation failed; the prior manager configuration was restored.' >&2
  exit 1
fi

docker restart "${container}" >/dev/null
for _ in $(seq 1 45); do
  status="$(docker exec "${container}" /var/ossec/bin/wazuh-control status 2>&1 || true)"
  if grep -q 'wazuh-analysisd is running' <<<"${status}" &&
     grep -q 'wazuh-integratord is running' <<<"${status}"; then
    printf '%s\n' 'soc_gateway_integration=installed' 'manager_status=healthy'
    exit 0
  fi
  sleep 2
done

docker logs --tail 80 "${container}" >&2
printf '%s\n' 'Wazuh manager did not recover after integration installation.' >&2
exit 1
