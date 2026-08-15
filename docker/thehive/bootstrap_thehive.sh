#!/usr/bin/env bash
set -euo pipefail

commit="c1671863c7a974a195177ab6bc32fb84f8a80834"
root="/opt/soc-lab/thehive-docker"

if [[ ${EUID} -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi

install -d -o ubuntu -g ubuntu -m 0750 /opt/soc-lab
if [[ ! -d "${root}/.git" ]]; then
  runuser -u ubuntu -- git clone https://github.com/StrangeBeeCorp/docker.git "${root}"
fi
runuser -u ubuntu -- git -C "${root}" fetch --depth 1 origin "${commit}"
runuser -u ubuntu -- git -C "${root}" checkout --detach "${commit}"
test "$(runuser -u ubuntu -- git -C "${root}" rev-parse HEAD)" = "${commit}"
printf 'thehive_docker_commit=%s\n' "${commit}"
