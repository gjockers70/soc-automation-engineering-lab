#!/usr/bin/env bash
set -euo pipefail

wazuh_version="v4.14.7"
install_root="/opt/soc-lab"
repository="${install_root}/wazuh-docker"

install -d -m 0750 -o root -g docker "${install_root}"

if [[ ! -d "${repository}/.git" ]]; then
  git clone --depth 1 --branch "${wazuh_version}" \
    https://github.com/wazuh/wazuh-docker.git "${repository}"
fi

actual_version="$(git -C "${repository}" describe --tags --exact-match)"
test "${actual_version}" = "${wazuh_version}"

cat >/etc/sysctl.d/90-wazuh-indexer.conf <<'EOF'
vm.max_map_count=262144
EOF
sysctl --system >/dev/null

echo "wazuh_source_version=${actual_version}"
echo "vm.max_map_count=$(sysctl -n vm.max_map_count)"
