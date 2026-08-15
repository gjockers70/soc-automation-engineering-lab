"""Phase 9 enrichment, scoring, and incident handoff pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from .audit import AuditWriter
from .enrichment import EnrichmentResult, extract_indicators, misp_types, normalize_misp
from .incidents import IncidentStore
from .metrics import MetricsRegistry
from .models import WazuhAlert
from .reporting import analyst_summary
from .scoring import ScoreResult, score_alert, thehive_severity


@dataclass(frozen=True)
class PipelineResult:
    incident_id: str | None
    incident_disposition: str
    enrichments: list[EnrichmentResult]
    score: ScoreResult
    summary: str


class AlertPipeline:
    def __init__(
        self,
        misp: Any,
        thehive: Any,
        store: IncidentStore,
        audit: AuditWriter,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self.misp = misp
        self.thehive = thehive
        self.store = store
        self.audit = audit
        self.metrics = metrics

    async def process(self, alert: WazuhAlert) -> PipelineResult:
        indicators = extract_indicators(alert.data)
        enrichment_started = time.perf_counter()
        try:
            enrichments = [
                normalize_misp(indicator, await self.misp.search(indicator.value, misp_types(indicator)))
                for indicator in indicators
            ]
        finally:
            if self.metrics is not None:
                self.metrics.observe(
                    "soc_enrichment_duration_seconds",
                    time.perf_counter() - enrichment_started,
                )
        score = score_alert(alert.rule.level, enrichments)
        summary = analyst_summary(alert, enrichments, score)
        fingerprint = self.store.fingerprint(alert, indicators)
        tag = f"soc-lab:dedup:{fingerprint}"
        reserved, case_id = self.store.reserve(fingerprint)
        if not reserved:
            disposition = "reused" if case_id else "pending"
            self._audit(alert, disposition, case_id, fingerprint, enrichments, score)
            return PipelineResult(case_id, disposition, enrichments, score, summary)

        try:
            existing = await self.thehive.find_case_by_tag(tag)
            if existing:
                case_id = str(existing.get("_id") or existing.get("id") or "") or None
                if case_id:
                    self.store.complete(fingerprint, case_id)
                    self._audit(alert, "reused", case_id, fingerprint, enrichments, score)
                    return PipelineResult(case_id, "reused", enrichments, score, summary)

            case = await self.thehive.create_case(
                self._case_payload(alert, tag, enrichments, score, summary)
            )
            case_id = str(case.get("_id") or case.get("id") or "")
            if not case_id:
                raise RuntimeError("TheHive returned no case identifier")
            for result in enrichments:
                await self.thehive.add_observable(case_id, self._observable_payload(result))
            self.store.complete(fingerprint, case_id)
        except Exception:
            self.store.release(fingerprint)
            raise

        self._audit(alert, "created", case_id, fingerprint, enrichments, score)
        return PipelineResult(case_id, "created", enrichments, score, summary)

    @staticmethod
    def _case_payload(
        alert: WazuhAlert, tag: str, enrichments: list[EnrichmentResult], score: ScoreResult, summary: str
    ) -> dict[str, Any]:
        evidence = "\n".join(
            f"- {item.type}: {item.indicator} | reputation={item.reputation} | confidence={item.confidence}"
            for item in enrichments
        ) or "- No valid IOC was extracted."
        return {
            "title": f"SOC-LAB {alert.rule.description} [{alert.id}]",
            "description": (
                f"{summary}\n\nEvidence:\n{evidence}\n\nScoring factors:\n- "
                + "\n- ".join(score.factors)
                + "\n\nResponse status: analyst approval required; no response action executed."
            ),
            "severity": thehive_severity(score.severity),
            "tlp": 2,
            "pap": 2,
            "tags": [
                "soc-lab:phase9",
                "source:wazuh-synthetic",
                "approval:required",
                "response:not-executed", tag,
            ],
        }

    @staticmethod
    def _observable_payload(result: EnrichmentResult) -> dict[str, Any]:
        return {
            "dataType": result.type,
            "data": [result.indicator],
            "tlp": 2,
            "message": f"Local MISP reputation={result.reputation}; confidence={result.confidence}",
            "tags": result.tags,
            "ignoreSimilarity": False,
        }

    def _audit(
        self,
        alert: WazuhAlert,
        disposition: str,
        case_id: str | None,
        fingerprint: str,
        enrichments: list[EnrichmentResult],
        score: ScoreResult,
    ) -> None:
        self.audit.write(
            "pipeline.completed",
            alert_id=alert.id,
            incident_id=case_id,
            incident_disposition=disposition,
            fingerprint=fingerprint,
            indicator_count=len(enrichments),
            score=score.score,
            severity=score.severity,
            response_action_executed=False,
        )
