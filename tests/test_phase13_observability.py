import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from soc_integration.app import create_app
from soc_integration.config import Settings
from soc_integration.metrics import MetricsRegistry
from soc_integration.observability import collect_playbook_metrics


class MetricsRegistryTests(unittest.TestCase):
    def test_counter_gauge_summary_and_label_escaping_render(self):
        registry = MetricsRegistry()
        registry.inc("soc_alerts_received_total", {"disposition": 'accepted"test'})
        registry.set("soc_dependency_healthy", 1, {"dependency": "misp"})
        registry.observe("soc_workflow_duration_seconds", 0.25)
        rendered = registry.render()
        expected = 'soc_alerts_received_total{disposition="accepted' + chr(92) + '"test"} 1'
        self.assertIn(expected, rendered)
        rendered = rendered.replace(chr(92), "")
        self.assertIn('soc_alerts_received_total{disposition="accepted\"test"} 1', rendered)
        self.assertIn('soc_dependency_healthy{dependency="misp"} 1', rendered)
        self.assertIn("soc_workflow_duration_seconds_count 1", rendered)
        self.assertIn("soc_workflow_duration_seconds_sum 0.25", rendered)

    def test_counter_cannot_decrease_or_use_unknown_labels(self):
        registry = MetricsRegistry()
        with self.assertRaisesRegex(ValueError, "non-negative"):
            registry.inc("soc_alerts_processed_total", amount=-1)
        with self.assertRaisesRegex(ValueError, "label"):
            registry.inc("soc_alerts_processed_total", {"bad-label": "value"})


class FakeShuffle:
    async def workflows(self):
        return [
            {"id": "one", "name": "SOC-LAB PB1 - Suspicious Login"},
            {"id": "ignored", "name": "Unrelated workflow"},
        ]

    async def executions(self, workflow_id):
        self.last_workflow = workflow_id
        return [
            {"status": "FINISHED", "started_at": 1_000, "completed_at": 1_004},
            {"status": "FAILED", "started_at": 2_000_000_000_000, "completed_at": 2_000_000_005_000},
            {"status": "EXECUTING", "started_at": 3_000},
        ]


class ShuffleCollectorTests(unittest.TestCase):
    def test_execution_statuses_and_seconds_are_aggregated(self):
        client = FakeShuffle()
        result = asyncio.run(collect_playbook_metrics(client))
        self.assertEqual((result.success, result.failure, result.running), (1, 1, 1))
        self.assertEqual((result.duration_count, result.duration_sum), (2, 9.0))
        self.assertEqual(client.last_workflow, "one")


class MetricsEndpointTests(unittest.TestCase):
    def test_gateway_exposes_delivery_and_rejection_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            token = "m" * 32
            app = create_app(
                Settings(
                    webhook_token=SecretStr(token),
                    audit_path=root / "audit.jsonl",
                    idempotency_db=root / "state.sqlite3",
                )
            )
            payload = {
                "id": "phase13-001",
                "timestamp": "2026-08-14T00:00:00Z",
                "rule": {"id": "130001", "level": 7, "description": "Synthetic metric alert"},
                "agent": {"id": "001", "name": "ubuntu-web-01"},
                "data": {"srcip": "198.51.100.44"},
                "synthetic": True,
            }
            headers = {"X-SOC-LAB-TOKEN": token, "Idempotency-Key": "phase13-metric-key"}
            with TestClient(app) as client:
                self.assertEqual(client.post("/v1/webhooks/wazuh", json=payload, headers=headers).status_code, 202)
                self.assertEqual(client.post("/v1/webhooks/wazuh", json=payload, headers=headers).status_code, 202)
                self.assertEqual(
                    client.post(
                        "/v1/webhooks/wazuh",
                        json={"synthetic": True},
                        headers={**headers, "Idempotency-Key": "phase13-invalid"},
                    ).status_code,
                    422,
                )
                response = client.get("/metrics")
            self.assertEqual(response.status_code, 200)
            self.assertIn('soc_alerts_received_total{disposition="accepted"} 1', response.text)
            self.assertIn('soc_alerts_received_total{disposition="duplicate"} 1', response.text)
            self.assertIn('soc_duplicate_suppression_total{layer="delivery"} 1', response.text)
            self.assertIn('soc_webhook_rejections_total{reason="schema"} 1', response.text)
            self.assertNotIn(token, response.text)


if __name__ == "__main__":
    unittest.main()
