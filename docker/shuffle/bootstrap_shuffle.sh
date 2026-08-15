#!/usr/bin/env bash
set -euo pipefail

shuffle_commit="a106f27312bbb81791a33dfee585a6b8d0ad3289"
apps_commit="ab2f5f54989e3c94b68e4c4e5ae856813fcd7bd8"
shuffle_root="/opt/soc-lab/shuffle"
apps_root="/opt/soc-lab/shuffle-python-apps"

if [[ ${EUID} -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi

install -d -o ubuntu -g ubuntu -m 0750 /opt/soc-lab
if [[ ! -d "${shuffle_root}/.git" ]]; then
  runuser -u ubuntu -- git clone https://github.com/Shuffle/Shuffle.git "${shuffle_root}"
fi
runuser -u ubuntu -- git -C "${shuffle_root}" fetch --depth 1 origin "${shuffle_commit}"
runuser -u ubuntu -- git -C "${shuffle_root}" checkout --detach "${shuffle_commit}"

if [[ ! -d "${apps_root}/.git" ]]; then
  runuser -u ubuntu -- git clone https://github.com/Shuffle/python-apps.git "${apps_root}"
fi
runuser -u ubuntu -- git -C "${apps_root}" fetch --depth 1 origin "${apps_commit}"
runuser -u ubuntu -- git -C "${apps_root}" checkout --detach "${apps_commit}"

test "$(runuser -u ubuntu -- git -C "${shuffle_root}" rev-parse HEAD)" = "${shuffle_commit}"
test "$(runuser -u ubuntu -- git -C "${apps_root}" rev-parse HEAD)" = "${apps_commit}"
printf 'shuffle_commit=%s\nshuffle_apps_commit=%s\n' "${shuffle_commit}" "${apps_commit}"
