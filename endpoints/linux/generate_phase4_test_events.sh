#!/usr/bin/env bash
set -euo pipefail

for attempt in 1 2 3 4 5 6; do
  logger --priority authpriv.warning --tag sshd \
    "Failed password for invalid user soc_phase4_test from 198.51.100.44 port $((4300 + attempt)) ssh2"
done

printf '%s\n' 'phase4_linux_test_events=6'
