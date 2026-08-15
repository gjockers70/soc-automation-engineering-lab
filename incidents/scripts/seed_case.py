#!/usr/bin/env python3
"""Idempotently seed one synthetic TheHive case without external dependencies."""

from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def build_case_payload(fixture: dict[str, Any]) -> dict[str, Any]:
    case = fixture["case"]
    required = {"title", "description", "severity", "tlp", "pap", "tags"}
    missing = required.difference(case)
    if missing:
        raise ValueError(f"case fixture missing: {', '.join(sorted(missing))}")
    if "soc-lab:phase6" not in case["tags"]:
        raise ValueError("phase idempotency tag is required")
    return dict(case)


def result_ids(result: Any) -> list[str]:
    items = result if isinstance(result, list) else [result]
    return [item["_id"] for item in items if isinstance(item, dict) and "_id" in item]


class TheHiveClient:
    def __init__(self, base_url: str, organisation: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "X-Organisation": organisation,
        }

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, headers=self.headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"TheHive {method} {path} returned HTTP {exc.code}: {detail}") from exc
        return json.loads(raw) if raw else None


def find_case(client: TheHiveClient, title: str) -> dict[str, Any] | None:
    payload = {"query": [{"_name": "listCase"}]}
    cases = client.request("POST", "/api/v1/query?name=phase6-cases", payload)
    return next((case for case in cases if case.get("title") == title), None)


def seed(client: TheHiveClient, fixture: dict[str, Any], state_path: Path) -> dict[str, Any]:
    created = False
    case = None
    state: dict[str, Any] = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        case = client.request("GET", f"/api/v1/case/{state['case_id']}")
    if case is None:
        case = find_case(client, fixture["case"]["title"])
    if case is None:
        case = client.request("POST", "/api/v1/case", build_case_payload(fixture))
        created = True

    case_id = case["_id"]
    current_observables = client.request("POST", "/api/v1/query?name=phase6-observables", {"query": [{"_name": "getCase", "idOrName": case_id}, {"_name": "observables"}]})
    observable_ids = result_ids(current_observables)
    current_values = {str(item.get("data")) for item in current_observables}
    for observable in fixture["observables"]:
        expected = str(observable["data"][0])
        if expected not in current_values:
            observable_ids.extend(result_ids(client.request("POST", f"/api/v1/case/{case_id}/observable", observable)))

    current_tasks = client.request("POST", "/api/v1/query?name=phase6-tasks", {"query": [{"_name": "getCase", "idOrName": case_id}, {"_name": "tasks"}]})
    task_ids = result_ids(current_tasks)
    current_titles = {item.get("title") for item in current_tasks}
    for task in fixture["tasks"]:
        if task["title"] not in current_titles:
            task_ids.extend(result_ids(client.request("POST", f"/api/v1/case/{case_id}/task", task)))

    if created or not state.get("comment_added", False):
        client.request("POST", f"/api/v1/case/{case_id}/comment", {"message": fixture["comment"]})
    client.request("PATCH", f"/api/v1/case/{case_id}", {"status": "InProgress"})

    state = {"case_id": case_id, "tasks": task_ids, "observables": observable_ids, "comment_added": True}
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.chmod(state_path, 0o640)
    case = client.request("GET", f"/api/v1/case/{case_id}")
    return {"created": created, "case": case, "tasks": task_ids, "observables": observable_ids}


def sanitized(result: dict[str, Any]) -> dict[str, Any]:
    case = result["case"]
    return {
        "created": result["created"],
        "case_id": case.get("_id"),
        "case_number": case.get("number"),
        "title": case.get("title"),
        "severity": case.get("severity"),
        "status": case.get("status"),
        "tags": case.get("tags", []),
        "task_count": len(result["tasks"]),
        "observable_count": len(result["observables"]),
        "approval_state": "pending",
        "response_action_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=Path("/opt/soc-lab/secrets/thehive.env"))
    parser.add_argument("--state", type=Path, default=Path("/opt/soc-lab/state/phase6-case.json"))
    args = parser.parse_args()
    config = load_env(args.env_file)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    client = TheHiveClient(
        config["THEHIVE_URL"], config["THEHIVE_ORGANISATION"],
        config["THEHIVE_USERNAME"], config["THEHIVE_PASSWORD"]
    )
    print(json.dumps(sanitized(seed(client, fixture, args.state)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
