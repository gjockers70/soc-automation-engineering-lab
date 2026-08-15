#!/usr/bin/env bash
set -euo pipefail

root="/opt/soc-lab/misp-docker"
secrets_root="/opt/soc-lab/secrets"
env_file="${secrets_root}/misp.env"
override_source="${MISP_OVERRIDE_FILE:-/root/misp-compose.override.yml}"

install -d -m 0750 -o root -g docker "${secrets_root}"
if [[ ! -f "${env_file}" ]]; then
  umask 0027
  cat >"${env_file}" <<EOF
CORE_TAG=v2.5.44
CORE_RUNNING_TAG=v2.5.44-slim
MODULES_TAG=v3.0.9
MODULES_RUNNING_TAG=v3.0.9-slim
GUARD_TAG=v1.2
BASE_URL=https://10.77.30.10:8443
CORE_HTTP_PORT=10.77.30.10:8080
CORE_HTTPS_PORT=10.77.30.10:8443
ADMIN_EMAIL=admin@soc-lab.test
ADMIN_ORG=SOC-LAB
ADMIN_PASSWORD=Misp-$(openssl rand -hex 20)
ADMIN_KEY=$(openssl rand -hex 20)
DISABLE_PRINTING_PLAINTEXT_CREDENTIALS=true
MYSQL_USER=misp
MYSQL_PASSWORD=$(openssl rand -hex 24)
MYSQL_ROOT_PASSWORD=$(openssl rand -hex 24)
MYSQL_DATABASE=misp
REDIS_PASSWORD=$(openssl rand -hex 24)
ENABLE_REDIS_EMPTY_PASSWORD=false
ENABLE_BACKGROUND_UPDATES=false
ENABLE_DB_SETTINGS=true
DISABLE_IPV6=true
TZ=UTC
NUM_WORKERS_DEFAULT=1
NUM_WORKERS_PRIO=1
NUM_WORKERS_EMAIL=1
NUM_WORKERS_UPDATE=1
NUM_WORKERS_CACHE=1
PHP_MEMORY_LIMIT=1024M
PHP_FCGI_CHILDREN=3
PHP_FCGI_START_SERVERS=1
PHP_FCGI_SPARE_SERVERS=1
INNODB_BUFFER_POOL_SIZE=512M
INNODB_LOG_FILE_SIZE=128M
INNODB_READ_IO_THREADS=4
INNODB_WRITE_IO_THREADS=2
EOF
fi

# Keep existing generated secrets while adding required static settings when
# this script is rerun after an upstream compose-file change.
ensure_setting() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "${env_file}"; then
    printf '%s=%s\n' "${key}" "${value}" >>"${env_file}"
  fi
}
ensure_setting "GUARD_TAG" "v1.2"

# MISP requires a 40-character alphanumeric authentication key. Rotate only
# an invalid generated value, preserving a valid existing lab credential.
admin_key="$(sed -n 's/^ADMIN_KEY=//p' "${env_file}")"
if [[ ! "${admin_key}" =~ ^[[:alnum:]]{40}$ ]]; then
  replacement_key="$(openssl rand -hex 20)"
  if grep -q '^ADMIN_KEY=' "${env_file}"; then
    sed -i "s/^ADMIN_KEY=.*/ADMIN_KEY=${replacement_key}/" "${env_file}"
  else
    printf 'ADMIN_KEY=%s\n' "${replacement_key}" >>"${env_file}"
  fi
fi

chown root:docker "${env_file}"
chmod 0640 "${env_file}"
install -m 0640 -o root -g docker "${env_file}" "${root}/.env"

install -m 0644 -o root -g root "${override_source}" "${root}/docker-compose.override.yml"
cd "${root}"
docker manifest inspect ghcr.io/misp/misp-docker/misp-core:v2.5.44-slim >/dev/null
docker manifest inspect ghcr.io/misp/misp-docker/misp-modules:v3.0.9-slim >/dev/null
docker compose config --quiet
docker compose pull

if grep -E '^(ADMIN_PASSWORD=admin|MYSQL_PASSWORD=example|MYSQL_ROOT_PASSWORD=password|REDIS_PASSWORD=redispassword)$' .env; then
  printf '%s\n' 'default credential remains' >&2
  exit 1
fi
printf '%s\n' 'misp_preparation=pass'
