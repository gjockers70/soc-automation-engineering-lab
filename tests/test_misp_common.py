from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "threat-intel" / "scripts" / "misp_common.py"
SPEC = importlib.util.spec_from_file_location("misp_common", MODULE_PATH)
assert SPEC and SPEC.loader
MISP_COMMON = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MISP_COMMON
SPEC.loader.exec_module(MISP_COMMON)


class IndicatorValidationTests(unittest.TestCase):
    def test_supported_indicators(self) -> None:
        self.assertEqual(MISP_COMMON.validate_indicator("198.51.100.44", "ip"), "198.51.100.44")
        self.assertEqual(
            MISP_COMMON.validate_indicator("suspicious-login.test", "domain"),
            "suspicious-login.test",
        )
        self.assertEqual(
            MISP_COMMON.validate_indicator("https://payload.test/download", "url"),
            "https://payload.test/download",
        )

    def test_malformed_indicator_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MISP_COMMON.validate_indicator("not a domain", "domain")
        with self.assertRaises(ValueError):
            MISP_COMMON.validate_indicator("abcd", "hash")

    def test_hash_type_mapping(self) -> None:
        value = "a" * 64
        self.assertEqual(MISP_COMMON.misp_types("hash", value), ["sha256"])


class NormalizationTests(unittest.TestCase):
    def test_known_result_is_normalized(self) -> None:
        attributes = [{"event_id": "12", "uuid": "attribute-uuid", "Tag": []}]
        fixture = {"reputation": "suspicious", "confidence": 75, "tags": ["tlp:clear"]}
        result = MISP_COMMON.normalize_result("198.51.100.44", "ip", attributes, fixture)
        self.assertEqual(result["reputation"], "suspicious")
        self.assertEqual(result["confidence"], 75)
        self.assertEqual(result["sources"][0]["name"], "local-misp")
        self.assertEqual(result["tags"], ["tlp:clear"])

    def test_unknown_result_has_no_claimed_reputation(self) -> None:
        result = MISP_COMMON.normalize_result("unknown.test", "domain", [], None)
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["reputation"], "unknown")
        self.assertEqual(result["confidence"], 0)


if __name__ == "__main__":
    unittest.main()
