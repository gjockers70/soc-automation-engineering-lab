import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from soc_integration.audit import AuditWriter
from soc_integration.incidents import IncidentStore
from soc_integration.models import WazuhAlert
from soc_integration.pipeline import AlertPipeline


def alert(alert_id: str, timestamp: str = "2026-08-13T15:30:00-05:00") -> WazuhAlert:
    return WazuhAlert.model_validate({
        "id": alert_id, "timestamp": timestamp,
        "rule": {"id": "100001", "level": 7, "description": "Synthetic failed login"},
        "agent": {"id": "001", "name": "ubuntu-web-01"},
        "data": {"srcip": "198.51.100.44"}, "synthetic": True,
    })


class FakeMisp:
    async def search(self, value, indicator_types):
        return {"response": {"Attribute": [{
            "event_id": "7", "uuid": "synthetic-uuid",
            "comment": 'soc_lab_metadata={"reputation":"suspicious","confidence":75,"tags":["soc-lab:synthetic"]}',
        }]}}


class FakeTheHive:
    def __init__(self):
        self.cases = []
        self.observables = []

    async def find_case_by_tag(self, tag):
        return next((case for case in self.cases if tag in case["tags"]), None)

    async def create_case(self, payload):
        case = {**payload, "_id": f"case-{len(self.cases) + 1}"}
        self.cases.append(case)
        return case

    async def add_observable(self, case_id, payload):
        self.observables.append((case_id, payload))
        return payload


class PipelineTests(unittest.TestCase):
    def test_distinct_alert_deliveries_reuse_one_incident(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            thehive = FakeTheHive()
            pipeline = AlertPipeline(FakeMisp(), thehive, IncidentStore(root / "state.sqlite3"), AuditWriter(root / "audit.jsonl"))

            first = asyncio.run(pipeline.process(alert("phase9-001")))
            second = asyncio.run(pipeline.process(alert("phase9-002")))

            self.assertEqual(first.incident_disposition, "created")
            self.assertEqual(second.incident_disposition, "reused")
            self.assertEqual(first.incident_id, second.incident_id)
            self.assertEqual(len(thehive.cases), 1)
            self.assertEqual(len(thehive.observables), 1)
            self.assertIn("approval:required", thehive.cases[0]["tags"])
            self.assertIn("no response action executed", thehive.cases[0]["description"].lower())
            self.assertEqual((first.score.score, first.score.severity), (53, "medium"))
            later = asyncio.run(pipeline.process(alert("phase9-003", "2026-08-13T16:31:00-05:00")))
            self.assertEqual(later.incident_disposition, "created")
            self.assertEqual(len(thehive.cases), 2)



if __name__ == "__main__":
    unittest.main()
