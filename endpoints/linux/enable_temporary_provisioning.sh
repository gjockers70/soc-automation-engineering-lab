#!/usr/bin/env bash
set -euo pipefail

interface="${1:-enp8s0}"
ip link set "${interface}" up
ip address replace 192.168.123.120/24 dev "${interface}"
ip route replace default via 192.168.123.1 dev "${interface}"
resolvectl dns "${interface}" 192.168.123.1
resolvectl domain "${interface}" '~.'
