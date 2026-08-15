#!/usr/bin/env python3
"""Validate the Phase 4 detection-as-code structure."""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
REQUIRED_SIGMA_FIELDS = {
    "title",
    "id",
    "status",
    "description",
    "author",
    "date",
    "logsource",
    "detection",
    "falsepositives",
    "level",
    "tags",
}
ALLOWED_LEVELS = {"informational", "low", "medium", "high", "critical"}
EXPECTED_IDS = {"SOC1001", "SOC1002", "SOC1003"}


def validate_sigma() -> int:
    rule_ids: set[uuid.UUID] = set()
    files = sorted((ROOT / "sigma").glob("*.yml"))
    if not files:
        raise ValueError("no Sigma rules found")

    for path in files:
        rule = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(rule, dict):
            raise ValueError(f"{path}: rule must be a mapping")
        missing = REQUIRED_SIGMA_FIELDS - rule.keys()
        if missing:
            raise ValueError(f"{path}: missing fields {sorted(missing)}")
        parsed_id = uuid.UUID(str(rule["id"]))
        if parsed_id in rule_ids:
            raise ValueError(f"{path}: duplicate Sigma id {parsed_id}")
        rule_ids.add(parsed_id)
        if rule["status"] != "test":
            raise ValueError(f"{path}: Phase 4 rules must remain status test")
        if rule["level"] not in ALLOWED_LEVELS:
            raise ValueError(f"{path}: invalid level {rule['level']}")
        if not isinstance(rule["date"], (dt.date, str)):
            raise ValueError(f"{path}: invalid date")
        if not isinstance(rule["logsource"], dict) or not rule["logsource"]:
            raise ValueError(f"{path}: logsource must be a non-empty mapping")
        detection = rule["detection"]
        if not isinstance(detection, dict) or not isinstance(detection.get("condition"), str):
            raise ValueError(f"{path}: detection condition is required")
        identifiers = {key for key in detection if key != "condition" and not key.startswith("_")}
        words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", detection["condition"]))
        operators = {"and", "or", "not", "of", "them", "all"}
        unknown = words - identifiers - operators
        if unknown:
            raise ValueError(f"{path}: condition has unknown identifiers {sorted(unknown)}")
        if not isinstance(rule["falsepositives"], list) or not rule["falsepositives"]:
            raise ValueError(f"{path}: false positives must be documented")
    return len(files)


def validate_wazuh() -> int:
    root = ET.parse(ROOT / "wazuh" / "phase4_rules.xml").getroot()
    ids: set[int] = set()
    for rule in root.findall("rule"):
        rule_id = int(rule.attrib["id"])
        if not 100000 <= rule_id <= 120000:
            raise ValueError(f"Wazuh custom rule id {rule_id} is outside the reserved range")
        if rule_id in ids:
            raise ValueError(f"duplicate Wazuh rule id {rule_id}")
        ids.add(rule_id)
        level = int(rule.attrib["level"])
        if not 0 <= level <= 16:
            raise ValueError(f"Wazuh rule {rule_id} has invalid level {level}")
        description = rule.findtext("description", default="")
        if not re.match(r"SOC\d{4}:", description):
            raise ValueError(f"Wazuh rule {rule_id} lacks a detection identifier")
        if rule.find("mitre/id") is None:
            raise ValueError(f"Wazuh rule {rule_id} lacks MITRE mapping")
    if len(ids) != 3:
        raise ValueError(f"expected 3 Wazuh rules, found {len(ids)}")
    return len(ids)


def validate_test_events_and_docs() -> int:
    found: set[str] = set()
    for path in sorted((ROOT / "test-events").glob("*.json")):
        event = json.loads(path.read_text(encoding="utf-8"))
        detection_id = event.get("detection_id")
        if detection_id not in EXPECTED_IDS:
            raise ValueError(f"{path}: unknown detection_id {detection_id}")
        if detection_id in found:
            raise ValueError(f"{path}: duplicate test event for {detection_id}")
        found.add(detection_id)
        if not isinstance(event.get("expected_wazuh_rule"), int):
            raise ValueError(f"{path}: expected_wazuh_rule must be an integer")
    if found != EXPECTED_IDS:
        raise ValueError(f"missing test events for {sorted(EXPECTED_IDS - found)}")
    for detection_id in EXPECTED_IDS:
        if not (ROOT / "documentation" / f"{detection_id}.md").is_file():
            raise ValueError(f"missing documentation for {detection_id}")
    return len(found)


def main() -> None:
    sigma_count = validate_sigma()
    wazuh_count = validate_wazuh()
    event_count = validate_test_events_and_docs()
    print(f"sigma_rules={sigma_count}")
    print(f"wazuh_rules={wazuh_count}")
    print(f"test_events={event_count}")
    print("detection_repository_validation=pass")


if __name__ == "__main__":
    main()
