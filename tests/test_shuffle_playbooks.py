import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "playbooks" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("seed_workflows", SCRIPT_DIR / "seed_workflows.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ShufflePlaybookTests(unittest.TestCase):
    def setUp(self):
        self.specs = json.loads((ROOT / "playbooks" / "fixtures" / "phase7-playbooks.json").read_text(encoding="utf-8"))
        self.inputs = json.loads((ROOT / "playbooks" / "fixtures" / "synthetic-inputs.json").read_text(encoding="utf-8"))
        self.app = {"id": "test-app-id"}

    def test_required_playbooks_and_safe_fallback_are_defined(self):
        self.assertEqual(
            {item["key"] for item in self.specs},
            {
                "suspicious-login",
                "suspicious-file",
                "suspicious-domain",
                "account-activity",
                "security-alert",
            },
        )

    def test_workflow_uses_authenticated_webhook_and_no_response_action(self):
        payload = MODULE.workflow_payload(self.specs[0], self.app, "test-token")
        auth = next(item for item in payload["triggers"][0]["parameters"] if item["name"] == "auth_headers")
        self.assertEqual(auth["value"], "X-SOC-LAB-TOKEN=test-token")
        self.assertEqual(payload["actions"][0]["name"], "repeat_back_to_me")
        self.assertEqual(len(payload["actions"]), 2)
        self.assertEqual(len(payload["branches"]), 2)
        self.assertNotIn("disable", json.dumps(payload["actions"]).lower())

    def test_all_inputs_are_explicitly_synthetic(self):
        self.assertTrue(all(item.get("synthetic") is True for item in self.inputs.values()))

    def test_account_playbook_requires_approval(self):
        self.assertTrue(self.inputs["account-activity"]["approval_required"])
        self.assertIn("approval", " ".join(self.specs[3]["handoff_steps"]).lower())
        self.assertTrue(self.specs[3]["approval_required"])


if __name__ == "__main__":
    unittest.main()
