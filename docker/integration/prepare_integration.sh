#!/usr/bin/env bash
set -euo pipefail

repo_source="/root/phase13-files"
deploy_root="/opt/soc-lab/integration"
state_root="/opt/soc-lab/integration-state"
secrets_root="/opt/soc-lab/secrets"
env_file="${secrets_root}/integration.env"
shuffle_state="/opt/soc-lab/state/phase7-workflows.json"

if [[ ${EUID} -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi

for required in wazuh.env shuffle.env misp.env thehive.env; do
  test -f "${secrets_root}/${required}"
done
test -f "${repo_source}/docker/integration/compose.yml"
test -f "${shuffle_state}"
docker image inspect soc-integration-gateway:phase12 >/dev/null 2>&1 || { echo "Phase 12 gateway image is required for this offline incremental build" >&2; exit 1; }

install -d -o root -g docker -m 0750 "${deploy_root}" "${secrets_root}"
install -d -o 10001 -g 10001 -m 0750 "${state_root}"
rm -rf "${deploy_root}/src"
cp -a "${repo_source}/src" "${deploy_root}/"
rm -rf "${deploy_root}/operations"
install -d -o root -g docker -m 0750 "${deploy_root}/operations"
cp -a "${repo_source}/operations/failure-lab" "${deploy_root}/operations/"
install -o root -g docker -m 0640 "${repo_source}/requirements.txt" "${deploy_root}/requirements.txt"
install -d -o root -g docker -m 0750 "${deploy_root}/docker/integration"
install -o root -g docker -m 0640 "${repo_source}/docker/integration/Dockerfile" "${deploy_root}/docker/integration/Dockerfile"
install -o root -g docker -m 0640 "${repo_source}/docker/integration/compose.yml" "${deploy_root}/docker/integration/compose.yml"
install -o root -g docker -m 0640 "${repo_source}/docker/integration/Dockerfile.dockerignore" "${deploy_root}/docker/integration/Dockerfile.dockerignore"
install -o root -g docker -m 0750 "${repo_source}/docker/integration/start_integration.sh" "${deploy_root}/docker/integration/start_integration.sh"
install -o root -g docker -m 0750 "${repo_source}/docker/integration/validate_phase12.sh" "${deploy_root}/docker/integration/validate_phase12.sh"
install -o root -g docker -m 0750 "${repo_source}/docker/integration/validate_phase13.sh" "${deploy_root}/docker/integration/validate_phase13.sh"

set -a
# shellcheck disable=SC1091
source "${secrets_root}/wazuh.env"
wazuh_password="${WAZUH_API_PASSWORD}"
# shellcheck disable=SC1091
source "${secrets_root}/shuffle.env"
shuffle_key="${SHUFFLE_DEFAULT_APIKEY}"
shuffle_webhook_token="${SHUFFLE_WEBHOOK_TOKEN}"
# shellcheck disable=SC1091
source "${secrets_root}/misp.env"
misp_key="${ADMIN_KEY}"
# shellcheck disable=SC1091
source "${secrets_root}/thehive.env"
thehive_url="${THEHIVE_URL}"
thehive_org="${THEHIVE_ORGANISATION}"
thehive_user="${THEHIVE_USERNAME}"
thehive_password="${THEHIVE_PASSWORD}"
set +a

webhook_token="$(sed -n 's/^SOC_WEBHOOK_TOKEN=//p' "${env_file}" 2>/dev/null || true)"
approval_token="$(sed -n 's/^SOC_APPROVAL_TOKEN=//p' "${env_file}" 2>/dev/null | tr -d '\r' || true)"
if [[ -z "${webhook_token}" ]]; then
  webhook_token="$(openssl rand -hex 32)"
fi

if [[ -z "${approval_token}" ]]; then
  approval_token="$(openssl rand -hex 32)"
fi
webhook_url() {
  local key=$1
  local hook_id
  hook_id="$(jq -er --arg key "${key}" '.workflows[$key].webhook_id' "${shuffle_state}")"
  printf 'http://127.0.0.1:5001/api/v1/hooks/webhook_%s' "${hook_id}"
}
umask 0077
cat >"${env_file}" <<EOF
SOC_WEBHOOK_TOKEN=${webhook_token}
SOC_APPROVAL_TOKEN=${approval_token}
SOC_AUDIT_PATH=/var/lib/soc-integration/audit.jsonl
SOC_IDEMPOTENCY_DB=/var/lib/soc-integration/idempotency.sqlite3
SOC_REQUEST_TIMEOUT_SECONDS=5
SOC_RETRY_ATTEMPTS=3
SOC_RETRY_BACKOFF_SECONDS=0.25
WAZUH_URL=https://10.77.30.10:55000
WAZUH_USERNAME=wazuh-wui
WAZUH_PASSWORD=${wazuh_password}
SHUFFLE_URL=http://127.0.0.1:5001
SHUFFLE_API_KEY=${shuffle_key}
SHUFFLE_WEBHOOK_TOKEN=${shuffle_webhook_token}
SHUFFLE_SUSPICIOUS_LOGIN_WEBHOOK=$(webhook_url suspicious-login)
SHUFFLE_SUSPICIOUS_FILE_WEBHOOK=$(webhook_url suspicious-file)
SHUFFLE_SUSPICIOUS_DOMAIN_WEBHOOK=$(webhook_url suspicious-domain)
SHUFFLE_ACCOUNT_ACTIVITY_WEBHOOK=$(webhook_url account-activity)
SHUFFLE_SECURITY_ALERT_WEBHOOK=$(webhook_url security-alert)
MISP_URL=https://10.77.30.10:8443
MISP_API_KEY=${misp_key}
THEHIVE_URL=${thehive_url}
THEHIVE_ORGANISATION=${thehive_org}
THEHIVE_USERNAME=${thehive_user}
THEHIVE_PASSWORD=${thehive_password}
SOC_VERIFY_INTERNAL_TLS=false
SOC_WORKER_POLL_SECONDS=0.5
SOC_WORKER_MAX_ATTEMPTS=5
SOC_WORKER_RETRY_BACKOFF_SECONDS=2
EOF
chown root:docker "${env_file}"
chmod 0640 "${env_file}"

docker compose -f "${deploy_root}/docker/integration/compose.yml" build
printf 'integration_image=prepared\n'
