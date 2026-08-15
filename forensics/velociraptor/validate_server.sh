#!/usr/bin/env bash
set -euo pipefail

run_root="${1:-/opt/soc-lab/velociraptor/collections/phase11-20260814T002030Z}"
systemctl is-active --quiet velociraptor-server
[[ -f "${run_root}/summary.json" ]]
jq -e '.collection_count == 12 and .raw_results_committed == false' "${run_root}/summary.json" >/dev/null
mapfile -t archives < <(find "${run_root}" -maxdepth 1 -name '*.zip' -type f | sort)
[[ ${#archives[@]} -eq 12 ]]
for archive in "${archives[@]}"; do
  [[ -s "${archive}" ]]
  python3 -m zipfile -t "${archive}" >/dev/null
done
[[ "$(stat -c '%a' /opt/soc-lab/secrets/velociraptor.env)" == 640 ]]
ss -lnt | grep -q '10.77.30.10:8000'
ss -lnt | grep -q '10.77.30.10:8889'
ss -lnt | grep -q '127.0.0.1:8001'
! ss -lnt | grep -q '0.0.0.0:8000'
! ss -lnt | grep -q '0.0.0.0:8889'
! ip route show default | grep -q .

clients="$(/usr/local/sbin/velociraptor --api_config /etc/velociraptor/api.config.yaml --nobanner query --format=jsonl 'SELECT client_id, os_info.hostname AS hostname, os_info.system AS system FROM clients()')"
jq -s -e 'length == 2 and ([.[].system] | sort == ["linux","windows"])' <<<"${clients}" >/dev/null

jq -n --argjson summary "$(cat "${run_root}/summary.json")" \
  --argjson sizes "$(printf '%s\n' "${archives[@]}" | xargs -r stat -c '%n %s' | jq -Rsc 'split("\n")[:-1] | map(split(" ") | {archive:(.[0]|split("/")|last),bytes:(.[1]|tonumber)})')" \
  --argjson clients "$(jq -s . <<<"${clients}")" \
  '{summary:$summary,archive_sizes:$sizes,enrolled_clients:($clients|map({client_id,hostname,system})),server_health:"active",listeners:{frontend:"10.77.30.10:8000",gui:"10.77.30.10:8889",api:"127.0.0.1:8001"},secret_mode:"0640",default_route:"absent",archive_integrity:"passed"}'
