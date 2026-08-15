# Observability deployment

This directory deploys Prometheus 3.13.2 and Grafana 13.1.3 using digest-pinned images.

prepare_observability.sh copies non-secret provisioning files to /opt/soc-lab/observability, generates or reuses a protected Grafana credential in /opt/soc-lab/secrets/observability.env, validates Compose, and pulls only missing images. Once images are cached, preparation works without a default route.

start_observability.sh starts the stack and waits for health. validate_observability.sh performs the complete Phase 13 live check. The deployment uses read-only root filesystems, dropped capabilities, no-new-privileges, bounded resources, persistent data volumes, and seven-day Prometheus retention.

Prometheus is loopback-only. Grafana is telemetry-only and should be reached through an SSH tunnel. No external data source, notification destination, analytics service, or paid API is configured.
