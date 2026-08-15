from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from soc_integration.app import create_app
from soc_integration.approvals import ApprovalConflict, ApprovalStore
from soc_integration.audit import AuditWriter
from soc_integration.enrichment import Indicator
from soc_integration.health import integration_health
from soc_integration.idempotency import IdempotencyConflict, IdempotencyStore
from soc_integration.incidents import IncidentStore
from soc_integration.integrations.base import IntegrationError
from soc_integration.models import ApprovalDecision, ApprovalProposal, WazuhAlert
from soc_integration.pipeline import AlertPipeline


def alert(payload: dict) -> WazuhAlert:
    return WazuhAlert.model_validate(payload)


class EmptyMisp:
    async def search(self, value: str, indicator_types: list[str]) -> dict:
        return {"response": {"Attribute": []}}

    async def close(self) -> None:
        return None


class RecoveringMisp:
    def __init__(self) -> None:
        self.available = False

    async def search(self, value: str, indicator_types: list[str]) -> dict:
        if not self.available:
            raise IntegrationError("misp", "unavailable")
        return {"response": {"Attribute": []}}

    async def close(self) -> None:
        return None


class CasePlatform:
    def __init__(self, existing: dict | None = None, missing_identifier: bool = False) -> None:
        self.existing = existing
        self.missing_identifier = missing_identifier
        self.created = 0
        self.observables: list[dict] = []

    async def find_case_by_tag(self, tag: str) -> dict | None:
        return self.existing

    async def create_case(self, payload: dict) -> dict:
        self.created += 1
        return {} if self.missing_identifier else {"_id": f"case-{self.created}"}

    async def add_observable(self, case_id: str, payload: dict) -> dict:
        self.observables.append(payload)
        return payload

    async def close(self) -> None:
        return None


def test_delivery_store_conflict_release_and_retry(tmp_path: Path) -> None:
    store = IdempotencyStore(tmp_path / "delivery.sqlite3")
    assert store.record("key-14", b"payload-a", "alert-a") is True
    assert store.record("key-14", b"payload-a", "alert-a") is False
    with pytest.raises(IdempotencyConflict):
        store.record("key-14", b"payload-b", "alert-b")
    store.release("key-14")
    assert store.record("key-14", b"payload-b", "alert-b") is True


def test_incident_reservation_persists_completed_case_and_releases_pending(
    tmp_path: Path,
) -> None:
    store = IncidentStore(tmp_path / "incidents.sqlite3")
    assert store.reserve("fingerprint-14") == (True, None)
    assert store.reserve("fingerprint-14") == (False, None)
    store.release("fingerprint-14")
    assert store.reserve("fingerprint-14") == (True, None)
    store.complete("fingerprint-14", "case-14")
    store.release("fingerprint-14")
    assert store.reserve("fingerprint-14") == (False, "case-14")


def test_incident_fingerprint_changes_by_hour_rule_and_endpoint(
    synthetic_alert_payload: dict,
) -> None:
    base = alert(synthetic_alert_payload)
    indicators = [Indicator(value="198.51.100.44", type="ip")]
    original = IncidentStore.fingerprint(base, indicators)
    later = alert({**synthetic_alert_payload, "timestamp": "2026-08-14T13:00:00-05:00"})
    other_rule = alert(
        {
            **synthetic_alert_payload,
            "rule": {**synthetic_alert_payload["rule"], "id": "140002"},
        }
    )
    other_agent = alert(
        {
            **synthetic_alert_payload,
            "agent": {**synthetic_alert_payload["agent"], "id": "002"},
        }
    )
    assert len({original, IncidentStore.fingerprint(later, indicators),
                IncidentStore.fingerprint(other_rule, indicators),
                IncidentStore.fingerprint(other_agent, indicators)}) == 4


def test_pipeline_reuses_existing_case_without_creating_another(
    tmp_path: Path, synthetic_alert_payload: dict
) -> None:
    platform = CasePlatform(existing={"_id": "existing-14"})
    pipeline = AlertPipeline(
        EmptyMisp(),
        platform,
        IncidentStore(tmp_path / "state.sqlite3"),
        AuditWriter(tmp_path / "audit.jsonl"),
    )
    result = asyncio.run(pipeline.process(alert(synthetic_alert_payload)))
    assert (result.incident_id, result.incident_disposition) == ("existing-14", "reused")
    assert platform.created == 0


