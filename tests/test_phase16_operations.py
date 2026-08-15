"""Phase 16 operational-document and health-snapshot safety tests."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = ROOT / "operations"


def test_required_runbooks_exist() -> None:
    required = {
        "RUNBOOK.md",
        "ESCALATION.md",
        "SERVICE_DEPENDENCIES.md",
        "HEALTH_CHECKS.md",
        "FAILURE_RECOVERY.md",
        "BACKUP_RECOVERY.md",
        "CHANGE_MANAGEMENT.md",
        "MAINTENANCE.md",
        "SHIFT_HANDOFF.md",
    }
    assert (ROOT / "RUNBOOK.md").is_file()
    assert required - {"RUNBOOK.md"} <= {path.name for path in OPERATIONS.glob("*.md")}


def test_runbooks_cover_operational_requirements() -> None:
    corpus = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in sorted(OPERATIONS.glob("*.md"))
    )
    for concept in (
        "service dependencies",
        "failed-playbook",
        "backup",
        "restore",
        "change management",
        "maintenance",
        "escalation",
        "shift handoff",
        "idempotency",
        "default route",
    ):
        assert concept in corpus


def test_health_snapshot_is_read_only() -> None:
    script = (OPERATIONS / "health_snapshot.sh").read_text(encoding="utf-8")
    assert "set -euo pipefail" in script
    forbidden = (
        r"\bdocker\s+(?:restart|stop|rm|compose\s+down)\b",
        r"\bsystemctl\s+(?:restart|stop|disable)\b",
        r"\brm\s+-",
        r"\bshutdown\b",
        r"\breboot\b",
        r"\biptables\b",
    )
    for pattern in forbidden:
        assert re.search(pattern, script) is None


def test_health_snapshot_checks_safety_and_capacity() -> None:
    script = (OPERATIONS / "health_snapshot.sh").read_text(encoding="utf-8")
    for required in (
        "ip route show default",
        "MemAvailable",
        "df -P /",
        "velociraptor-server.service",
        "integration_gateway",
        "prometheus",
        "grafana",
    ):
        assert required in script


def test_runbook_does_not_claim_24x7_operation() -> None:
    root_runbook = (ROOT / "RUNBOOK.md").read_text(encoding="utf-8").lower()
    handoff = (OPERATIONS / "SHIFT_HANDOFF.md").read_text(encoding="utf-8").lower()
    assert "does not claim" in root_runbook
    assert "not staffed in shifts" in handoff
