from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from soc_integration.integrations.base import IntegrationError, RetryingClient
from soc_integration.integrations.misp import MispClient
from soc_integration.integrations.shuffle import ShuffleClient
from soc_integration.integrations.thehive import TheHiveClient
from soc_integration.integrations.wazuh import WazuhClient

COMMON = {
    "timeout": 1,
    "attempts": 3,
    "backoff": 0,
    "verify": True,
}


def test_misp_search_uses_authenticated_structured_request() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["authorization"] = request.headers.get("Authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"response": {"Attribute": []}})

    async def exercise() -> dict:
        client = MispClient(
            "https://misp.test",
            "synthetic-misp-key",
            **COMMON,
            transport=httpx.MockTransport(handler),
        )
        try:
            return await client.search("198.51.100.44", ["ip-src", "ip-dst"])
        finally:
            await client.close()

    assert asyncio.run(exercise()) == {"response": {"Attribute": []}}
    assert seen == {
        "method": "POST",
        "path": "/attributes/restSearch",
        "authorization": "synthetic-misp-key",
        "body": {
            "returnFormat": "json",
            "value": "198.51.100.44",
            "type": ["ip-src", "ip-dst"],
        },
    }


def test_wazuh_health_exchanges_basic_auth_for_bearer_token() -> None:
    requests: list[tuple[str, str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(
            (request.method, request.url.path, request.headers.get("Authorization", ""))
        )
        if request.url.path.endswith("/security/user/authenticate"):
            return httpx.Response(200, json={"data": {"token": "synthetic-jwt"}})
        return httpx.Response(200, json={"data": {"affected_items": []}})

    async def exercise() -> None:
        client = WazuhClient(
            "https://wazuh.test",
            "api-user",
            "synthetic-password",
            **COMMON,
            transport=httpx.MockTransport(handler),
        )
        try:
            await client.health()
        finally:
            await client.close()

    asyncio.run(exercise())
    assert requests[0][0:2] == ("POST", "/security/user/authenticate")
    assert requests[0][2].startswith("Basic ")
    assert requests[1] == ("GET", "/manager/status", "Bearer synthetic-jwt")


def test_shuffle_response_shapes_are_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer synthetic-shuffle-key"
        if request.url.path == "/api/v1/workflows":
            return httpx.Response(200, json={"workflows": [{"id": "pb-1"}]})
        return httpx.Response(200, json={"executions": [{"status": "FINISHED"}]})

    async def exercise() -> tuple[list[dict], list[dict]]:
        client = ShuffleClient(
            "https://shuffle.test",
            "synthetic-shuffle-key",
            **COMMON,
            transport=httpx.MockTransport(handler),
        )
        try:
            return await client.workflows(), await client.executions("pb-1")
        finally:
            await client.close()

    assert asyncio.run(exercise()) == (
        [{"id": "pb-1"}],
        [{"status": "FINISHED"}],
    )


def test_thehive_case_observable_and_comment_contracts() -> None:
    seen: list[tuple[str, str, dict]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else {}
        seen.append((request.method, request.url.path, body))
        assert request.headers["X-Organisation"] == "SOC-LAB"
        assert request.headers["Authorization"].startswith("Basic ")
        if request.url.path == "/api/v1/query":
            return httpx.Response(200, json=[{"_id": "case-14", "tags": ["dedup:14"]}])
        return httpx.Response(201, json={"_id": "case-14"})

    async def exercise() -> None:
        client = TheHiveClient(
            "https://thehive.test",
            "SOC-LAB",
            "automation",
            "synthetic-password",
            **COMMON,
            transport=httpx.MockTransport(handler),
        )
        try:
            assert (await client.find_case_by_tag("dedup:14"))["_id"] == "case-14"
            await client.create_case({"title": "Synthetic case"})
            await client.add_observable("case-14", {"dataType": "domain", "data": ["phase14.test"]})
            await client.add_comment("case-14", "Synthetic analyst note")
        finally:
            await client.close()

    asyncio.run(exercise())
    assert [item[1] for item in seen] == [
        "/api/v1/query",
        "/api/v1/case",
        "/api/v1/case/case-14/observable",
        "/api/v1/case/case-14/comment",
    ]
    assert seen[-1][2] == {"message": "Synthetic analyst note"}


def test_retry_after_is_bounded_and_recovery_is_returned() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "600"})
        return httpx.Response(200, json={"ok": True})

    async def exercise() -> httpx.Response:
        client = RetryingClient(
            "test",
            "https://service.test",
            **COMMON,
            transport=httpx.MockTransport(handler),
        )
        try:
            with patch(
                "soc_integration.integrations.base.asyncio.sleep",
                new_callable=AsyncMock,
            ) as sleeper:
                response = await client.request("GET", "/health")
                sleeper.assert_awaited_once_with(5.0)
                return response
        finally:
            await client.close()

    assert asyncio.run(exercise()).status_code == 200
    assert calls == 2


def test_non_retryable_http_error_fails_once() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(400)

    async def exercise() -> None:
        client = RetryingClient(
            "test",
            "https://service.test",
            **COMMON,
            transport=httpx.MockTransport(handler),
        )
        try:
            with pytest.raises(IntegrationError) as raised:
                await client.request("GET", "/health")
            assert raised.value.category == "http_error"
            assert raised.value.status_code == 400
        finally:
            await client.close()

    asyncio.run(exercise())
    assert calls == 1


def test_request_error_retries_then_reports_unavailable_without_url() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("synthetic connection refusal", request=request)

    async def exercise() -> IntegrationError:
        client = RetryingClient(
            "misp",
            "https://secret-hostname.test",
            **{**COMMON, "attempts": 2},
            transport=httpx.MockTransport(handler),
        )
        try:
            with pytest.raises(IntegrationError) as raised:
                await client.request("GET", "/health")
            return raised.value
        finally:
            await client.close()

    error = asyncio.run(exercise())
    assert error.category == "unavailable"
    assert calls == 2
    assert "secret-hostname" not in str(error)


def test_retryable_status_exhaustion_is_classified_without_extra_attempt() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503)

    async def exercise() -> IntegrationError:
        client = RetryingClient(
            "thehive",
            "https://thehive.test",
            **{**COMMON, "attempts": 2},
            transport=httpx.MockTransport(handler),
        )
        try:
            with pytest.raises(IntegrationError) as raised:
                await client.request("GET", "/health")
            return raised.value
        finally:
            await client.close()

    error = asyncio.run(exercise())
    assert (error.category, error.status_code, calls) == ("http_error", 503, 2)
