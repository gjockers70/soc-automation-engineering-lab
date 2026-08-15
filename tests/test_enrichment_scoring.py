import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from soc_integration.enrichment import Indicator, extract_indicators, normalize_misp
from soc_integration.scoring import score_alert


class EnrichmentTests(unittest.TestCase):
    def test_nested_iocs_are_validated_normalized_and_deduplicated(self):
        indicators = extract_indicators({
            "network": {"srcip": "198.51.100.44", "domain": "Suspicious-Login.TEST"},
            "repeat": {"source_ip": "198.51.100.44"},
            "bad": {"dstip": "999.1.1.1", "hash": "not-a-hash"},
        })
        self.assertEqual(
            [(item.type, item.value) for item in indicators],
            [("domain", "suspicious-login.test"), ("ip", "198.51.100.44")],
        )

    def test_misp_metadata_is_normalized(self):
        indicator = Indicator(value="198.51.100.44", type="ip")
        result = normalize_misp(indicator, {"response": {"Attribute": [{
            "event_id": "7", "uuid": "synthetic-uuid",
            "comment": 'soc_lab_metadata={"reputation":"suspicious","confidence":75,"tags":["soc-lab:synthetic"]}',
            "Tag": [{"name": "tlp:clear"}],
        }]}})
        self.assertEqual(result.reputation, "suspicious")
        self.assertEqual(result.confidence, 75)
        self.assertEqual(result.tags, ["soc-lab:synthetic", "tlp:clear"])
        self.assertEqual(result.sources[0]["name"], "local-misp")

    def test_unknown_indicator_stays_unknown(self):
        result = normalize_misp(Indicator(value="unknown.test", type="domain"), {"response": {"Attribute": []}})
        self.assertEqual((result.reputation, result.confidence, result.sources), ("unknown", 0, []))

    def test_scoring_is_deterministic_and_explainable(self):
        enrichment = normalize_misp(Indicator(value="198.51.100.44", type="ip"), {"response": {"Attribute": [{
            "event_id": "7", "uuid": "synthetic-uuid",
            "comment": 'soc_lab_metadata={"reputation":"suspicious","confidence":75,"tags":[]}',
        }]}})
        result = score_alert(7, [enrichment])
        self.assertEqual((result.score, result.severity), (53, "medium"))
        self.assertEqual(len(result.factors), 3)


if __name__ == "__main__":
    unittest.main()
