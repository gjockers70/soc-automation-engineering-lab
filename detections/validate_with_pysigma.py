#!/usr/bin/env python3
"""Parse every Sigma rule with the official pySigma library."""

from pathlib import Path

from sigma.collection import SigmaCollection

rules = sorted((Path(__file__).resolve().parent / "sigma").glob("*.yml"))
if not rules:
    raise SystemExit("no Sigma rules found")

for rule in rules:
    SigmaCollection.from_yaml(rule.read_text(encoding="utf-8"))
    print(f"pysigma_parse=pass file={rule.name}")

print(f"pysigma_rules={len(rules)}")
