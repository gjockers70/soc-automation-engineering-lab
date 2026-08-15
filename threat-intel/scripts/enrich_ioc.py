#!/usr/bin/env python3
"""Query local MISP and emit one normalized IOC enrichment record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from misp_common import (
    client_from_env_file,
    extract_attributes,
    misp_types,
    normalize_result,
    validate_indicator,
)


def load_fixture(path: Path, indicator: str, indicator_type: str) -> dict[str, Any] | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data.get("indicators", []):
        if item.get("indicator") == indicator and item.get("type") == indicator_type:
            return item
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("indicator")
    parser.add_argument("--type", required=True, choices=["ip", "domain", "url", "hash"])
    parser.add_argument(
        "--env-file", type=Path, default=Path("/opt/soc-lab/secrets/misp.env")
    )
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    try:
        indicator = validate_indicator(args.indicator, args.type)
        fixture = load_fixture(args.fixture, indicator, args.type)
        client = client_from_env_file(args.env_file, args.timeout)
        attributes: list[dict[str, Any]] = []
        for misp_type in misp_types(args.type, indicator):
            response = client.request(
                "POST",
                "attributes/restSearch",
                {
                    "returnFormat": "json",
                    "value": indicator,
                    "type": misp_type,
                    "includeEventTags": True,
                },
            )
            attributes.extend(extract_attributes(response))
        print(json.dumps(normalize_result(indicator, args.type, attributes, fixture), indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"enrichment_error={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
