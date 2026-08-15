#!/usr/bin/env bash
set -euo pipefail

install -d -m 0750 -o root -g root /var/lib/soc-lab
install -d -m 1777 -o root -g root /tmp/soc-lab-test

cat >/etc/audit/rules.d/50-soc-lab.rules <<'EOF'
## SOC lab audit rules: focused identity, privilege, and user execution telemetry.
-w /etc/passwd -p wa -k identity_change
-w /etc/group -p wa -k identity_change
-w /etc/sudoers -p wa -k privilege_change
-w /etc/sudoers.d -p wa -k privilege_change
-w /tmp/soc-lab-test -p wa -k soc_test_file
-a always,exit -F arch=b64 -S execve -F auid>=1000 -F auid!=unset -k user_exec
EOF

augenrules --load
systemctl enable --now auditd

cat >/var/lib/soc-lab/phase2.conf <<'EOF'
endpoint_role=linux
telemetry_address=10.77.30.20/24
log_sources=auth,journal,auditd
EOF

logger --tag soc-phase2 "Linux endpoint telemetry configuration validated"

echo "auditd_active=$(systemctl is-active auditd)"
echo "auditd_enabled=$(systemctl is-enabled auditd)"
auditctl -l
test -r /var/log/auth.log && echo "auth_log=present" || echo "auth_log=journal_only"
