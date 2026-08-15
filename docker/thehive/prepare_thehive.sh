#!/usr/bin/env bash
set -euo pipefail

root="/opt/soc-lab/thehive-docker/prod1-thehive"
override_source="/root/thehive-compose.override.yml"
override_target="${root}/compose.soc-lab.yml"

if [[ ${EUID} -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi
test -d "${root}"
test -f "${override_source}"

memory_kib=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
free_kib=$(df --output=avail / | tail -1 | tr -d ' ')
(( memory_kib >= 20 * 1024 * 1024 )) || { echo "TheHive profile requires at least 20 GiB guest memory" >&2; exit 1; }
(( free_kib >= 40 * 1024 * 1024 )) || { echo "TheHive profile requires at least 40 GiB free disk" >&2; exit 1; }

# Match the upstream initializer's documented permission contract without an
# interactive repair prompt.
find "${root}"/cassandra "${root}"/certificates "${root}"/elasticsearch \
  "${root}"/nginx "${root}"/scripts "${root}"/thehive -type d -exec chmod 0750 {} +
find "${root}"/docker-compose.yml "${root}"/dot.env.template \
  "${root}"/cassandra "${root}"/certificates "${root}"/elasticsearch \
  "${root}"/nginx "${root}"/thehive -type f -exec chmod 0644 {} +
find "${root}"/scripts -type f -exec chmod 0755 {} +

if [[ ! -f "${root}/.env" ]]; then
  runuser -u ubuntu -- bash -c "cd '${root}' && printf '%s\\n' 'thehive.soc.test' | bash ./scripts/init.sh"
fi

install -o ubuntu -g ubuntu -m 0640 "${override_source}" "${override_target}"
chmod 0640 "${root}/.env" "${root}/thehive/config/secret.conf" "${root}/thehive/config/index.conf"

runuser -u ubuntu -- docker compose --env-file "${root}/.env" \
  -f "${root}/docker-compose.yml" -f "${override_target}" config --quiet
runuser -u ubuntu -- docker compose --env-file "${root}/.env" \
  -f "${root}/docker-compose.yml" -f "${override_target}" pull

printf 'thehive_source=%s\n' "$(runuser -u ubuntu -- git -C /opt/soc-lab/thehive-docker rev-parse HEAD)"
printf 'thehive_memory_gib=%s\n' "$((memory_kib / 1024 / 1024))"
printf 'thehive_disk_free_gib=%s\n' "$((free_kib / 1024 / 1024))"
