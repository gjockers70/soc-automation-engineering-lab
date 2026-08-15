#!/usr/bin/env bash
set -euo pipefail

stage=/root/phase11-files
runtime=/opt/soc-lab/velociraptor
secrets=/opt/soc-lab/secrets/velociraptor.env
binary=/root/phase11-binaries/velociraptor-linux
expected_sha256=6636020f3ce03ea4eff5d5b96d635c400e51d2636c823a8f0bd458ddc7c4d28a

[[ ${EUID} -eq 0 ]] || { echo "run as root" >&2; exit 1; }
echo "${expected_sha256}  ${binary}" | sha256sum -c -
id velociraptor >/dev/null 2>&1 || useradd --system --home-dir "${runtime}" --shell /usr/sbin/nologin velociraptor
install -d -o velociraptor -g velociraptor -m 0750 "${runtime}"/{datastore,filestore,logs,collections}
install -d -o root -g velociraptor -m 0750 /etc/velociraptor /opt/soc-lab/secrets
chgrp velociraptor /opt/soc-lab
chmod 0750 /opt/soc-lab
install -o root -g root -m 0755 "${binary}" /usr/local/sbin/velociraptor

if [[ ! -f /etc/velociraptor/server.config.yaml ]]; then
  /usr/local/sbin/velociraptor config generate --nobanner \
    --merge_file "${stage}/forensics/velociraptor/server-merge.json" \
    > /etc/velociraptor/server.config.yaml
  chown root:velociraptor /etc/velociraptor/server.config.yaml
  chmod 0640 /etc/velociraptor/server.config.yaml
fi

if [[ ! -f "${secrets}" ]]; then
  umask 0077
  printf 'VELOCIRAPTOR_ADMIN_PASSWORD=%s\n' "$(openssl rand -base64 32 | tr -d '\n')" > "${secrets}"
  chown root:velociraptor "${secrets}"
  chmod 0640 "${secrets}"
fi

set -a
# shellcheck disable=SC1090
source "${secrets}"
set +a
/usr/local/sbin/velociraptor --config /etc/velociraptor/server.config.yaml \
  user add --role administrator soc-admin "${VELOCIRAPTOR_ADMIN_PASSWORD}" >/dev/null

/usr/local/sbin/velociraptor --config /etc/velociraptor/server.config.yaml \
  config client > /etc/velociraptor/client.config.yaml
chown root:velociraptor /etc/velociraptor/client.config.yaml
chmod 0640 /etc/velociraptor/client.config.yaml

if [[ ! -f /etc/velociraptor/api.config.yaml ]]; then
  /usr/local/sbin/velociraptor --config /etc/velociraptor/server.config.yaml \
    config api_client --name soc-triage-api --role investigator \
    /etc/velociraptor/api.config.yaml >/dev/null
  chown root:velociraptor /etc/velociraptor/api.config.yaml
  chmod 0640 /etc/velociraptor/api.config.yaml
fi

install -o root -g root -m 0644 \
  "${stage}/forensics/velociraptor/velociraptor-server.service" \
  /etc/systemd/system/velociraptor-server.service
systemctl daemon-reload
chown -R velociraptor:velociraptor "${runtime}"
systemctl enable --now velociraptor-server.service
printf 'velociraptor_server=prepared\n'
