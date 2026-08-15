#!/usr/bin/env bash
set -euo pipefail

version="4.14.7"
source_root="/opt/soc-lab/wazuh-docker"
runtime_root="/opt/soc-lab/wazuh-single-node"
secrets_root="/opt/soc-lab/secrets"
secrets_file="${secrets_root}/wazuh.env"

install -d -m 0750 -o root -g docker "${secrets_root}"

if [[ ! -f "${secrets_file}" ]]; then
  umask 0027
  cat >"${secrets_file}" <<EOF
WAZUH_INDEXER_ADMIN_PASSWORD=S0c-$(openssl rand -hex 20)
WAZUH_INDEXER_DASHBOARD_PASSWORD=D4sh-$(openssl rand -hex 20)
WAZUH_API_PASSWORD=Api-$(openssl rand -hex 20)
WAZUH_ENROLLMENT_PASSWORD=Enroll-$(openssl rand -hex 20)
EOF
fi
chown root:docker "${secrets_file}"
chmod 0640 "${secrets_file}"

set -a
source "${secrets_file}"
set +a

rm -rf "${runtime_root}"
cp -a "${source_root}/single-node" "${runtime_root}"
chown -R root:docker "${runtime_root}"
chmod 0750 "${runtime_root}"

docker pull "wazuh/wazuh-indexer:${version}"

hash_password() {
  local password="$1"
  docker run --rm "wazuh/wazuh-indexer:${version}" \
      bash /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh \
      -p "${password}" |
    grep -E '^\$2[aby]\$' |
    tail -n 1
}

export WAZUH_INDEXER_ADMIN_HASH
export WAZUH_INDEXER_DASHBOARD_HASH
WAZUH_INDEXER_ADMIN_HASH="$(hash_password "${WAZUH_INDEXER_ADMIN_PASSWORD}")"
WAZUH_INDEXER_DASHBOARD_HASH="$(hash_password "${WAZUH_INDEXER_DASHBOARD_PASSWORD}")"
test -n "${WAZUH_INDEXER_ADMIN_HASH}"
test -n "${WAZUH_INDEXER_DASHBOARD_HASH}"

python3 - <<'PY'
from __future__ import annotations

import os
import re
from pathlib import Path

root = Path("/opt/soc-lab/wazuh-single-node")
compose_path = root / "docker-compose.yml"
compose = compose_path.read_text(encoding="utf-8")

replacements = {
    'INDEXER_PASSWORD=SecretPassword': f'INDEXER_PASSWORD={os.environ["WAZUH_INDEXER_ADMIN_PASSWORD"]}',
    'DASHBOARD_PASSWORD=kibanaserver': f'DASHBOARD_PASSWORD={os.environ["WAZUH_INDEXER_DASHBOARD_PASSWORD"]}',
    'API_PASSWORD=MyS3cr37P450r.*-': f'API_PASSWORD={os.environ["WAZUH_API_PASSWORD"]}',
    '"1514:1514"': '"10.77.30.10:1514:1514"',
    '"1515:1515"': '"10.77.30.10:1515:1515"',
    '"514:514/udp"': '"10.77.30.10:514:514/udp"',
    '"55000:55000"': '"10.77.30.10:55000:55000"',
    '"9200:9200"': '"10.77.30.10:9200:9200"',
    '- 443:5601': '- "10.77.30.10:443:5601"',
}
for old, new in replacements.items():
    if old not in compose:
        raise RuntimeError(f"expected compose value is missing: {old}")
    compose = compose.replace(old, new)

manager_mount = "      - ./config/wazuh_cluster/wazuh_manager.conf:/wazuh-config-mount/etc/ossec.conf"
compose = compose.replace(
    manager_mount,
    manager_mount + "\n      - /opt/soc-lab/secrets/authd.pass:/var/ossec/etc/authd.pass:ro",
)
compose_path.write_text(compose, encoding="utf-8")

users_path = root / "config/wazuh_indexer/internal_users.yml"
users = users_path.read_text(encoding="utf-8")
for username, password_hash in (
    ("admin", os.environ["WAZUH_INDEXER_ADMIN_HASH"]),
    ("kibanaserver", os.environ["WAZUH_INDEXER_DASHBOARD_HASH"]),
):
    pattern = rf"(?ms)^({re.escape(username)}:\n\s+hash:\s+)[^\n]+"
    users, count = re.subn(pattern, rf'\1"{password_hash}"', users, count=1)
    if count != 1:
        raise RuntimeError(f"failed to update hash for {username}")
users_path.write_text(users, encoding="utf-8")

dashboard_path = root / "config/wazuh_dashboard/wazuh.yml"
dashboard = dashboard_path.read_text(encoding="utf-8")
dashboard, count = re.subn(
    r'(?m)^(\s+password:\s+).+$',
    rf'\1"{os.environ["WAZUH_API_PASSWORD"]}"',
    dashboard,
    count=1,
)
if count != 1:
    raise RuntimeError("failed to update the Wazuh API password")
dashboard_path.write_text(dashboard, encoding="utf-8")

manager_path = root / "config/wazuh_cluster/wazuh_manager.conf"
manager = manager_path.read_text(encoding="utf-8")
if "<use_password>no</use_password>" not in manager:
    raise RuntimeError("expected enrollment setting is missing")
manager = manager.replace(
    "<use_password>no</use_password>",
    "<use_password>yes</use_password>",
    1,
)
manager_path.write_text(manager, encoding="utf-8")
PY

printf '%s\n' "${WAZUH_ENROLLMENT_PASSWORD}" >"${secrets_root}/authd.pass"
chown root:docker "${secrets_root}/authd.pass"
chmod 0640 "${secrets_root}/authd.pass"

cd "${runtime_root}"
docker compose -f generate-indexer-certs.yml run --rm generator
docker compose config --quiet
docker compose pull

if grep -R -E 'SecretPassword|MyS3cr37P450r|DASHBOARD_PASSWORD=kibanaserver|<use_password>no</use_password>' \
  docker-compose.yml config/wazuh_dashboard/wazuh.yml config/wazuh_cluster/wazuh_manager.conf; then
  echo "default credential material remains" >&2
  exit 1
fi

echo "wazuh_stack_preparation=pass"
echo "wazuh_version=${version}"
echo "runtime_root=${runtime_root}"