def test_pipeline_releases_reservation_when_case_identifier_is_missing(
    tmp_path: Path, synthetic_alert_payload: dict
) -> None:
    store = IncidentStore(tmp_path / "state.sqlite3")
    pipeline = AlertPipeline(
        EmptyMisp(),
        CasePlatform(missing_identifier=True),
        store,
        AuditWriter(tmp_path / "audit.jsonl"),
    )
    parsed = alert(synthetic_alert_payload)
    with pytest.raises(RuntimeError, match="no case identifier"):
        asyncio.run(pipeline.process(parsed))
    fingerprint = store.fingerprint(parsed, [
        Indicator(value="phase14.test", type="domain"),
        Indicator(value="a" * 64, type="hash"),
        Indicator(value="198.51.100.44", type="ip"),
        Indicator(value="https://phase14.test/download", type="url"),
    ])
    assert store.reserve(fingerprint) == (True, None)


def test_gateway_releases_delivery_after_dependency_recovery(
    settings_factory, synthetic_alert_payload: dict
) -> None:
    misp = RecoveringMisp()
    platform = CasePlatform()
    clients = {"wazuh": None, "shuffle": None, "misp": misp, "thehive": platform}
    app = create_app(
        settings_factory(worker_poll_seconds=0.05, worker_retry_backoff_seconds=0.1),
        clients_override=clients,
    )
    headers = {
        "X-SOC-LAB-TOKEN": "w" * 32,
        "Idempotency-Key": "phase14-recovery-key",
    }
    with TestClient(app) as client:
        accepted = client.post("/v1/webhooks/wazuh", json=synthetic_alert_payload, headers=headers)
        for _ in range(50):
            pending = client.get(
                "/v1/deliveries/phase14-recovery-key",
                headers={"X-SOC-LAB-TOKEN": "w" * 32},
            ).json()
            if pending["status"] == "retrying":
                break
            time.sleep(0.01)
        misp.available = True
        for _ in range(100):
            recovered = client.get(
                "/v1/deliveries/phase14-recovery-key",
                headers={"X-SOC-LAB-TOKEN": "w" * 32},
            )
            if recovered.json()["status"] == "completed":
                break
            time.sleep(0.01)
    assert accepted.status_code == 202
    assert accepted.json()["processing_status"] == "queued"
    assert pending["status"] == "retrying"
    assert recovered.status_code == 200
    assert recovered.json()["status"] == "completed"
    assert recovered.json()["incident_disposition"] == "created"


class HealthyClient:
    async def health(self) -> None:
        return None


class UnhealthyClient:
    async def health(self) -> None:
        raise IntegrationError("synthetic", "timeout")


def test_health_aggregation_distinguishes_all_dependency_states() -> None:
    result = asyncio.run(
        integration_health(
            {"healthy": HealthyClient(), "unhealthy": UnhealthyClient(), "missing": None}
        )
    )
    assert result["healthy"].status == "healthy"
    assert result["unhealthy"].model_dump(exclude={"latency_ms"}) == {
        "status": "unhealthy",
        "detail": "timeout",
    }
    assert result["missing"].status == "not_configured"


def test_audit_writer_keeps_concurrent_records_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    writer = AuditWriter(path)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda number: writer.write("phase14.test", sequence=number), range(40)))
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 40
    assert {record["sequence"] for record in records} == set(range(40))
    assert all(record["timestamp"].endswith("Z") for record in records)


def test_tampered_approval_record_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "approval.sqlite3"
    store = ApprovalStore(path)
    proposal = ApprovalProposal(
        incident_id="case-14",
        action="disable_synthetic_account",
        target="soc-response-test",
        reason="Synthetic suspicious account activity for validation.",
        evidence=["synthetic alert phase14"],
        confidence=0.9,
    )
    approval_id = store.create(proposal).approval_id
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE approvals SET target = 'outside-allowlist' WHERE approval_id = ?",
            (approval_id,),
        )
    decision = ApprovalDecision(
        decision="approve",
        analyst="analyst.phase14",
        note="Testing fail-closed stored-record validation.",
    )
    with pytest.raises(ApprovalConflict, match="outside the response allowlist"):
        store.decide(approval_id, decision)
    assert store.identity_state("soc-response-test") == "enabled"
