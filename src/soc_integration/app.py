"""Authenticated alert intake and integration health API."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response

from .approvals import ApprovalConflict, ApprovalNotFound, ApprovalStore
from .audit import AuditWriter
from .config import Settings
from .deliveries import Delivery, DeliveryStore
from .health import integration_health
from .idempotency import IdempotencyConflict
from .incidents import IncidentStore
from .integrations import MispClient, ShuffleClient, TheHiveClient, WazuhClient
from .integrations.base import IntegrationError
from .logging import configure_logging
from .metrics import MetricsRegistry
from .models import (
    ApprovalDecision,
    ApprovalProposal,
    ApprovalRecord,
    DeliveryStatus,
    HandoffReconciliation,
    HealthResponse,
    TriageRecord,
    TriageRequest,
    TriageUpdate,
    WazuhAlert,
    WebhookReceipt,
)
from .observability import collect_playbook_metrics
from .pipeline import AlertPipeline
from .triage import TriageStore
from .worker import DeliveryWorker

logger = logging.getLogger("soc.integration")


def create_app(settings: Settings | None = None, clients_override: dict | None = None) -> FastAPI:
    config = settings or Settings.from_env()
    client_options = {
        "timeout": config.request_timeout_seconds,
        "attempts": config.retry_attempts,
        "backoff": config.retry_backoff_seconds,
        "verify": config.verify_internal_tls,
    }
    clients = clients_override or {
        "wazuh": WazuhClient(str(config.wazuh_url), config.wazuh_username, config.wazuh_password.get_secret_value(), **client_options) if config.wazuh_username else None,
        "shuffle": ShuffleClient(str(config.shuffle_url), config.shuffle_api_key.get_secret_value(), **client_options) if config.shuffle_api_key.get_secret_value() else None,
        "misp": MispClient(str(config.misp_url), config.misp_api_key.get_secret_value(), **client_options) if config.misp_api_key.get_secret_value() else None,
        "thehive": TheHiveClient(str(config.thehive_url), config.thehive_organisation, config.thehive_username, config.thehive_password.get_secret_value(), **client_options) if config.thehive_username else None,
    }

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        worker_task = None
        if app.state.worker is not None:
            worker_task = asyncio.create_task(app.state.worker.run())
        yield
        if app.state.worker is not None:
            app.state.worker.stop()
        if worker_task is not None:
            await worker_task
        for client in clients.values():
            if client is not None:
                await client.close()

    app = FastAPI(title="SOC Integration Gateway", version="0.5.0", lifespan=lifespan)
    app.state.settings = config
    app.state.deliveries = DeliveryStore(config.idempotency_db)
    app.state.audit = AuditWriter(config.audit_path)
    app.state.clients = clients
    app.state.incidents = IncidentStore(config.idempotency_db)
    app.state.approvals = ApprovalStore(config.idempotency_db)
    app.state.triage = TriageStore(config.idempotency_db)
    app.state.metrics = MetricsRegistry()
    app.state.pipeline = (
        AlertPipeline(
            clients["misp"],
            clients["thehive"],
            app.state.incidents,
            app.state.audit,
            app.state.metrics,
        )
        if clients.get("misp") is not None and clients.get("thehive") is not None else None
    )
    shuffle_webhooks = {
        name: str(value)
        for name, value in {
            "suspicious-login": config.shuffle_suspicious_login_webhook,
            "suspicious-file": config.shuffle_suspicious_file_webhook,
            "suspicious-domain": config.shuffle_suspicious_domain_webhook,
            "account-activity": config.shuffle_account_activity_webhook,
            "security-alert": config.shuffle_security_alert_webhook,
        }.items()
        if value is not None
    }
    app.state.worker = (
        DeliveryWorker(
            app.state.deliveries,
            app.state.pipeline,
            clients.get("shuffle"),
            shuffle_webhooks,
            config.shuffle_webhook_token.get_secret_value(),
            app.state.approvals,
            app.state.audit,
            app.state.metrics,
            poll_seconds=config.worker_poll_seconds,
            max_attempts=config.worker_max_attempts,
            retry_backoff_seconds=config.worker_retry_backoff_seconds,
        )
        if app.state.pipeline is not None
        else None
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        if request.url.path == "/v1/webhooks/wazuh":
            app.state.metrics.inc("soc_webhook_rejections_total", {"reason": "schema"})
        return await request_validation_exception_handler(request, exc)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/health/ready", response_model=HealthResponse)
    async def ready() -> HealthResponse:
        checks = await integration_health(app.state.clients)
        for name, item in checks.items():
            app.state.metrics.set(
                "soc_dependency_healthy",
                1 if item.status == "healthy" else 0,
                {"dependency": name},
            )
        overall = "healthy" if all(item.status == "healthy" for item in checks.values()) else "degraded"
        return HealthResponse(status=overall, integrations=checks)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        if app.state.worker is not None:
            app.state.worker.refresh_queue_metrics()
        checks = await integration_health(app.state.clients)
        for name, item in checks.items():
            app.state.metrics.set(
                "soc_dependency_healthy",
                1 if item.status == "healthy" else 0,
                {"dependency": name},
            )
        shuffle = app.state.clients.get("shuffle")
        if shuffle is None:
            app.state.metrics.set("soc_metrics_collection_up", 0, {"collector": "shuffle"})
        else:
            try:
                summary = await collect_playbook_metrics(shuffle)
                app.state.metrics.set("soc_metrics_collection_up", 1, {"collector": "shuffle"})
                for result, value in (
                    ("success", summary.success),
                    ("failure", summary.failure),
                    ("running", summary.running),
                ):
                    app.state.metrics.set("soc_playbook_executions", value, {"result": result})
                app.state.metrics.set(
                    "soc_playbook_execution_duration_seconds",
                    summary.duration_count,
                    {"statistic": "count"},
                )
                app.state.metrics.set(
                    "soc_playbook_execution_duration_seconds",
                    summary.duration_sum,
                    {"statistic": "sum"},
                )
            except IntegrationError:
                app.state.metrics.set("soc_metrics_collection_up", 0, {"collector": "shuffle"})
        return Response(
            app.state.metrics.render(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    def require_approval_token(provided: str) -> None:
        if not hmac.compare_digest(provided, config.approval_token.get_secret_value()):
            app.state.metrics.inc(
                "soc_webhook_rejections_total", {"reason": "approval_authentication"}
            )
            app.state.audit.write("approval.authentication_failed")
            raise HTTPException(status_code=401, detail="invalid approval authentication")

    async def add_case_note(case_id: str, message: str) -> None:
        client = app.state.clients.get("thehive")
        if client is None:
            return
        try:
            await client.add_comment(case_id, message)
        except IntegrationError as exc:
            app.state.metrics.inc(
                "soc_api_failures_total",
                {"service": exc.service, "category": exc.category},
            )
            app.state.audit.write(
                "approval.case_sync_failed", incident_id=case_id,
                service=exc.service, category=exc.category,
            )

    @app.post("/v1/approvals", response_model=ApprovalRecord, status_code=status.HTTP_201_CREATED)
    async def create_approval(
        proposal: ApprovalProposal,
        x_soc_lab_token: str = Header(default=""),
    ) -> ApprovalRecord:
        if not hmac.compare_digest(x_soc_lab_token, config.webhook_token.get_secret_value()):
            app.state.metrics.inc(
                "soc_webhook_rejections_total", {"reason": "proposal_authentication"}
            )
            app.state.audit.write("approval.proposal_authentication_failed")
            raise HTTPException(status_code=401, detail="invalid proposal authentication")
        record = app.state.approvals.create(proposal)
        app.state.audit.write(
            "approval.proposed", approval_id=record.approval_id,
            incident_id=record.incident_id, action=record.action, target=record.target,
            confidence=record.confidence, response_action_executed=False,
        )
        await add_case_note(
            record.incident_id,
            f"Approval proposed: {record.approval_id}; action={record.action}; "
            f"target={record.target}; confidence={record.confidence:.2f}; status=pending",
        )
        return record

    @app.get("/v1/approvals/{approval_id}", response_model=ApprovalRecord)
    async def get_approval(
        approval_id: str, x_soc_approval_token: str = Header(default=""),
    ) -> ApprovalRecord:
        require_approval_token(x_soc_approval_token)
        try:
            return app.state.approvals.get(approval_id)
        except ApprovalNotFound as exc:
            raise HTTPException(status_code=404, detail="approval not found") from exc

    @app.get("/v1/approvals", response_model=list[ApprovalRecord])
    async def list_approvals(
        approval_status: str | None = None,
        x_soc_approval_token: str = Header(default=""),
    ) -> list[ApprovalRecord]:
        require_approval_token(x_soc_approval_token)
        if approval_status not in {None, "pending", "approve", "reject", "escalate"}:
            raise HTTPException(status_code=422, detail="invalid approval status")
        return app.state.approvals.list(approval_status)

    @app.post("/v1/approvals/{approval_id}/decision", response_model=ApprovalRecord)
    async def decide_approval(
        approval_id: str,
        decision: ApprovalDecision,
        x_soc_approval_token: str = Header(default=""),
    ) -> ApprovalRecord:
        require_approval_token(x_soc_approval_token)
        try:
            record = app.state.approvals.decide(approval_id, decision)
        except ApprovalNotFound as exc:
            raise HTTPException(status_code=404, detail="approval not found") from exc
        except ApprovalConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        app.state.audit.write(
            "approval.decided", approval_id=record.approval_id,
            incident_id=record.incident_id, decision=record.status,
            analyst=record.analyst, action=record.action, target=record.target,
            execution_result=record.execution_result,
            response_action_executed=record.response_action_executed,
        )
        await add_case_note(
            record.incident_id,
            f"Approval decision: {record.approval_id}; decision={record.status}; "
            f"analyst={record.analyst}; result={record.execution_result or 'no action'}",
        )
        app.state.metrics.inc("soc_approval_decisions_total", {"decision": record.status})
        return record

    @app.get("/v1/lab-identities/{identity}")
    async def get_lab_identity(
        identity: str, x_soc_approval_token: str = Header(default=""),
    ) -> dict[str, str]:
        require_approval_token(x_soc_approval_token)
        if identity != "soc-response-test":
            raise HTTPException(status_code=404, detail="lab identity not found")
        return {"identity": identity, "state": app.state.approvals.identity_state(identity)}

    @app.post("/v1/triage", response_model=TriageRecord, status_code=status.HTTP_201_CREATED)
    async def create_triage(
        request: TriageRequest,
        x_soc_analyst: str = Header(min_length=3, max_length=64),
        x_soc_approval_token: str = Header(default=""),
    ) -> TriageRecord:
        require_approval_token(x_soc_approval_token)
        record = app.state.triage.create(request, x_soc_analyst)
        app.state.audit.write(
            "triage.requested", request_id=record.request_id,
            incident_id=record.incident_id, endpoint=record.endpoint,
            collection=record.collection, analyst=x_soc_analyst,
            response_action_executed=False,
        )
        await add_case_note(
            record.incident_id,
            f"Bounded triage requested: {record.request_id}; endpoint={record.endpoint}; "
            f"collection={record.collection}; analyst={x_soc_analyst}",
        )
        return record

    @app.get("/v1/triage", response_model=list[TriageRecord])
    async def list_triage(
        x_soc_approval_token: str = Header(default=""),
    ) -> list[TriageRecord]:
        require_approval_token(x_soc_approval_token)
        return app.state.triage.list()

    @app.post("/v1/triage/{request_id}/status", response_model=TriageRecord)
    async def update_triage(
        request_id: str,
        update: TriageUpdate,
        x_soc_approval_token: str = Header(default=""),
    ) -> TriageRecord:
        require_approval_token(x_soc_approval_token)
        try:
            record = app.state.triage.update(request_id, update.status, update.summary)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="triage request not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        app.state.audit.write(
            "triage.updated", request_id=record.request_id,
            incident_id=record.incident_id, status=record.status,
            response_action_executed=False,
        )
        if record.summary:
            await add_case_note(
                record.incident_id,
                f"Bounded triage {record.request_id} status={record.status}. "
                f"Sanitized summary: {record.summary}",
            )
        return record

    def delivery_status(record: Delivery) -> DeliveryStatus:
        result = record.result or {}
        return DeliveryStatus(
            idempotency_key=record.key,
            alert_id=record.alert_id,
            trace_id=record.trace_id,
            status=record.status,
            attempts=record.attempts,
            last_error=record.last_error,
            incident_id=result.get("incident_id"),
            incident_disposition=result.get("incident_disposition"),
            shuffle_execution_id=result.get("shuffle_execution_id"),
            scenario=result.get("scenario"),
            score=result.get("score"),
            severity=result.get("severity"),
            next_attempt_at=record.next_attempt_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @app.get("/v1/deliveries/{idempotency_key}", response_model=DeliveryStatus)
    async def get_delivery(
        idempotency_key: str,
        x_soc_lab_token: str = Header(default=""),
    ) -> DeliveryStatus:
        if not hmac.compare_digest(
            x_soc_lab_token, config.webhook_token.get_secret_value()
        ):
            raise HTTPException(status_code=401, detail="invalid webhook authentication")
        try:
            return delivery_status(app.state.deliveries.get(idempotency_key))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="delivery not found") from exc

    @app.post("/v1/deliveries/{idempotency_key}/replay", response_model=DeliveryStatus)
    async def replay_delivery(
        idempotency_key: str,
        x_soc_approval_token: str = Header(default=""),
    ) -> DeliveryStatus:
        require_approval_token(x_soc_approval_token)
        if not app.state.deliveries.requeue(idempotency_key):
            raise HTTPException(status_code=409, detail="only failed deliveries can be replayed")
        app.state.audit.write("delivery.requeued", idempotency_key=idempotency_key)
        return delivery_status(app.state.deliveries.get(idempotency_key))

    @app.post(
        "/v1/deliveries/{idempotency_key}/handoff-reconciliation",
        response_model=DeliveryStatus,
    )
    async def reconcile_delivery_handoff(
        idempotency_key: str,
        reconciliation: HandoffReconciliation,
        x_soc_approval_token: str = Header(default=""),
    ) -> DeliveryStatus:
        require_approval_token(x_soc_approval_token)
        try:
            record = app.state.deliveries.get(idempotency_key)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="delivery not found") from exc
        if record.status != "failed":
            raise HTTPException(
                status_code=409,
                detail="handoff reconciliation requires a failed delivery",
            )
        try:
            app.state.deliveries.reconcile_handoff(
                record.trace_id,
                reconciliation.outcome,
                reconciliation.execution_id,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Shuffle handoff not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if not app.state.deliveries.requeue(idempotency_key):
            raise HTTPException(status_code=409, detail="failed delivery could not be requeued")
        app.state.audit.write(
            "shuffle.handoff_reconciled",
            idempotency_key=idempotency_key,
            trace_id=record.trace_id,
            outcome=reconciliation.outcome,
            execution_id=reconciliation.execution_id,
            note=reconciliation.note,
            response_action_executed=False,
        )
        return delivery_status(app.state.deliveries.get(idempotency_key))

    @app.post("/v1/webhooks/wazuh", response_model=WebhookReceipt, status_code=status.HTTP_202_ACCEPTED)
    async def receive_wazuh_alert(
        alert: WazuhAlert,
        x_soc_lab_token: str = Header(default=""),
        idempotency_key: str = Header(min_length=8, max_length=128),
    ) -> WebhookReceipt:
        expected = config.webhook_token.get_secret_value()
        if not hmac.compare_digest(x_soc_lab_token, expected):
            app.state.metrics.inc(
                "soc_webhook_rejections_total", {"reason": "authentication"}
            )
            app.state.audit.write("webhook.authentication_failed", source="wazuh")
            raise HTTPException(status_code=401, detail="invalid webhook authentication")

        canonical = alert.model_dump_json(exclude_none=True).encode("utf-8")
        trace_id = hashlib.sha256(
            f"{idempotency_key}:{alert.id}".encode("utf-8")
        ).hexdigest()[:32]
        try:
            created = app.state.deliveries.enqueue(
                idempotency_key, canonical, alert.id, trace_id
            )
        except IdempotencyConflict as exc:
            app.state.metrics.inc(
                "soc_webhook_rejections_total", {"reason": "idempotency_conflict"}
            )
            app.state.audit.write("webhook.idempotency_conflict", alert_id=alert.id)
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        receipt_status = "accepted" if created else "duplicate"
        app.state.metrics.inc("soc_alerts_received_total", {"disposition": receipt_status})
        if not created:
            app.state.metrics.inc("soc_duplicate_suppression_total", {"layer": "delivery"})
        app.state.audit.write(
            "webhook.received",
            alert_id=alert.id,
            rule_id=alert.rule.id,
            agent=alert.agent.name,
            disposition=receipt_status,
            response_action_executed=False,
        )
        logger.info("alert %s disposition=%s", alert.id, receipt_status)

        record = app.state.deliveries.get(idempotency_key)
        result = record.result or {}
        return WebhookReceipt(
            status=receipt_status,
            alert_id=alert.id,
            idempotency_key=idempotency_key,
            processing_status=record.status,
            status_url=f"/v1/deliveries/{idempotency_key}",
            trace_id=trace_id,
            incident_id=result.get("incident_id"),
            incident_disposition=result.get("incident_disposition"),
            indicator_count=len(result.get("indicators", [])) if result else None,
            score=result.get("score"),
            severity=result.get("severity"),
            summary=result.get("summary"),
            enrichments=result.get("indicators"),
            shuffle_execution_id=result.get("shuffle_execution_id"),
        )

    return app
