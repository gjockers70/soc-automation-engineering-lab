"""Concise analyst-facing summaries."""

from __future__ import annotations

from .enrichment import EnrichmentResult
from .models import WazuhAlert
from .scoring import ScoreResult


def analyst_summary(alert: WazuhAlert, enrichments: list[EnrichmentResult], score: ScoreResult) -> str:
    known = [item for item in enrichments if item.sources]
    indicator_text = ", ".join(f"{item.type}:{item.indicator}" for item in enrichments) or "none"
    return (
        f"Synthetic Wazuh alert {alert.id} on {alert.agent.name}: {alert.rule.description}. "
        f"Validated indicators: {indicator_text}. Local MISP matches: {len(known)}. "
        f"Deterministic risk score: {score.score}/100 ({score.severity}). "
        "Analyst review is required; no response action was executed."
    )
