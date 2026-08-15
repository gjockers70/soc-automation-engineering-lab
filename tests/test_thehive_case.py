import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "incidents" / "scripts" / "seed_case.py"
SPEC = importlib.util.spec_from_file_location("seed_case", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TheHiveFixtureTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "incidents" / "fixtures" / "phase6-synthetic-case.json"
        self.fixture = json.loads(path.read_text(encoding="utf-8"))

    def test_case_payload_has_required_fields(self):
        payload = MODULE.build_case_payload(self.fixture)
        self.assertEqual(payload["severity"], 2)
        self.assertIn("approval:required", payload["tags"])

    def test_case_uses_only_reserved_synthetic_indicators(self):
        values = [item for obs in self.fixture["observables"] for item in obs["data"]]
        self.assertIn("198.51.100.44", values)
        self.assertTrue(any(value.endswith(".test") for value in values))

    def test_case_keeps_response_approval_gated(self):
        review = next(task for task in self.fixture["tasks"] if "containment" in task["title"].lower())
        self.assertEqual(review["status"], "Waiting")
        self.assertIn("Do not contain automatically", review["description"])

    def test_result_ids_accepts_thehive_list_response(self):
        self.assertEqual(MODULE.result_ids([{"_id": "~1"}, {"_id": "~2"}]), ["~1", "~2"])


if __name__ == "__main__":
    unittest.main()
