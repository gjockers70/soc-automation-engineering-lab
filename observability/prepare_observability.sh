#!/usr/bin/env bash
set -euo pipefail

repo_source="/root/phase13-files/observability"
deploy_root="/opt/soc-lab/observability"
secrets_root="/opt/soc-lab/secrets"
env_file="${secrets_root}/observability.env"

if [[ ${EUID} -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi

test -f "${repo_source}/compose.yml"
install -d -o root -g docker -m 0750 "${deploy_root}" "${secrets_root}"
rm -rf "${deploy_root}/prometheus" "${deploy_root}/grafana"
cp -a "${repo_source}/prometheus" "${deploy_root}/"
cp -a "${repo_source}/grafana" "${deploy_root}/"
install -o root -g docker -m 0640 "${repo_source}/compose.yml" "${deploy_root}/compose.yml"
install -o root -g docker -m 0750 "${repo_source}/start_observability.sh" "${deploy_root}/start_observability.sh"
install -o root -g docker -m 0750 "${repo_source}/validate_observability.sh" "${deploy_root}/validate_observability.sh"
# Prometheus and Grafana run as non-root users. These files contain only
# non-secret provisioning data, so grant container-readable permissions while
# keeping the generated environment file below restricted to root:docker.
find "${deploy_root}/prometheus" "${deploy_root}/grafana" -type d -exec chmod 0755 {} +
find "${deploy_root}/prometheus" "${deploy_root}/grafana" -type f -exec chmod 0644 {} +
chown -R root:root "${deploy_root}/prometheus" "${deploy_root}/grafana"

admin_password="$(sed -n 's/^GF_SECURITY_ADMIN_PASSWORD=//p' "${env_file}" 2>/dev/null | tr -d '\r' || true)"
if [[ -z "${admin_password}" ]]; then
  admin_password="$(openssl rand -hex 32)"
fi
umask 0077
cat >"${env_file}" <<EOF
GF_SECURITY_ADMIN_USER=socadmin
GF_SECURITY_ADMIN_PASSWORD=${admin_password}
GF_USERS_ALLOW_SIGN_UP=false
GF_AUTH_ANONYMOUS_ENABLED=false
GF_ANALYTICS_REPORTING_ENABLED=false
GF_ANALYTICS_CHECK_FOR_UPDATES=false
GF_UPDATE_CHECK_ENABLED=false
GF_PLUGINS_PREINSTALL_DISABLED=true
EOF
chown root:docker "${env_file}"
chmod 0640 "${env_file}"

docker compose -f "${deploy_root}/compose.yml" config -q
while IFS= read -r image; do
  if ! docker image inspect "${image}" >/dev/null 2>&1; then
    docker pull "${image}"
  fi
done < <(docker compose -f "${deploy_root}/compose.yml" config --images)
printf 'observability_images=prepared\n'
