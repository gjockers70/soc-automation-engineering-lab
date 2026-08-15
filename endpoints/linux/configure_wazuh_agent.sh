#!/usr/bin/env bash
set -euo pipefail

config="/var/ossec/etc/ossec.conf"
password_file="/var/ossec/etc/authd.pass"

test -s "${password_file}"
chown root:wazuh "${password_file}"
chmod 0640 "${password_file}"

python3 - <<'PY'
from pathlib import Path

path = Path("/var/ossec/etc/ossec.conf")
text = path.read_text(encoding="utf-8")
blocks = []
if "/var/log/audit/audit.log" not in text:
    blocks.append("""
  <localfile>
    <log_format>audit</log_format>
    <location>/var/log/audit/audit.log</location>
  </localfile>
""")
if "<disabled>yes</disabled>" not in text:
    blocks.append("""
  <active-response>
    <disabled>yes</disabled>
  </active-response>
""")
if blocks:
    text = text.replace("</ossec_config>", "".join(blocks) + "</ossec_config>", 1)
path.write_text(text, encoding="utf-8")
PY

/var/ossec/bin/agent-auth -m 10.77.30.10 -A ubuntu-web-01
rm -f "${password_file}"
systemctl enable --now wazuh-agent.service
/var/ossec/bin/wazuh-control status
printf '%s\n' 'linux_agent_configuration=pass'
