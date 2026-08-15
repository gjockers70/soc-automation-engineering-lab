#!/usr/bin/env bash
set -euo pipefail

interface="${1:-enp8s0}"
ip route del default via 192.168.123.1 dev "${interface}" 2>/dev/null || true
resolvectl revert "${interface}" 2>/dev/null || true
ip address flush dev "${interface}" scope global
