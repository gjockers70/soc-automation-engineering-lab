#!/usr/bin/env python3
"""Verify Phase 4 negative controls against manager alert records."""

from __future__ import annotations

import json
from pathlib import Path

records = [
    json.loads(line)
    for line in Path("/var/ossec/logs/alerts/alerts.json")
    .read_text(encoding="utf-8", errors="replace")
    .splitlines()
]


def rule_id(record: dict[str, object]) -> str:
    return str(record.get("rule", {}).get("id", ""))  # type: ignore[union-attr]


ssh_records = [
    record
    for record in records
    if record.get("data", {}).get("srcip") == "198.51.100.45"  # type: ignore[union-attr]
]
if sum(rule_id(record) == "5710" for record in ssh_records) < 4:
    raise SystemExit("missing below-threshold SSH base events")
if any(rule_id(record) == "100100" for record in ssh_records):
    raise SystemExit("below-threshold SSH events triggered SOC1001")

account_records = [
    record
    for record in records
    if record.get("data", {})
    .get("win", {})
    .get("eventdata", {})
    .get("targetUserName")
    == "soc_phase4_machine$"  # type: ignore[union-attr]
]
if not any(rule_id(record) == "60109" for record in account_records):
    raise SystemExit("missing machine-like account base event")
if any(rule_id(record) == "100102" for record in account_records):
    raise SystemExit("machine-like account triggered SOC1003")

plain_records = [
    record
    for record in records
    if "SOC_PHASE4_NEGATIVE_PLAIN"
    in record.get("data", {})
    .get("win", {})
    .get("eventdata", {})
    .get("commandLine", "")  # type: ignore[union-attr]
]
if not any(rule_id(record) == "67027" for record in plain_records):
    raise SystemExit("missing plain PowerShell base event")
if any(rule_id(record) == "100101" for record in plain_records):
    raise SystemExit("plain PowerShell triggered SOC1002")

print("soc1001_below_threshold=pass")
print("soc1002_plain_powershell=pass")
print("soc1003_machine_account_filter=pass")
print("phase4_negative_validation=pass")
