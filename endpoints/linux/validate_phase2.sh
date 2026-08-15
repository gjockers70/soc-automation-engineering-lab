#!/usr/bin/env bash
set -euo pipefail

test "$(systemctl is-active auditd)" = "active"
test "$(systemctl is-enabled auditd)" = "enabled"
ip -4 address show dev soc-telemetry | grep -q '10.77.30.20/24'
if ip -4 route show default | grep -q .; then
  echo "unexpected default route" >&2
  exit 1
fi

auditctl -l | grep -q -- '-k identity_change'
auditctl -l | grep -q -- '-k privilege_change'
auditctl -l | grep -q -- '-k soc_test_file'
auditctl -l | grep -Eq -- '(-k user_exec|-F key=user_exec)'

validation_file="/tmp/soc-lab-test/phase2-validation"
printf 'safe synthetic file event\n' >"${validation_file}"
logger --tag soc-phase2 "safe synthetic endpoint validation event"
sleep 2
ausearch -k soc_test_file -ts recent --format raw | grep -q '/tmp/soc-lab-test/phase2-validation'

test -r /var/log/auth.log
test -r /var/log/audit/audit.log
test -r /var/lib/soc-lab/phase2.conf

echo "linux_phase2_validation=pass"
echo "telemetry_address=10.77.30.20/24"
echo "default_route=absent"
echo "audit_event=soc_test_file"
