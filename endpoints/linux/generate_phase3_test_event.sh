#!/usr/bin/env bash
set -euo pipefail

for attempt in 1 2 3 4 5 6; do
  logger --priority authpriv.warning --tag sshd \
    "Failed password for invalid user soc_phase3_test from 198.51.100.23 port $((4200 + attempt)) ssh2"
done

printf '%s\n' 'linux_synthetic_auth_events=6'
