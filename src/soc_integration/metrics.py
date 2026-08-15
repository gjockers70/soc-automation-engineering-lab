"""Thread-safe Prometheus text exposition without an external runtime dependency."""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict
from collections.abc import Mapping

METRICS: dict[str, tuple[str, str]] = {
    "soc_alerts_received_total": ("counter", "Authenticated synthetic alerts received by disposition."),
    "soc_alerts_processed_total": ("counter", "Alert pipeline completions by result."),
    "soc_webhook_rejections_total": ("counter", "Webhook rejections by bounded reason."),
    "soc_duplicate_suppression_total": ("counter", "Duplicate suppression decisions by layer."),
    "soc_incidents_total": ("counter", "Incident handoffs by disposition."),
    "soc_api_failures_total": ("counter", "Terminal integration failures by service and category."),
    "soc_approval_decisions_total": ("counter", "Recorded analyst approval decisions."),
    "soc_enrichment_duration_seconds": ("summary", "Time spent extracting and enriching indicators."),
    "soc_workflow_duration_seconds": ("summary", "End-to-end alert pipeline execution time."),
    "soc_dependency_healthy": ("gauge", "Current dependency health where 1 is healthy."),
    "soc_metrics_collection_up": ("gauge", "Current metrics collector status where 1 is successful."),
    "soc_playbook_executions": ("gauge", "Current retained Shuffle execution count by result."),
    "soc_playbook_execution_duration_seconds": ("gauge", "Duration aggregate for retained Shuffle executions."),
    "soc_gateway_start_time_seconds": ("gauge", "Gateway process start time in Unix seconds."),
    "soc_delivery_attempts_total": ("counter", "Durable delivery processing attempts by result."),
    "soc_delivery_queue_items": ("gauge", "Durable delivery records by active state."),
    "soc_delivery_oldest_pending_seconds": ("gauge", "Age of the oldest pending delivery."),
    "soc_shuffle_handoffs_total": ("counter", "Gateway-to-Shuffle handoffs by result."),
}

_NAME = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")


def _labels(labels: Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:
    normalized = tuple(sorted((str(key), str(value)) for key, value in (labels or {}).items()))
    if any(not _NAME.fullmatch(key) for key, _ in normalized):
        raise ValueError("invalid metric label name")
    return normalized


def _escape(value: str) -> str:
    backslash = chr(92)
    return (
        value.replace(backslash, backslash * 2)
        .replace(chr(10), backslash + "n")
        .replace(chr(34), backslash + chr(34))
    )


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    return "{" + ",".join(f'{key}="{_escape(value)}"' for key, value in labels) + "}"


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._observations: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[int, float]] = {}
        self.set("soc_gateway_start_time_seconds", time.time())
        for result in ("success", "failure", "running"):
            self.set("soc_playbook_executions", 0, {"result": result})

    def inc(self, name: str, labels: Mapping[str, str] | None = None, amount: float = 1) -> None:
        self._require(name, "counter")
        if amount < 0:
            raise ValueError("counter amount must be non-negative")
        with self._lock:
            self._values[(name, _labels(labels))] += amount

    def set(self, name: str, value: float, labels: Mapping[str, str] | None = None) -> None:
        self._require(name, "gauge")
        with self._lock:
            self._values[(name, _labels(labels))] = float(value)

    def observe(self, name: str, value: float, labels: Mapping[str, str] | None = None) -> None:
        self._require(name, "summary")
        key = (name, _labels(labels))
        with self._lock:
            count, total = self._observations.get(key, (0, 0.0))
            self._observations[key] = (count + 1, total + max(0.0, float(value)))

    def render(self) -> str:
        with self._lock:
            values = dict(self._values)
            observations = dict(self._observations)
        lines: list[str] = []
        for name, (metric_type, help_text) in METRICS.items():
            lines.extend((f"# HELP {name} {help_text}", f"# TYPE {name} {metric_type}"))
            for (candidate, labels), value in sorted(values.items()):
                if candidate == name:
                    lines.append(f"{name}{_format_labels(labels)} {value:g}")
            for (candidate, labels), (count, total) in sorted(observations.items()):
                if candidate == name:
                    formatted = _format_labels(labels)
                    lines.append(f"{name}_count{formatted} {count}")
                    lines.append(f"{name}_sum{formatted} {total:g}")
        newline = chr(10)
        return newline.join(lines) + newline

    @staticmethod
    def _require(name: str, expected: str) -> None:
        definition = METRICS.get(name)
        if definition is None or definition[0] != expected:
            raise ValueError(f"metric {name} is not a {expected}")
