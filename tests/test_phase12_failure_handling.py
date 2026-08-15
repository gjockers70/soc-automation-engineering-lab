import asyncio
import logging
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "operations" / "failure-lab"))

from run_phase12_drills import mock_drills

from soc_integration.diagnostics import classify_endpoint_health
from soc_integration.enrichment import invalid_indicator_candidates
from soc_integration.integrations.base import IntegrationError, RetryingClient
from soc_integration.logging import configure_logging


class EndpointHealthTests(unittest.TestCase):
    def test_heartbeat_states_are_deterministic(self):
        now = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(classify_endpoint_health(now - timedelta(seconds=30), observed_at=now).status, "connected")
        self.assertEqual(classify_endpoint_health(now - timedelta(seconds=180), observed_at=now).status, "stale")
        self.assertEqual(classify_endpoint_health(now - timedelta(seconds=600), observed_at=now).status, "disconnected")

    def test_invalid_thresholds_and_naive_time_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            classify_endpoint_health(datetime(2026, 8, 14, 12, 0))
        with self.assertRaisesRegex(ValueError, "thresholds"):
            classify_endpoint_health(datetime.now(timezone.utc), stale_after_seconds=300, disconnected_after_seconds=300)


class FailureDrillTests(unittest.TestCase):
    def test_http_client_request_urls_are_not_logged_at_info(self):
        configure_logging()
        self.assertEqual(logging.getLogger("httpx").level, logging.WARNING)
        self.assertEqual(logging.getLogger("httpcore").level, logging.WARNING)

    def test_mock_drills_cover_six_non_mutating_failures(self):
        results = asyncio.run(mock_drills())
        self.assertEqual({item["id"] for item in results}, {"P12-F01", "P12-F03", "P12-F05", "P12-F06", "P12-F07", "P12-F08"})
        self.assertTrue(all(item["response_action_executed"] is False for item in results))

    def test_malformed_ioc_values_are_explainable(self):
        invalid = invalid_indicator_candidates({"srcip": "300.1.1.1", "sha256": "short"})
        self.assertEqual([(item.expected_type, item.reason) for item in invalid], [("hash", "invalid_format"), ("ip", "invalid_format")])

    def test_retry_and_terminal_failure_are_logged_without_url(self):
        calls = 0

        def timeout(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            raise httpx.ReadTimeout("synthetic timeout", request=request)

        client = RetryingClient(
            "misp", "https://secret-host.test", timeout=0.1, attempts=2,
            backoff=0, verify=True, transport=httpx.MockTransport(timeout),
        )

        async def run() -> None:
            with self.assertRaises(IntegrationError):
                await client.request("GET", "/private/path")
            await client.close()

        with self.assertLogs("soc.integration.client", logging.WARNING) as captured:
            asyncio.run(run())
        rendered = " ".join(captured.output)
        self.assertEqual(calls, 2)
        self.assertIn("category=timeout", rendered)
        self.assertNotIn("secret-host", rendered)
        self.assertNotIn("private/path", rendered)


if __name__ == "__main__":
    unittest.main()
