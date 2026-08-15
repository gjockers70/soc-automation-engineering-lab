#!/usr/bin/env bash
set -euo pipefail

echo "[identity]"
hostnamectl --static
. /etc/os-release
printf '%s %s\n' "$NAME" "$VERSION_ID"

echo "[cloud-init]"
cloud-init status --long

echo "[network]"
ip -br address
ip route
if ip route | grep -q '^default '; then
  echo "unexpected default route" >&2
  exit 1
fi
ip route get 1.1.1.1 >/dev/null 2>&1 && {
  echo "unexpected external route" >&2
  exit 1
}

echo "[docker]"
systemctl is-enabled docker
systemctl is-active docker
docker --version
docker compose version
docker info --format 'server={{.ServerVersion}} driver={{.Driver}} containers={{.Containers}}'
test "$(stat -c '%U:%G:%a' /etc/docker/daemon.json)" = "root:root:644"

echo "[filesystem]"
df -hT /
test -d /opt/soc-lab
test "$(stat -c '%U:%G' /opt/soc-lab)" = "ubuntu:ubuntu"

echo "[result]"
echo "phase1-guest-validation=pass"
