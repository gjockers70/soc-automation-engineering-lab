# Phase 13 implementation

## Objective

Measure whether the SOC automation pipeline is receiving, processing, enriching, deduplicating, and handing off alerts reliably without exposing alert content or credentials.

## Architecture

The gateway owns application counters, gauges, and timing summaries and publishes Prometheus text at /metrics. A read-only collector summarizes the existing SOC-LAB PB Shuffle executions. Prometheus scrapes the gateway every 15 seconds, retains seven days locally, and evaluates five health rules. Grafana reads only Prometheus and provisions the dashboard from version-controlled JSON.

## Deployment

Prometheus and Grafana run beside the existing services on soc-mgr-01. Images are version- and digest-pinned. Prometheus binds only to loopback; Grafana binds only to the isolated telemetry address. Both containers use read-only root filesystems, temporary writable paths, dropped capabilities, resource limits, restart policies, and health checks.

The generated Grafana credential remains outside Git with mode 0640. Provisioning files contain no secrets and are world-readable so the images' non-root users can read their bind mounts.

## Operational behavior

Metric names and label sets are fixed in code. Unbounded values such as alert identifiers, usernames, IOC values, endpoints, and case IDs never become labels. Dependency gauges update during readiness checks. The Shuffle collector fails closed by setting its collection-health gauge to zero while leaving the gateway metrics endpoint available.

Prometheus rules intentionally remain local and do not page an analyst. Notification routing, escalation ownership, backup, and maintenance are Phase 16 concerns.

## Safety

The phase is read-only with respect to endpoints and response actions. It does not stop services, change accounts, block addresses, quarantine hosts, export telemetry, or add a default route. The existing synthetic response remains unchanged and approval-gated.
