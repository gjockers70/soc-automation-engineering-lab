"""Validated webhook and API response models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AlertRule(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    level: int = Field(ge=0, le=15)
    description: str = Field(min_length=1, max_length=500)


class AlertAgent(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)


class WazuhAlert(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1, max_length=128)
    timestamp: datetime
    rule: AlertRule
    agent: AlertAgent
    data: dict[str, Any] = Field(default_factory=dict)
    synthetic: bool

    @field_validator("timestamp")
    @classmethod
    def timestamp_requires_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value

    @field_validator("synthetic")
    @classmethod
    def synthetic_only(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("the gateway accepts synthetic lab alerts only")
        return value


class WebhookReceipt(BaseModel):
    status: Literal["accepted", "duplicate"]
    alert_id: str
    idempotency_key: str
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    response_action_executed: Literal[False] = False
    incident_id: str | None = None
    incident_disposition: Literal["created", "reused", "pending"] | None = None
    indicator_count: int | None = None
    score: int | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    summary: str | None = None
    enrichments: list[dict[str, Any]] | None = None
    processing_status: Literal["queued", "processing", "retrying", "completed", "failed"] = "queued"
    status_url: str | None = None
    trace_id: str | None = None
    shuffle_execution_id: str | None = None


class DeliveryStatus(BaseModel):
    idempotency_key: str
    alert_id: str
    trace_id: str
    status: Literal["queued", "processing", "retrying", "completed", "failed"]
    attempts: int
    last_error: str | None = None
    incident_id: str | None = None
    incident_disposition: Literal["created", "reused", "pending"] | None = None
    shuffle_execution_id: str | None = None
    scenario: str | None = None
    score: int | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    next_attempt_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class HandoffReconciliation(BaseModel):
    outcome: Literal["retry", "completed"]
    execution_id: str | None = Field(default=None, min_length=1, max_length=128)
    note: str = Field(min_length=8, max_length=1000)

    @model_validator(mode="after")
    def execution_matches_outcome(self) -> "HandoffReconciliation":
        if self.outcome == "completed" and not self.execution_id:
            raise ValueError("completed handoff reconciliation requires an execution ID")
        if self.outcome == "retry" and self.execution_id:
            raise ValueError("retry handoff reconciliation cannot include an execution ID")
        return self


class TriageRequest(BaseModel):
    incident_id: str = Field(min_length=1, max_length=128)
    endpoint: str = Field(pattern=r"^(ubuntu-web-01|win11-01)$")
    collection: Literal["linux_bounded_triage", "windows_bounded_triage"]
    reason: str = Field(min_length=8, max_length=1000)

    @model_validator(mode="after")
    def collection_matches_endpoint(self) -> "TriageRequest":
        expected = {
            "ubuntu-web-01": "linux_bounded_triage",
            "win11-01": "windows_bounded_triage",
        }
        if expected[self.endpoint] != self.collection:
            raise ValueError("triage collection does not match the selected endpoint")
        return self


class TriageRecord(TriageRequest):
    request_id: str
    status: Literal["requested", "collecting", "completed", "failed"]
    requested_by: str
    created_at: datetime
    updated_at: datetime
    summary: str | None = None


class TriageUpdate(BaseModel):
    status: Literal["collecting", "completed", "failed"]
    summary: str | None = Field(default=None, max_length=4000)


class ApprovalProposal(BaseModel):
    incident_id: str = Field(min_length=1, max_length=128)
    action: Literal["disable_synthetic_account"]
    target: Literal["soc-response-test"]
    reason: str = Field(min_length=8, max_length=1000)
    evidence: list[Annotated[str, Field(min_length=1, max_length=500)]] = Field(min_length=1, max_length=20)
    confidence: float = Field(ge=0, le=1)


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject", "escalate"]
    analyst: str = Field(pattern=r"^[A-Za-z0-9._@-]{3,64}$")
    note: str = Field(min_length=3, max_length=1000)


class ApprovalRecord(ApprovalProposal):
    approval_id: str
    status: Literal["pending", "approve", "reject", "escalate"]
    created_at: datetime
    decided_at: datetime | None = None
    analyst: str | None = None
    analyst_note: str | None = None
    execution_result: Literal["disabled", "already_disabled"] | None = None
    response_action_executed: bool = False


class IntegrationHealth(BaseModel):
    status: Literal["healthy", "unhealthy", "not_configured"]
    latency_ms: int | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    integrations: dict[str, IntegrationHealth]
