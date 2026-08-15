import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBSERVABILITY = ROOT / "observability"


def test_images_are_pinned_and_listeners_are_restricted():
    compose = (OBSERVABILITY / "compose.yml").read_text(encoding="utf-8")
    assert "prom/prometheus:v3.13.2@sha256:" in compose
    assert "grafana/grafana:13.1.3@sha256:" in compose
    assert ":latest" not in compose
    assert '"127.0.0.1:9090:9090"' in compose
    assert '"10.77.30.10:3000:3000"' in compose
    assert "read_only: true" in compose
    assert compose.count("no-new-privileges:true") == 2


def test_non_secret_provisioning_files_are_container_readable():
    prepare = (OBSERVABILITY / "prepare_observability.sh").read_text(encoding="utf-8")
    assert "-type f -exec chmod 0644" in prepare
    assert 'chmod 0640 "${env_file}"' in prepare


def test_prometheus_scrape_and_alert_rules_cover_platform_health():
    config = (OBSERVABILITY / "prometheus" / "prometheus.yml").read_text(encoding="utf-8")
    rules = (OBSERVABILITY / "prometheus" / "rules.yml").read_text(encoding="utf-8")
    assert "10.77.30.10:8010" in config
    assert "metrics_path: /metrics" in config
    for alert in (
        "SOCIntegrationGatewayDown",
        "SOCDependencyUnhealthy",
        "SOCPipelineFailures",
        "SOCPlaybookFailureRatioHigh",
        "SOCEnrichmentLatencyHigh",
        "SOCDeliveryQueueStale",
        "SOCDeliveryTerminalFailures",
    ):
        assert f"alert: {alert}" in rules


def test_dashboard_is_valid_and_queries_required_metrics():
    dashboard = json.loads(
        (OBSERVABILITY / "grafana" / "dashboards" / "soc-platform-overview.json").read_text(
            encoding="utf-8"
        )
    )
    expressions = " ".join(
        target["expr"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    )
    assert dashboard["uid"] == "soc-platform-overview"
    assert len(dashboard["panels"]) >= 10
    for metric in (
        "soc_alerts_received_total",
        "soc_alerts_processed_total",
        "soc_incidents_total",
        "soc_duplicate_suppression_total",
        "soc_dependency_healthy",
        "soc_playbook_executions",
        "soc_enrichment_duration_seconds",
        "soc_workflow_duration_seconds",
        "soc_api_failures_total",
        "soc_delivery_queue_items",
        "soc_delivery_oldest_pending_seconds",
    ):
        assert metric in expressions


def test_validation_preserves_isolation_and_checks_secrets():
    script = (OBSERVABILITY / "validate_observability.sh").read_text(encoding="utf-8")
    assert "stat -c '%a'" in script
    assert "0.0.0.0:9090" in script
    assert "0.0.0.0:3000" in script
    assert "! ip route show default" in script
    gateway_script = (ROOT / "docker" / "integration" / "validate_phase13.sh").read_text(
        encoding="utf-8"
    )
    assert "required_metrics=(" in gateway_script
    assert "for required in + " not in gateway_script
