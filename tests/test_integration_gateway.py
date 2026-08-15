import asyncio
import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from soc_integration.app import create_app
from soc_integration.config import Settings
from soc_integration.idempotency import IdempotencyStore
from soc_integration.integrations.base import IntegrationError, RetryingClient


def alert(alert_id: str = "phase8-001") -> dict:
    return {
        "id": alert_id,
        "timestamp": "2026-08-13T15:30:00-05:00",
        "rule": {"id": "100001", "level": 7, "description": "Synthetic failed login"},
        "agent": {"id": "001", "name": "ubuntu-web-01"},
        "data": {"srcip": "198.51.100.44"},
        "synthetic": True,
    }


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.token = "t" * 32
        settings = Settings(
            webhook_token=SecretStr(self.token),
            audit_path=root / "audit.jsonl",
            idempotency_db=root / "idempotency.sqlite3",
        )
        self.app = create_app(settings)
        self.client = TestClient(self.app)
        self.headers = {"X-SOC-LAB-TOKEN": self.token, "Idempotency-Key": "phase8-key-001"}

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def test_authenticated_webhook_is_accepted_then_suppressed(self):
        first = self.client.post("/v1/webhooks/wazuh", json=alert(), headers=self.headers)
        second = self.client.post("/v1/webhooks/wazuh", json=alert(), headers=self.headers)
        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.json()["status"], "accepted")
        self.assertEqual(second.status_code, 202)
        self.assertEqual(second.json()["status"], "duplicate")
        self.assertFalse(second.json()["response_action_executed"])

    def test_missing_authentication_is_rejected_and_audited(self):
        response = self.client.post(
            "/v1/webhooks/wazuh", json=alert(), headers={"Idempotency-Key": "phase8-key-002"}
        )
        self.assertEqual(response.status_code, 401)
        records = [json.loads(line) for line in self.app.state.settings.audit_path.read_text().splitlines()]
        self.assertEqual(records[-1]["event"], "webhook.authentication_failed")

    def test_malformed_webhook_is_rejected(self):
        payload = alert()
        payload["synthetic"] = False
        response = self.client.post("/v1/webhooks/wazuh", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)

    def test_reused_key_with_different_payload_conflicts(self):
        self.client.post("/v1/webhooks/wazuh", json=alert("phase8-001"), headers=self.headers)
        response = self.client.post("/v1/webhooks/wazuh", json=alert("phase8-002"), headers=self.headers)
        self.assertEqual(response.status_code, 409)


class IdempotencyTests(unittest.TestCase):
    def test_concurrent_duplicate_is_suppressed(self):
        with tempfile.TemporaryDirectory() as temp:
            store = IdempotencyStore(Path(temp) / "idempotency.sqlite3")
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(
                    executor.map(
                        lambda _: store.record("concurrent-key", b"same-payload", "alert-1"), range(2)
                    )
                )
        self.assertEqual(sorted(results), [False, True])


class RetryTests(unittest.TestCase):
    def test_rate_limit_is_retried(self):
        calls = 0

        def handler(_: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(429, headers={"Retry-After": "0"})
            return httpx.Response(200, json={"ok": True})

        client = RetryingClient(
            "test", "https://service.test", timeout=1, attempts=2, backoff=0,
            verify=True, transport=httpx.MockTransport(handler)
        )

        async def run() -> None:
            response = await client.request("GET", "/health")
            self.assertEqual(response.status_code, 200)
            await client.close()

        asyncio.run(run())
        self.assertEqual(calls, 2)

    def test_authentication_failure_is_classified(self):
        client = RetryingClient(
            "test", "https://service.test", timeout=1, attempts=2, backoff=0,
            verify=True, transport=httpx.MockTransport(lambda _: httpx.Response(401))
        )

        async def run() -> None:
            with self.assertRaisesRegex(IntegrationError, "authentication"):
                await client.request("GET", "/health")
            await client.close()

        asyncio.run(run())

    def test_timeout_is_retried_then_classified(self):
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            raise httpx.ReadTimeout("synthetic timeout", request=request)

        client = RetryingClient(
            "test", "https://service.test", timeout=1, attempts=2, backoff=0,
            verify=True, transport=httpx.MockTransport(handler)
        )

        async def run() -> None:
            with self.assertRaisesRegex(IntegrationError, "timeout"):
                await client.request("GET", "/health")
            await client.close()

        asyncio.run(run())
        self.assertEqual(calls, 2)


if __name__ == "__main__":
    unittest.main()
