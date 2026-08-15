"""Background delivery processor for the durable alert inbox."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from .approvals import ApprovalStore
from .audit import AuditWriter
from .deliveries import DeliveryStore
from .integrations.base import IntegrationError
from .metrics import MetricsRegistry
from .models import ApprovalProposal, WazuhAlert

logger = logging.getLogger("soc.integration.worker")


def scenario_for(alert: WazuhAlert) -> str:
    if alert.rule.id == "100100":
        return "suspicious-login"
    if alert.rule.id == "100102":
        return "account-activity"
    keys = {str(key).lower() for key in alert.data}
    flattened = str(alert.data).lower()
    if keys & {"hash", "md5", "sha1", "sha256"} or "sha256" in flattened:
        return "suspicious-file"
    if keys & {"domain", "query", "url", "uri"} or ".test" in flattened:
        return "suspicious-domain"
    return "security-alert"


class DeliveryWorker:
    def __init__(
        self,
        store: DeliveryStore,
        pipeline: Any,
        shuffle: Any,
        shuffle_webhooks: dict[str, str],
        shuffle_token: str,
        approvals: ApprovalStore,
        audit: AuditWriter,
        metrics: MetricsRegistry,
        *,
        poll_seconds: float,
        max_attempts: int,
        retry_backoff_seconds: float,
    ) -> None:
        self.store = store
        self.pipeline = pipeline
        self.shuffle = shuffle
        self.shuffle_webhooks = shuffle_webhooks
        self.shuffle_token = shuffle_token
        self.approvals = approvals
        self.audit = audit
        self.metrics = metrics
        self.poll_seconds = poll_seconds
        self.max_attempts = max_attempts
        self.retry_backoff_seconds = retry_backoff_seconds
        self.stop_event = asyncio.Event()

    async def run(self) -> None:
        recovered = self.store.recover_processing()
        if recovered:
            self.audit.write("worker.recovered", deliveries=recovered)
        while not self.stop_event.is_set():
            processed = await self.process_once()
            self.refresh_queue_metrics()
            if not processed:
                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=self.poll_seconds)
                except TimeoutError:
                    pass

    async def process_once(self) -> bool:
        delivery = self.store.claim_due()
        if delivery is None:
            return False
        started = time.perf_counter()
        try:
            alert = WazuhAlert.model_validate(delivery.payload)
            result = await self.pipeline.process(alert)
            scenario = scenario_for(alert)
            handoff = {
                "schema_version": 1,
                "trace_id": delivery.trace_id,
                "alert_id": alert.id,
                "incident_id": result.incident_id,
                "incident_disposition": result.incident_disposition,
                "scenario": scenario,
                "score": result.score.score,
                "severity": result.score.severity,
                "summary": result.summary,
                "indicators": [item.model_dump() for item in result.enrichments],
                "approval_required": scenario == "account-activity",
                "response_action_executed": False,
            }
            execution_id = None
            webhook = self.shuffle_webhooks.get(scenario)
            if self.shuffle is not None and webhook:
                reserved, prior_execution = self.store.reserve_handoff(delivery.trace_id)
                if not reserved:
                    if prior_execution is None:
                        raise RuntimeError("shuffle handoff requires operator reconciliation")
                    execution_id = prior_execution
                else:
                    try:
                        execution = await self.shuffle.trigger(
                            webhook, self.shuffle_token, handoff
                        )
                    except IntegrationError as exc:
                        # A timeout or transport failure may occur after Shuffle accepted the
                        # request. Retain the reservation so an automatic retry cannot create
                        # a second execution. Definite HTTP rejections are safe to retry.
                        if exc.category not in {"timeout", "unavailable"}:
                            self.store.release_handoff(delivery.trace_id)
                        raise
                    except Exception:
                        raise
                    execution_id = str(
                        execution.get("execution_id") or execution.get("id") or ""
                    ) or None
                    self.store.complete_handoff(delivery.trace_id, execution_id)
                    self.metrics.inc("soc_shuffle_handoffs_total", {"result": "success"})
                if result.incident_id and hasattr(self.pipeline.thehive, "add_comment"):
                    await self.pipeline.thehive.add_comment(
                        result.incident_id,
                        f"Shuffle handoff trace={delivery.trace_id}; "
                        f"execution={execution_id or 'accepted-without-id'}; scenario={scenario}",
                    )
            if scenario == "account-activity" and result.incident_id:
                self.approvals.create_once(
                    delivery.trace_id,
                    ApprovalProposal(
                        incident_id=result.incident_id,
                        action="disable_synthetic_account",
                        target="soc-response-test",
                        reason="Synthetic account activity requires analyst review.",
                        evidence=[
                            f"trace_id={delivery.trace_id}",
                            f"score={result.score.score}",
                            f"severity={result.score.severity}",
                        ],
                        confidence=min(1.0, result.score.score / 100),
                    ),
                )
            completed = {
                **handoff,
                "shuffle_execution_id": execution_id,
            }
            self.store.complete(delivery.key, completed)
            self.metrics.inc("soc_alerts_processed_total", {"result": "success"})
            self.metrics.observe(
                "soc_workflow_duration_seconds", time.perf_counter() - started
            )
            self.metrics.inc(
                "soc_incidents_total", {"disposition": result.incident_disposition}
            )
            if result.incident_disposition == "reused":
                self.metrics.inc("soc_duplicate_suppression_total", {"layer": "incident"})
            self.audit.write(
                "delivery.completed", trace_id=delivery.trace_id, alert_id=alert.id,
                incident_id=result.incident_id, shuffle_execution_id=execution_id,
                scenario=scenario, response_action_executed=False,
            )
        except Exception as exc:
            delay = self.retry_backoff_seconds * max(1, 2 ** (delivery.attempts - 1))
            status = self.store.fail(
                delivery.key, type(exc).__name__, self.max_attempts, delay
            )
            self.metrics.inc("soc_alerts_processed_total", {"result": "failure"})
            self.metrics.observe(
                "soc_workflow_duration_seconds", time.perf_counter() - started
            )
            self.metrics.inc("soc_delivery_attempts_total", {"result": status})
            if isinstance(exc, IntegrationError):
                self.metrics.inc(
                    "soc_api_failures_total",
                    {"service": exc.service, "category": exc.category},
                )
                if exc.service == "shuffle":
                    self.metrics.inc("soc_shuffle_handoffs_total", {"result": "failure"})
            self.audit.write(
                "delivery.processing_failed", trace_id=delivery.trace_id,
                alert_id=delivery.alert_id, category=type(exc).__name__, status=status,
                response_action_executed=False,
            )
            logger.warning(
                "delivery_processing_failed trace_id=%s category=%s status=%s",
                delivery.trace_id, type(exc).__name__, status,
            )
        return True

    def refresh_queue_metrics(self) -> None:
        counts = self.store.counts()
        for status in ("queued", "processing", "retrying", "failed"):
            self.metrics.set("soc_delivery_queue_items", counts.get(status, 0), {"status": status})
        self.metrics.set("soc_delivery_oldest_pending_seconds", self.store.oldest_pending_age())

    def stop(self) -> None:
        self.stop_event.set()
