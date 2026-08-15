#!/usr/bin/env bash
set -euo pipefail

for attempt in 1 2 3 4; do
  logger --priority authpriv.warning --tag sshd \
    "Failed password for invalid user soc_phase4_below_threshold from 198.51.100.45 port $((4400 + attempt)) ssh2"
done

printf '%s\n' 'phase4_linux_negative_events=4'
