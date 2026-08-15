#!/usr/bin/env bash
set -euo pipefail

stage=/root/phase11-client
expected_sha256=6636020f3ce03ea4eff5d5b96d635c400e51d2636c823a8f0bd458ddc7c4d28a
[[ ${EUID} -eq 0 ]] || { echo "run as root" >&2; exit 1; }
echo "${expected_sha256}  ${stage}/velociraptor-linux" | sha256sum -c -
install -o root -g root -m 0755 "${stage}/velociraptor-linux" /usr/local/sbin/velociraptor
install -d -o root -g root -m 0750 /etc/velociraptor
install -o root -g root -m 0600 "${stage}/client.config.yaml" /etc/velociraptor/client.config.yaml
install -o root -g root -m 0644 "${stage}/velociraptor-linux-client.service" /etc/systemd/system/velociraptor-client.service
systemctl daemon-reload
[[ -e /etc/velociraptor.writeback.yaml ]] || install -o root -g root -m 0600 /dev/null /etc/velociraptor.writeback.yaml
[[ -e /etc/velociraptor.writeback.yaml.bak ]] || install -o root -g root -m 0600 /dev/null /etc/velociraptor.writeback.yaml.bak
systemctl enable --now velociraptor-client.service
printf 'velociraptor_linux_client=installed\n'
