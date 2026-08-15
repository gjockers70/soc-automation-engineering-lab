#!/usr/bin/env bash
set -euo pipefail

binary=/usr/local/sbin/velociraptor
api=/etc/velociraptor/api.config.yaml
output_root=/opt/soc-lab/velociraptor/collections
run_id="phase11-$(date -u +%Y%m%dT%H%M%SZ)"
run_root="${output_root}/${run_id}"
install -d -o velociraptor -g velociraptor -m 0750 "${run_root}"

clients="$(${binary} --api_config "${api}" --nobanner query --format=jsonl \
  'SELECT client_id, os_info.hostname AS hostname, os_info.system AS system, timestamp(epoch=last_seen_at/1000) AS last_seen FROM clients()')"
linux_id="$(jq -r 'select((.hostname | ascii_downcase) == "ubuntu-web-01") | .client_id' <<<"${clients}" | head -1)"
windows_id="$(jq -r 'select((.hostname | ascii_downcase) == "win11-01") | .client_id' <<<"${clients}" | head -1)"
[[ -n "${linux_id}" && -n "${windows_id}" ]]

collect() {
  local client_id="$1" artifact="$2" output="$3"
  shift 3
  "${binary}" --api_config "${api}" --nobanner artifacts collect "${artifact}" \
    --client_id "${client_id}" --timeout 300 --progress_timeout 120 \
    --cpu_limit 20 --output "${run_root}/${output}.zip" --format json "$@" >/dev/null
}

collect "${linux_id}" Linux.Sys.Pslist linux-processes
collect "${linux_id}" Linux.Network.Netstat linux-network
collect "${linux_id}" Linux.Sys.Users linux-users
collect "${linux_id}" Linux.Sys.LastUserLogin linux-logins
collect "${linux_id}" Linux.Sys.Services linux-startup-services
collect "${linux_id}" Linux.Search.FileFinder linux-file-metadata \
  --args SearchFilesGlob=/var/lib/soc-lab/phase2.conf --args Upload_File=N --args Calculate_Hash=Y

start_date="$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%SZ)"
collect "${windows_id}" Generic.System.Pstree windows-processes
collect "${windows_id}" Windows.Network.Netstat windows-network
collect "${windows_id}" Windows.Sys.Users windows-users
collect "${windows_id}" Windows.Sys.StartupItems windows-startup-items
collect "${windows_id}" Windows.EventLogs.Evtx windows-selected-events \
  --args 'ChannelRegex=^(Security|Microsoft-Windows-PowerShell/Operational)$' \
  --args 'IDRegex=^(4624|4625|4688|4104)$' --args "StartDate=${start_date}"
collect "${windows_id}" Windows.Search.FileFinder windows-file-metadata \
  --args 'Glob=C:/SOC-Lab/Phase11/triage-marker.txt' --args Upload_File=N --args Calculate_Hash=Y

summary="${run_root}/summary.json"
jq -n --arg run_id "${run_id}" --arg linux_id "${linux_id}" --arg windows_id "${windows_id}" \
  --arg generated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson archives "$(find "${run_root}" -maxdepth 1 -name '*.zip' -printf '%f\n' | sort | jq -Rsc 'split("\n")[:-1]')" \
  '{run_id:$run_id,generated_at:$generated_at,clients:{linux:$linux_id,windows:$windows_id},archives:$archives,collection_count:($archives|length),raw_results_committed:false}' \
  > "${summary}"
chown -R velociraptor:velociraptor "${run_root}"
chmod -R o-rwx "${run_root}"
cat "${summary}"
