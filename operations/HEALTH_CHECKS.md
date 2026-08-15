# Health Checks

## Read-only snapshot

Install health_snapshot.sh at /opt/soc-lab/operations/health_snapshot.sh on soc-mgr-01, then run:

~~~bash
sudo /opt/soc-lab/operations/health_snapshot.sh
echo $?
~~~

Exit 0 means all bounded checks passed; exit 1 means at least one named check is degraded. The JSON contains no credentials or alert content. The script checks three HTTP endpoints, ten critical containers, Velociraptor, root-disk pressure, available memory, and the isolation route boundary.

## Thresholds

| Signal | Healthy | Warning/action |
|---|---|---|
| Root filesystem | under 85% used | Stop creating recovery copies and investigate growth |
| Available memory | at least 1024 MiB | Inspect consumers before starting services |
| Default route | absent | Any default route is a security-boundary failure |
| Critical container | running | Missing/exited is degraded; inspect project and logs |
| Velociraptor server | active | Inactive blocks triage; detection may continue |
| HTTP readiness | succeeds within 5 seconds | Inspect service state, then bounded logs |

Thresholds are lab limits, not universal production values. Override only through a documented change with SOC_DISK_WARN_PERCENT and SOC_MEMORY_WARN_MIB.

## Detailed checks

~~~bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
sudo /opt/soc-lab/observability/validate_observability.sh
sudo /opt/soc-lab/integration/docker/integration/validate_phase13.sh
systemctl status velociraptor-server.service --no-pager
df -h /
free -h
ip route show default
~~~

Use docker logs with a bounded time and line count only after identifying the component. Do not dump environment variables or secret files into committed evidence.

## Cadence

- Start and end of an attended session: health snapshot.
- Before and after a change: snapshot plus the component validator.
- Weekly: dashboard/rule review and capacity trend.
- Monthly: restore exercise and stale credential/configuration review.

Production also needs an external observer because an in-stack monitor cannot report its own total outage.
