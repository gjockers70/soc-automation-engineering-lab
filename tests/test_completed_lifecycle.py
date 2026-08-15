from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from soc_integration.app import create_app
from soc_integration.approvals import ApprovalStore
from soc_integration.audit import AuditWriter
from soc_integration.deliveries import DeliveryStore
from soc_integration.incidents import IncidentStore
from soc_integration.integrations.base import IntegrationError
from soc_integration.integrations.shuffle import ShuffleClient
from soc_integration.metrics import MetricsRegistry
from soc_integration.pipeline import AlertPipeline
from soc_integration.worker import DeliveryWorker, scenario_for

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "docker" / "wazuh" / "integrations" / "soc_gateway_adapter.py"
SPEC = importlib.util.spec_from_file_location("soc_gateway_adapter", ADAPTER_PATH)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)


def native_alert(rule_id: str = "100102") -> dict:
    return {
        "id": "wazuh-live-001",
        "timestamp": "2026-08-14T12:00:00-05:00",
        "rule": {
            "id": rule_id,
            "level": 9,
            "description": "SOC1003 synthetic account created",
            "groups": ["soc_lab", "windows", "identity"],
        },
        "agent": {"id": "002", "name": "win11-01"},
        "data": {"win": {"eventdata": {"targetUserName": "soc-response-test"}}},
    }


class EmptyMisp:
    async def search(self, value: str, indicator_types: list[str]) -> dict:
        return {"response": {"Attribute": []}}


class FakeHive:
    def __init__(self) -> None:
        self.cases: list[dict] = []
        self.comments: list[str] = []

    async def find_case_by_tag(self, tag: str) -> dict | None:
        return None

    async def create_case(self, payload: dict) -> dict:
        case = {**payload, "_id": "case-complete-1"}
        self.cases.append(case)
        return case

    async def add_observable(self, case_id: str, payload: dict) -> dict:
        return payload

    async def add_comment(self, case_id: str, message: str) -> dict:
        self.comments.append(message)
        return {"message": message}


class FakeShuffle:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    async def trigger(self, webhook: str, token: str, payload: dict) -> dict:
        self.calls.append((webhook, token, payload))
        return {"execution_id": "shuffle-execution-1"}


def test_wazuh_adapter_maps_only_allowlisted_synthetic_rules(tmp_path: Path) -> None:
    payload = ADAPTER.normalize_alert(native_alert())
    assert payload["synthetic"] is True
    assert payload["rule"]["id"] == "100102"
    assert ADAPTER.idempotency_key(payload) == ADAPTER.idempotency_key(payload)
    outside = native_alert("5710")
    with pytest.raises(ValueError, match="allowlist"):
        ADAPTER.normalize_alert(outside)

    config = ADAPTER.AdapterConfig("http://gateway.test", "x" * 32, tmp_path)
    with patch.object(ADAPTER, "send", side_effect=OSError("offline")):
        path = ADAPTER.spool(config, ADAPTER.idempotency_key(payload), payload)
    assert path.is_file()
    assert "x" * 32 not in path.read_text(encoding="utf-8")


def test_delivery_store_persists_retries_completion_and_handoff(tmp_path: Path) -> None:
    store = DeliveryStore(tmp_path / "state.sqlite3")
    body = json.dumps({"id": "one"}).encode()
    assert store.enqueue("key-one", body, "one", "trace-one") is True
    assert store.enqueue("key-one", body, "one", "trace-one") is False
    claimed = store.claim_due()
    assert claimed and claimed.status == "processing" and claimed.attempts == 1
    assert store.fail("key-one", "synthetic", 2, 0) == "retrying"
    assert store.claim_due() is not None
    assert store.fail("key-one", "synthetic", 2, 0) == "failed"
    assert store.requeue("key-one") is True
    claimed = store.claim_due()
    assert claimed is not None and claimed.attempts == 1
    store.complete("key-one", {"incident_id": "case-one"})
    assert store.get("key-one").status == "completed"
    assert store.reserve_handoff("trace-one") == (True, None)
    store.complete_handoff("trace-one", "execution-one")
    assert store.reserve_handoff("trace-one") == (False, "execution-one")
    assert store.reserve_handoff("trace-retry") == (True, None)
    store.reconcile_handoff("trace-retry", "retry")
    assert store.reserve_handoff("trace-retry") == (True, None)
    assert store.reserve_handoff("trace-observed") == (True, None)
    store.reconcile_handoff("trace-observed", "completed", "execution-observed")
    assert store.reserve_handoff("trace-observed") == (False, "execution-observed")


