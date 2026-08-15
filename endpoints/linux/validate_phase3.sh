#!/usr/bin/env bash
set -euo pipefail

systemctl is-active --quiet wazuh-agent.service
grep -q '<address>10.77.30.10</address>' /var/ossec/etc/ossec.conf
grep -q '/var/log/audit/audit.log' /var/ossec/etc/ossec.conf
grep -q '<disabled>yes</disabled>' /var/ossec/etc/ossec.conf
test ! -e /var/ossec/etc/authd.pass
! ip route show default | grep -q .
printf '%s\n' 'linux_phase3_validation=pass'
