from __future__ import annotations

from pathlib import Path

import pytest

from soc_integration.config import Settings


@pytest.fixture
def synthetic_alert_payload() -> dict:
    return {
        "id": "phase14-001",
        "timestamp": "2026-08-14T12:00:00-05:00",
        "rule": {
            "id": "140001",
            "level": 8,
            "description": "Synthetic Phase 14 contract alert",
        },
        "agent": {"id": "001", "name": "ubuntu-web-01"},
        "data": {
            "srcip": "198.51.100.44",
            "domain": "phase14.test",
            "url": "https://phase14.test/download",
            "sha256": "a" * 64,
        },
        "synthetic": True,
    }


@pytest.fixture
def settings_factory(tmp_path: Path):
    def build(**overrides: object) -> Settings:
        values: dict[str, object] = {
            "webhook_token": "w" * 32,
            "approval_token": "a" * 32,
            "audit_path": tmp_path / "audit.jsonl",
            "idempotency_db": tmp_path / "state.sqlite3",
        }
        values.update(overrides)
        return Settings.model_validate(values)

    return build
