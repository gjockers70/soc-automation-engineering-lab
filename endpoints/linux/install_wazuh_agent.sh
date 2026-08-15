#!/usr/bin/env bash
set -euo pipefail

version="4.14.7-1"
package="/tmp/wazuh-agent_${version}_amd64.deb"
package_index="/tmp/wazuh-packages-index"
base_url="https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent"

curl --fail --location --proto '=https' --tlsv1.2 \
  --output "${package}" "${base_url}/wazuh-agent_${version}_amd64.deb"
curl --fail --location --proto '=https' --tlsv1.2 \
  --output "${package_index}" \
  'https://packages.wazuh.com/4.x/apt/dists/stable/main/binary-amd64/Packages'
expected_sha512="$(python3 - "${package_index}" "${version}" <<'PY'
import pathlib
import sys

index = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
version = sys.argv[2]
for paragraph in index.split("\n\n"):
    fields = dict(line.split(": ", 1) for line in paragraph.splitlines() if ": " in line)
    if fields.get("Package") == "wazuh-agent" and fields.get("Version") == version:
        print(fields["SHA512"])
        break
else:
    raise SystemExit("pinned Wazuh package is missing from repository metadata")
PY
)"
printf '%s  %s\n' "${expected_sha512}" "${package}" | sha512sum --check --strict

WAZUH_MANAGER="10.77.30.10" \
WAZUH_REGISTRATION_SERVER="10.77.30.10" \
WAZUH_AGENT_NAME="ubuntu-web-01" \
  dpkg --install "${package}"

systemctl stop wazuh-agent.service || true
rm -f "${package}" "${package_index}"
printf '%s\n' 'linux_agent_install=pass'
