#!/usr/bin/env python3
"""Idempotently seed MISP with isolated synthetic indicators."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from misp_common import MispClient, client_from_env_file, extract_attributes


def event_id_from_response(response: Any) -> str | None:
    candidates: list[Any] = response if isinstance(response, list) else [response]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        nested = candidate.get("Event", candidate)
        if isinstance(nested, dict) and nested.get("id"):
            return str(nested["id"])
        response_value = candidate.get("response")
        if isinstance(response_value, list):
            found = event_id_from_response(response_value)
            if found:
                return found
        if isinstance(response_value, dict):
            found = event_id_from_response(response_value)
            if found:
                return found
    return None


def find_event(client: MispClient, info: str) -> str | None:
    response = client.request(
        "POST", "events/restSearch", {"returnFormat": "json", "eventinfo": info}
    )
    return event_id_from_response(response)


def ensure_event(client: MispClient, info: str) -> str:
    existing = find_event(client, info)
    if existing:
        return existing
    created = client.request(
        "POST",
        "events/add",
        {
            "Event": {
                "info": info,
                "distribution": "0",
                "threat_level_id": "2",
                "analysis": "2",
                "published": False,
                "comment": "Local-only synthetic intelligence for defensive workflow validation",
            }
        },
    )
    event_id = event_id_from_response(created)
    if not event_id:
        raise RuntimeError("MISP created an event but did not return its identifier")
    return event_id


def attribute_exists(client: MispClient, value: str, misp_type: str) -> bool:
    response = client.request(
        "POST",
        "attributes/restSearch",
        {"returnFormat": "json", "value": value, "type": misp_type},
    )
    return bool(extract_attributes(response))


def seed(client: MispClient, fixture: dict[str, Any]) -> dict[str, Any]:
    event_id = ensure_event(client, str(fixture["event_info"]))
    created = 0
    existing = 0
    for item in fixture["indicators"]:
        value = str(item["indicator"])
        misp_type = str(item["misp_type"])
        if attribute_exists(client, value, misp_type):
            existing += 1
            continue
        metadata = {
            "reputation": item["reputation"],
            "confidence": item["confidence"],
            "tags": item["tags"],
            "description": item["description"],
        }
        client.request(
            "POST",
            f"attributes/add/{event_id}",
            {
                "Attribute": {
                    "type": misp_type,
                    "category": item["category"],
                    "value": value,
                    "to_ids": False,
                    "distribution": "0",
                    "comment": "soc_lab_metadata=" + json.dumps(metadata, separators=(",", ":")),
                }
            },
        )
        created += 1
    return {"event_id": event_id, "created": created, "existing": existing}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env-file", type=Path, default=Path("/opt/soc-lab/secrets/misp.env")
    )
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    try:
        fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
        result = seed(client_from_env_file(args.env_file, args.timeout), fixture)
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"seed_error={exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
