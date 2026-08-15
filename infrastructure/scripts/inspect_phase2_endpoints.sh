#!/usr/bin/env bash
set -euo pipefail

for domain in ubuntu-web-01 win11-01; do
  echo "[domain:${domain}]"
  virsh -c qemu:///system dominfo "${domain}" | grep -E '^(Name|State|CPU.s|Max memory|Autostart):'
  virsh -c qemu:///system domiflist "${domain}" --inactive
  virsh -c qemu:///system domblklist "${domain}" --inactive --details
done

virsh -c qemu:///system net-info pentest-isolated
virsh -c qemu:///system net-info soc-telemetry
