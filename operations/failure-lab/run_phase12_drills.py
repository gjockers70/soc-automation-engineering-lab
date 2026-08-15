#!/usr/bin/env python3
"""Run safe Phase 12 failure drills against synthetic data and local substitutes."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

import httpx

from soc_integration.diagnostics import classify_endpoint_health
from soc_integration.enrichment import extract_indicators, invalid_indicator_candidates
from soc_integration.integrations.base import IntegrationError, RetryingClient
from soc_integration.logging import configure_logging


def result(scenario_id: str, signal: str, recovery: str) -> dict[str, object]:
    return {
        "id": scenario_id,
        "status": "passed",
        "observed_signal": signal,
        "recovery": recovery,
        "response_action_executed": False,
    }


async def classified_client_failure(
    service: str,
    handler: Callable[[httpx.Request], httpx.Response],
    expected_category: str,
) -> tuple[str, int]:
    calls = 0

    def counted(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return handler(request)

    client = RetryingClient(
        service,
        "https://synthetic.service.test",
        timeout=0.1,
        attempts=3,
        backoff=0,
        verify=True,
        transport=httpx.MockTransport(counted),
    )
    try:
        await client.request("GET", "/health")
    except IntegrationError as exc:
        if exc.category != expected_category:
            raise AssertionError(f"expected {expected_category}, received {exc.category}") from exc
        return exc.category, calls
    finally:
        await client.close()
    raise AssertionError("synthetic dependency failure unexpectedly succeeded")


async def mock_drills() -> list[dict[str, object]]:
    def unavailable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("synthetic connection refusal", request=request)

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    unavailable_category, unavailable_calls = await classified_client_failure(
        "misp", unavailable, "unavailable"
    )
    timeout_category, timeout_calls = await classified_client_failure("misp", timeout, "timeout")
    thehive_category, thehive_calls = await classified_client_failure(
        "thehive", unavailable, "unavailable"
    )
    auth_category, auth_calls = await classified_client_failure(
        "misp", lambda _: httpx.Response(401), "authentication"
    )

    observed = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)
    endpoint = classify_endpoint_health(
        observed - timedelta(minutes=10), observed_at=observed
    )
    if endpoint.status != "disconnected":
        raise AssertionError("expired synthetic heartbeat was not classified as disconnected")

    malformed = {"srcip": "999.1.1.1", "domain": "not a domain", "sha256": "not-a-hash"}
    invalid = invalid_indicator_candidates(malformed)
    if extract_indicators(malformed) or len(invalid) != 3:
        raise AssertionError("malformed IOC validation did not isolate all candidates")

    return [
        result("P12-F01", f"misp:{unavailable_category}; attempts={unavailable_calls}", "retry after service health recovers"),
        result("P12-F03", f"misp:{timeout_category}; attempts={timeout_calls}", "retry after latency returns below timeout"),
        result("P12-F05", f"thehive:{thehive_category}; attempts={thehive_calls}", "retry case handoff after readiness recovers"),
        result("P12-F06", f"endpoint:{endpoint.status}; age_seconds={endpoint.age_seconds}", "verify route and restart the lab collector if approved"),
        result("P12-F07", f"invalid_ioc_candidates={len(invalid)}; valid_iocs=0", "correct or discard the malformed indicator"),
        result("P12-F08", f"misp:{auth_category}; attempts={auth_calls}", "restore the protected service credential and recheck readiness"),
    ]


def live_gateway_drills(base_url: str, token: str) -> list[dict[str, object]]:
    if len(token) < 32:
        raise ValueError("SOC_WEBHOOK_TOKEN is unavailable")
    run_id = f"phase12-{uuid4()}"
    alert = {
        "id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rule": {"id": "120001", "level": 7, "description": "Synthetic Phase 12 failed login"},
        "agent": {"id": "001", "name": "ubuntu-web-01"},
        "data": {"srcip": "198.51.100.44"},
        "synthetic": True,
    }
    with httpx.Client(base_url=base_url, timeout=15, verify=False) as client:
        malformed = client.post(
            "/v1/webhooks/wazuh",
            headers={"X-SOC-LAB-TOKEN": token, "Idempotency-Key": f"{run_id}-malformed"},
            json={"synthetic": True},
        )
        if malformed.status_code != 422:
            raise AssertionError(f"malformed webhook returned HTTP {malformed.status_code}")

        headers = {"X-SOC-LAB-TOKEN": token, "Idempotency-Key": f"{run_id}-duplicate"}
        first = client.post("/v1/webhooks/wazuh", headers=headers, json=alert)
        second = client.post("/v1/webhooks/wazuh", headers=headers, json=alert)
        if first.status_code != 202 or first.json().get("status") != "accepted":
            raise AssertionError("first synthetic delivery was not accepted")
        if second.status_code != 202 or second.json().get("status") != "duplicate":
            raise AssertionError("duplicate synthetic delivery was not suppressed")
        if first.json().get("response_action_executed") or second.json().get("response_action_executed"):
            raise AssertionError("failure drill crossed the response boundary")

    return [
        result("P12-F02", "malformed_webhook=http_422", "correct the producer schema before replay"),
        result("P12-F04", "duplicate_delivery=suppressed", "retain the original receipt and close the replay"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://10.77.30.10:8010")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    configure_logging()

    scenarios = asyncio.run(mock_drills())
    if not args.offline:
        scenarios.extend(live_gateway_drills(args.base_url, os.getenv("SOC_WEBHOOK_TOKEN", "")))
    scenarios.sort(key=lambda item: str(item["id"]))
    report = {
        "phase": 12,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "isolated owned SOC lab; synthetic data only",
        "summary": {"passed": len(scenarios), "failed": 0},
        "scenarios": scenarios,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
