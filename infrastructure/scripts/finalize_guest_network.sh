#!/usr/bin/env bash
set -euo pipefail

chown ubuntu:ubuntu /home/ubuntu/.ssh/authorized_keys
chmod 600 /home/ubuntu/.ssh/authorized_keys
chmod 600 /etc/netplan/60-soc-telemetry.yaml
netplan generate
netplan apply
sleep 2
ip -br address
ip route
