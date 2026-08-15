"""Small, deterministic helpers for operational failure diagnosis."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class EndpointHealth(BaseModel):
    status: Literal["connected", "stale", "disconnected"]
    age_seconds: int = Field(ge=0)
    detail: Literal["heartbeat_current", "heartbeat_delayed", "heartbeat_expired"]


def classify_endpoint_health(
    last_seen: datetime,
    *,
    observed_at: datetime | None = None,
    stale_after_seconds: int = 120,
    disconnected_after_seconds: int = 300,
) -> EndpointHealth:
    """Classify a heartbeat without contacting or changing the endpoint."""
    now = observed_at or datetime.now(timezone.utc)
    if last_seen.tzinfo is None or now.tzinfo is None:
        raise ValueError("heartbeat timestamps must include a timezone")
    if stale_after_seconds < 1 or disconnected_after_seconds <= stale_after_seconds:
        raise ValueError("heartbeat thresholds are invalid")
    age = max(0, int((now - last_seen).total_seconds()))
    if age > disconnected_after_seconds:
        return EndpointHealth(status="disconnected", age_seconds=age, detail="heartbeat_expired")
    if age > stale_after_seconds:
        return EndpointHealth(status="stale", age_seconds=age, detail="heartbeat_delayed")
    return EndpointHealth(status="connected", age_seconds=age, detail="heartbeat_current")
