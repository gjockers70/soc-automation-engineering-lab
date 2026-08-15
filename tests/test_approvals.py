from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from soc_integration.app import create_app
from soc_integration.approvals import ApprovalConflict, ApprovalStore
from soc_integration.config import Settings
from soc_integration.models import ApprovalDecision, ApprovalProposal


def proposal(**overrides: object) -> ApprovalProposal:
    values = {
        "incident_id": "case-123",
        "action": "disable_synthetic_account",
        "target": "soc-response-test",
        "reason": "Repeated suspicious authentication in the isolated lab.",
        "evidence": ["alert=synthetic-001", "score=92"],
        "confidence": 0.92,
    }
    values.update(overrides)
    return ApprovalProposal.model_validate(values)


def decision(value: str) -> ApprovalDecision:
    return ApprovalDecision(decision=value, analyst="analyst.one", note="Reviewed synthetic evidence.")


def test_reject_and_escalate_never_change_identity() -> None:
    with TemporaryDirectory() as directory:
        store = ApprovalStore(Path(directory) / "state.sqlite3")
        rejected = store.decide(store.create(proposal()).approval_id, decision("reject"))
        escalated = store.decide(store.create(proposal()).approval_id, decision("escalate"))
        assert rejected.response_action_executed is False
        assert escalated.response_action_executed is False
        assert store.identity_state("soc-response-test") == "enabled"


def test_approval_executes_once_and_repeated_decision_is_idempotent() -> None:
    with TemporaryDirectory() as directory:
        store = ApprovalStore(Path(directory) / "state.sqlite3")
        approval_id = store.create(proposal()).approval_id
        approved = store.decide(approval_id, decision("approve"))
        repeated = store.decide(approval_id, decision("approve"))
        assert approved.execution_result == "disabled"
        assert approved.response_action_executed is True
        assert repeated == approved
        assert store.identity_state("soc-response-test") == "disabled"


def test_conflicting_final_decision_is_rejected() -> None:
    with TemporaryDirectory() as directory:
        store = ApprovalStore(Path(directory) / "state.sqlite3")
        approval_id = store.create(proposal()).approval_id
        store.decide(approval_id, decision("reject"))
        with pytest.raises(ApprovalConflict):
            store.decide(approval_id, decision("approve"))


def test_allowlist_is_enforced_by_validation() -> None:
    with pytest.raises(ValidationError):
        proposal(target="real-user")
    with pytest.raises(ValidationError):
        proposal(action="disable_linux_account")


def test_api_separates_proposal_and_approval_credentials() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        settings = Settings(
            webhook_token="w" * 32,
            approval_token="a" * 32,
            audit_path=root / "audit.jsonl",
            idempotency_db=root / "state.sqlite3",
        )
        with TestClient(create_app(settings, clients_override={
            "wazuh": None, "shuffle": None, "misp": None, "thehive": None,
        })) as client:
            created = client.post(
                "/v1/approvals", json=proposal().model_dump(),
                headers={"X-SOC-LAB-TOKEN": "w" * 32},
            )
            assert created.status_code == 201
            approval_id = created.json()["approval_id"]
            unauthorized = client.post(
                f"/v1/approvals/{approval_id}/decision", json=decision("approve").model_dump(),
            )
            assert unauthorized.status_code == 401
            approved = client.post(
                f"/v1/approvals/{approval_id}/decision", json=decision("approve").model_dump(),
                headers={"X-SOC-APPROVAL-TOKEN": "a" * 32},
            )
            assert approved.status_code == 200
            assert approved.json()["response_action_executed"] is True
            state = client.get(
                "/v1/lab-identities/soc-response-test",
                headers={"X-SOC-APPROVAL-TOKEN": "a" * 32},
            )
            assert state.json()["state"] == "disabled"
