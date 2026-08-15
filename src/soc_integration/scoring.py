"""Explainable deterministic alert scoring."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .enrichment import EnrichmentResult


class ScoreResult(BaseModel):
    score: int = Field(ge=0, le=100)
    severity: str
    factors: list[str]


def score_alert(rule_level: int, enrichments: list[EnrichmentResult]) -> ScoreResult:
    rule_points = min(rule_level * 4, 60)
    confidence = max((item.confidence for item in enrichments if item.sources), default=0)
    intelligence_points = int(confidence * 0.3 + 0.5)
    indicator_points = min(len(enrichments) * 2, 10)
    score = min(rule_points + intelligence_points + indicator_points, 100)
    severity = "critical" if score >= 80 else "high" if score >= 60 else "medium" if score >= 30 else "low"
    factors = [
        f"wazuh_rule_level:{rule_level}={rule_points}",
        f"max_local_intelligence_confidence:{confidence}={intelligence_points}",
        f"validated_indicator_count:{len(enrichments)}={indicator_points}",
    ]
    return ScoreResult(score=score, severity=severity, factors=factors)


def thehive_severity(severity: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 3}[severity]
