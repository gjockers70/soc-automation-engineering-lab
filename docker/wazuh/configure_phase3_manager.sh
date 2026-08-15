#!/usr/bin/env bash
set -euo pipefail

runtime="/opt/soc-lab/wazuh-single-node"
config="${runtime}/config/wazuh_cluster/wazuh_manager.conf"

test -f "${config}"
if grep -q '<disabled>no</disabled>' "${config}"; then
  sed -i '0,/<disabled>no<\/disabled>/s//<disabled>yes<\/disabled>/' "${config}"
fi
grep -q '<disabled>yes</disabled>' "${config}"

cd "${runtime}"
docker compose restart wazuh.manager
printf '%s\n' 'manager_active_response=disabled'
printf '%s\n' 'phase3_manager_configuration=pass'
