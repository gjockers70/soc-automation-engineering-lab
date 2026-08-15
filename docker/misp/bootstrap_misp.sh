#!/usr/bin/env bash
set -euo pipefail

commit="223b675c4480730832f928e113b6f2e5260b450d"
root="/opt/soc-lab/misp-docker"

if [[ ! -d "${root}/.git" ]]; then
  git clone https://github.com/MISP/misp-docker.git "${root}"
fi
git -C "${root}" fetch --depth 1 origin "${commit}"
git -C "${root}" checkout --detach "${commit}"
test "$(git -C "${root}" rev-parse HEAD)" = "${commit}"
printf 'misp_docker_commit=%s\n' "${commit}"
