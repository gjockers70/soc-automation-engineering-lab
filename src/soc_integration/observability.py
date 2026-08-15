"""Read-only aggregation of bounded Shuffle playbook execution metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SUCCESS = {"FINISHED", "SUCCESS"}
FAILURE = {"ABORTED", "FAILURE", "FAILED"}


@dataclass(frozen=True)
class PlaybookMetrics:
    success: int = 0
    failure: int = 0
    running: int = 0
    duration_count: int = 0
    duration_sum: float = 0.0


def _epoch(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed / 1000 if parsed > 10_000_000_000 else parsed


async def collect_playbook_metrics(client: Any) -> PlaybookMetrics:
    counts = {"success": 0, "failure": 0, "running": 0}
    duration_count = 0
    duration_sum = 0.0
    for workflow in await client.workflows():
        if not str(workflow.get("name", "")).startswith("SOC-LAB PB"):
            continue
        workflow_id = str(workflow.get("id", ""))
        if not workflow_id:
            continue
        for execution in await client.executions(workflow_id):
            status = str(execution.get("status", "")).upper()
            result = "success" if status in SUCCESS else "failure" if status in FAILURE else "running"
            counts[result] += 1
            started = _epoch(execution.get("started_at"))
            completed = _epoch(execution.get("completed_at"))
            if started is not None and completed is not None and completed >= started:
                duration_count += 1
                duration_sum += completed - started
    return PlaybookMetrics(
        success=counts["success"],
        failure=counts["failure"],
        running=counts["running"],
        duration_count=duration_count,
        duration_sum=duration_sum,
    )
