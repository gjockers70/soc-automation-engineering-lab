#!/usr/bin/env bash
set -euo pipefail

secrets_dir="/opt/soc-lab/secrets"
env_file="${secrets_dir}/thehive.env"
bootstrap_env="/root/thehive-bootstrap.env"
base_url="http://127.0.0.1:9000"
organisation="SOC-LAB"
username="soc-automation@lab.test"
initial_password=""

if [[ ${EUID} -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi
command -v jq >/dev/null
install -d -o root -g docker -m 0750 "${secrets_dir}"

if [[ ! -f "${env_file}" ]]; then
  test -f "${bootstrap_env}" || { echo "create protected ${bootstrap_env} with THEHIVE_INITIAL_ADMIN_PASSWORD" >&2; exit 1; }
  # shellcheck disable=SC1090
  source "${bootstrap_env}"
  : "${THEHIVE_INITIAL_ADMIN_PASSWORD:?missing initial administrator password}"
  initial_password="${THEHIVE_INITIAL_ADMIN_PASSWORD}"
  admin_password=$(openssl rand -base64 36 | tr -d '\n')
  user_password=$(openssl rand -base64 36 | tr -d '\n')
  umask 0077
  cat >"${env_file}" <<EOF
THEHIVE_URL=${base_url}
THEHIVE_ORGANISATION=${organisation}
THEHIVE_USERNAME=${username}
THEHIVE_PASSWORD=${user_password}
THEHIVE_API_KEY=
THEHIVE_ADMIN_PASSWORD=${admin_password}
EOF
  chown root:docker "${env_file}"
  chmod 0640 "${env_file}"
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

code=000
for _ in $(seq 1 60); do
  if [[ -n "${initial_password}" ]]; then
    code=$(curl -ksS -o /dev/null -w '%{http_code}' -u "admin@thehive.local:${initial_password}" \
      "${base_url}/api/v1/user/current" || true)
    [[ "${code}" == 200 ]] && break
  fi
  code=$(curl -ksS -o /dev/null -w '%{http_code}' -u "admin@thehive.local:${THEHIVE_ADMIN_PASSWORD}" \
    "${base_url}/api/v1/user/current" || true)
  [[ "${code}" == 200 ]] && break
  sleep 5
done
[[ "${code}" == 200 ]] || { echo "TheHive API did not become ready" >&2; exit 1; }

if [[ -n "${initial_password}" ]] && curl -ksS -u "admin@thehive.local:${initial_password}" \
  "${base_url}/api/v1/user/current" | jq -e .login >/dev/null 2>&1; then
  admin_auth="admin@thehive.local:${initial_password}"
  using_initial_password=true
else
  admin_auth="admin@thehive.local:${THEHIVE_ADMIN_PASSWORD}"
  using_initial_password=false
fi

org_code=$(curl -ksS -o /tmp/thehive-org.json -w '%{http_code}' -u "${admin_auth}" \
  "${base_url}/api/organisation/${organisation}")
if [[ "${org_code}" == 404 ]]; then
  curl -ksS --fail-with-body -u "${admin_auth}" -H 'Content-Type: application/json' \
    -d "{\"name\":\"${organisation}\",\"description\":\"Isolated SOC engineering lab\"}" \
    "${base_url}/api/organisation" >/dev/null
elif [[ "${org_code}" != 200 ]]; then
  cat /tmp/thehive-org.json >&2
  exit 1
fi

user_code=$(curl -ksS -o /tmp/thehive-user.json -w '%{http_code}' -u "${admin_auth}" \
  "${base_url}/api/v1/user/${username}")
if [[ "${user_code}" == 404 ]]; then
  payload=$(jq -nc --arg login "${username}" --arg org "${organisation}" --arg pass "${THEHIVE_PASSWORD}" \
    '{login:$login,name:"SOC automation service",organisation:$org,profile:"analyst",password:$pass}')
  curl -ksS --fail-with-body -u "${admin_auth}" -H 'Content-Type: application/json' \
    -d "${payload}" "${base_url}/api/v1/user" >/dev/null
elif [[ "${user_code}" != 200 ]]; then
  cat /tmp/thehive-user.json >&2
  exit 1
fi
user_id=$(curl -ksS --fail-with-body -u "${admin_auth}" "${base_url}/api/v1/user/${username}" | jq -r '._id')
membership=$(jq -nc --arg org "${organisation}" '{organisations:[{organisation:$org,profile:"analyst"}]}')
curl -ksS --fail-with-body -X PUT -u "${admin_auth}" -H 'Content-Type: application/json' \
  -d "${membership}" "${base_url}/api/v1/user/${user_id}/organisations" >/dev/null


if [[ "${using_initial_password}" == true ]]; then
  payload=$(jq -nc --arg password "${THEHIVE_ADMIN_PASSWORD}" '{password:$password}')
  curl -ksS --fail-with-body -u "${admin_auth}" -H 'Content-Type: application/json' \
    -d "${payload}" "${base_url}/api/v1/user/admin@thehive.local/password/set" >/dev/null
fi

key=$(curl -ksS --fail-with-body -u "${username}:${THEHIVE_PASSWORD}" -X POST \
  -H "X-Organisation: ${organisation}" "${base_url}/api/v1/user/${username}/key/renew" || true)
if [[ -n "${key}" ]]; then
  sed -i "s|^THEHIVE_API_KEY=.*$|THEHIVE_API_KEY=${key}|" "${env_file}"
fi

printf 'thehive_organisation=%s\n' "${organisation}"
printf 'thehive_user=%s\n' "${username}"
printf 'default_admin_password_disabled=true\n'
