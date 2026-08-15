#!/usr/bin/env bash
set -euo pipefail

root="/opt/soc-lab/shuffle"
secrets="/opt/soc-lab/secrets/shuffle.env"
override_source="/root/shuffle-compose.override.yml"
override_target="${root}/compose.soc-lab.yml"
apps_source="/opt/soc-lab/shuffle-python-apps/shuffle-tools/1.2.0"
apps_target="/opt/soc-lab/shuffle-apps/shuffle-tools/1.2.0"

if [[ ${EUID} -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi
test -f "${root}/docker-compose.yml"
test -f "${override_source}"
test -f "${apps_source}/api.yaml"

memory_kib=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
free_kib=$(df --output=avail / | tail -1 | tr -d ' ')
(( memory_kib >= 8 * 1024 * 1024 )) || { echo "Shuffle profile requires 8 GiB available memory" >&2; exit 1; }
(( free_kib >= 35 * 1024 * 1024 )) || { echo "Shuffle profile requires 35 GiB free disk" >&2; exit 1; }

install -d -o root -g docker -m 0750 /opt/soc-lab/secrets
install -d -o ubuntu -g ubuntu -m 0750 /opt/soc-lab/shuffle-database \
  /opt/soc-lab/shuffle-apps /opt/soc-lab/shuffle-files
install -d -o ubuntu -g ubuntu -m 0750 "$(dirname "${apps_target}")"
if [[ ! -d "${apps_target}" ]]; then
  cp -a "${apps_source}" "${apps_target}"
fi
chown -R ubuntu:ubuntu /opt/soc-lab/shuffle-apps /opt/soc-lab/shuffle-files
chown -R 1000:1000 /opt/soc-lab/shuffle-database

if [[ ! -f "${secrets}" ]]; then
  admin_password="$(openssl rand -hex 24)Aa1!"
  opensearch_password="$(openssl rand -hex 24)Aa1!"
  api_key="$(cat /proc/sys/kernel/random/uuid)"
  webhook_token="$(openssl rand -hex 32)"
  encryption_modifier="$(openssl rand -hex 32)"
  umask 0077
  cat >"${secrets}" <<EOF
ENVIRONMENT_NAME=Shuffle
SHUFFLE_DEFAULT_USERNAME=soc-admin
SHUFFLE_DEFAULT_PASSWORD=${admin_password}
SHUFFLE_DEFAULT_APIKEY=${api_key}
SHUFFLE_ENCRYPTION_MODIFIER=${encryption_modifier}
SHUFFLE_OPENSEARCH_PASSWORD=${opensearch_password}
OPENSEARCH_INITIAL_ADMIN_PASSWORD=${opensearch_password}
SHUFFLE_WEBHOOK_TOKEN=${webhook_token}
SHUFFLE_OPENSEARCH_URL=https://shuffle-opensearch:9200
SHUFFLE_OPENSEARCH_SKIPSSL_VERIFY=true
SHUFFLE_OPENSEARCH_USERNAME=admin
SHUFFLE_ELASTIC=true
SHUFFLE_APP_HOTLOAD_FOLDER=/shuffle-apps
SHUFFLE_APP_HOTLOAD_LOCATION=/opt/soc-lab/shuffle-apps
SHUFFLE_FILE_LOCATION=/opt/soc-lab/shuffle-files
DB_LOCATION=/opt/soc-lab/shuffle-database
BACKEND_HOSTNAME=shuffle-backend
BACKEND_PORT=5001
FRONTEND_PORT=3001
FRONTEND_PORT_HTTPS=3443
BASE_URL=http://shuffle-backend:5001
OUTER_HOSTNAME=shuffle-backend
SSO_REDIRECT_URL=http://10.77.30.10:3001
AUTH_FOR_ORBORUS=
DOCKER_API_VERSION=1.44
SHUFFLE_WORKER_IMAGE=ghcr.io/shuffle/shuffle-worker:2.2.1
SHUFFLE_STATS_DISABLED=true
SHUFFLE_LOGS_DISABLED=true
SHUFFLE_CHAT_DISABLED=true
SHUFFLE_PASS_WORKER_PROXY=FALSE
SHUFFLE_PASS_APP_PROXY=FALSE
SHUFFLE_ORBORUS_EXECUTION_CONCURRENCY=2
SHUFFLE_APP_REPLICAS=1
SHUFFLE_CONTAINER_AUTO_CLEANUP=true
SHUFFLE_PROTECTED_CLEANUP_DISABLED=true
SHUFFLE_SKIPSSL_VERIFY=true
LIQUID_SANITIZE_INPUT=true
TZ=America/Chicago
EOF
  chown root:docker "${secrets}"
  chmod 0640 "${secrets}"
fi

install -o ubuntu -g ubuntu -m 0640 "${override_source}" "${override_target}"
runuser -u ubuntu -- docker compose --env-file "${secrets}" \
  -f "${root}/docker-compose.yml" -f "${override_target}" config --quiet
runuser -u ubuntu -- docker compose --env-file "${secrets}" \
  -f "${root}/docker-compose.yml" -f "${override_target}" pull
docker pull ghcr.io/shuffle/shuffle-worker:2.2.1

printf 'shuffle_memory_available_gib=%s\n' "$((memory_kib / 1024 / 1024))"
printf 'shuffle_disk_free_gib=%s\n' "$((free_kib / 1024 / 1024))"
