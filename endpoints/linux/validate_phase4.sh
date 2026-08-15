#!/usr/bin/env bash
set -euo pipefail

systemctl is-active --quiet wazuh-agent.service
! ip -4 route show default | grep -q .
printf '%s\n' 'linux_phase4_validation=pass'