def test_worker_completes_case_shuffle_and_idempotent_approval(tmp_path: Path) -> None:
    store = DeliveryStore(tmp_path / "state.sqlite3")
    approvals = ApprovalStore(tmp_path / "state.sqlite3")
    hive = FakeHive()
    shuffle = FakeShuffle()
    pipeline = AlertPipeline(
        EmptyMisp(), hive, IncidentStore(tmp_path / "state.sqlite3"),
        AuditWriter(tmp_path / "audit.jsonl"),
    )
    payload = ADAPTER.normalize_alert(native_alert())
    store.enqueue(
        "key-worker", json.dumps(payload).encode(), payload["id"], "trace-worker"
    )
    worker = DeliveryWorker(
        store, pipeline, shuffle,
        {"account-activity": "http://shuffle.test/account"}, "s" * 32,
        approvals, AuditWriter(tmp_path / "audit.jsonl"), MetricsRegistry(),
        poll_seconds=0.01, max_attempts=3, retry_backoff_seconds=0,
    )
    assert asyncio.run(worker.process_once()) is True
    completed = store.get("key-worker")
    assert completed.status == "completed"
    assert completed.result["shuffle_execution_id"] == "shuffle-execution-1"
    assert shuffle.calls[0][2]["incident_id"] == "case-complete-1"
    assert shuffle.calls[0][2]["approval_required"] is True
    assert len(approvals.list("pending")) == 1
    assert "shuffle-execution-1" in hive.comments[0]


def test_shuffle_client_posts_authenticated_structured_handoff() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["url"] = str(request.url)
        observed["token"] = request.headers["X-SOC-LAB-TOKEN"]
        observed["idempotency_key"] = request.headers["Idempotency-Key"]
        observed["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"execution_id": "exec-1"})

    client = ShuffleClient(
        "http://shuffle.test", "api-key", timeout=1, attempts=1, backoff=0,
        verify=True, transport=httpx.MockTransport(handler),
    )

    async def run() -> dict:
        try:
            return await client.trigger(
                "http://shuffle.test/hooks/account", "hook-token", {"trace_id": "trace-1"}
            )
        finally:
            await client.close()

    assert asyncio.run(run())["execution_id"] == "exec-1"
    assert observed == {
        "url": "http://shuffle.test/hooks/account",
        "token": "hook-token",
        "idempotency_key": "trace-1",
        "payload": {"trace_id": "trace-1"},
    }


def test_shuffle_post_is_not_repeated_after_ambiguous_timeout() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("ambiguous", request=request)

    client = ShuffleClient(
        "http://shuffle.test", "api-key", timeout=1, attempts=3, backoff=0,
        verify=True, transport=httpx.MockTransport(handler),
    )

    async def run() -> None:
        try:
            with pytest.raises(IntegrationError, match="timeout"):
                await client.trigger(
                    "http://shuffle.test/hooks/account",
                    "hook-token",
                    {"trace_id": "trace-timeout"},
                )
        finally:
            await client.close()

    asyncio.run(run())
    assert calls == 1


def test_analyst_can_list_approvals_and_record_bounded_triage(
    settings_factory,
) -> None:
    app = create_app(
        settings_factory(),
        clients_override={"wazuh": None, "shuffle": None, "misp": None, "thehive": None},
    )
    headers = {"X-SOC-APPROVAL-TOKEN": "a" * 32}
    with TestClient(app) as client:
        assert client.get("/v1/approvals", headers=headers).status_code == 200
        created = client.post(
            "/v1/triage",
            headers={**headers, "X-SOC-ANALYST": "analyst.one"},
            json={
                "incident_id": "case-triage-1",
                "endpoint": "ubuntu-web-01",
                "collection": "linux_bounded_triage",
                "reason": "Validate the synthetic login alert context.",
            },
        )
        assert created.status_code == 201
        request_id = created.json()["request_id"]
        completed = client.post(
            f"/v1/triage/{request_id}/status",
            headers=headers,
            json={"status": "completed", "summary": "No unexpected process or connection."},
        )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"


def test_analyst_reconciles_ambiguous_shuffle_handoff(settings_factory) -> None:
    app = create_app(
        settings_factory(),
        clients_override={"wazuh": None, "shuffle": None, "misp": None, "thehive": None},
    )
    payload = json.dumps({"id": "ambiguous"}).encode()
    app.state.deliveries.enqueue("ambiguous-key", payload, "ambiguous", "ambiguous-trace")
    assert app.state.deliveries.claim_due() is not None
    assert app.state.deliveries.fail("ambiguous-key", "IntegrationError", 1, 0) == "failed"
    assert app.state.deliveries.reserve_handoff("ambiguous-trace") == (True, None)
    headers = {"X-SOC-APPROVAL-TOKEN": "a" * 32}
    with TestClient(app) as client:
        denied = client.post(
            "/v1/deliveries/ambiguous-key/handoff-reconciliation",
            json={"outcome": "retry", "note": "No matching execution exists."},
        )
        reconciled = client.post(
            "/v1/deliveries/ambiguous-key/handoff-reconciliation",
            headers=headers,
            json={"outcome": "retry", "note": "No matching execution exists."},
        )
    assert denied.status_code == 401
    assert reconciled.status_code == 200
    assert reconciled.json()["status"] == "queued"
    assert reconciled.json()["attempts"] == 0
    assert app.state.deliveries.reserve_handoff("ambiguous-trace") == (True, None)


def test_scenario_mapping_has_safe_general_fallback(synthetic_alert_payload: dict) -> None:
    from soc_integration.models import WazuhAlert

    alert = WazuhAlert.model_validate(synthetic_alert_payload)
    assert scenario_for(alert) == "suspicious-file"
    general = alert.model_copy(
        update={"data": {}, "rule": alert.rule.model_copy(update={"id": "100101"})}
    )
    assert scenario_for(general) == "security-alert"
