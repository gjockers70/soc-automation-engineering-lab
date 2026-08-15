#!/usr/bin/env python3
"""Create or update five idempotent Shuffle handoff workflows and webhooks."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from pathlib import Path
from typing import Any

from shuffle_common import ShuffleClient, find_named, load_env


def node_id(key: str, kind: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"soc-lab:phase7:{key}:{kind}"))


def workflow_payload(spec: dict[str, Any], app: dict[str, Any], webhook_token: str) -> dict[str, Any]:
    trigger_id = node_id(spec["key"], "webhook")
    actions = []
    action_ids = []
    for index, label in enumerate(spec["handoff_steps"], start=1):
        action_id = node_id(spec["key"], f"step-{index}")
        action_ids.append(action_id)
        actions.append(
            {
                "app_name": "Shuffle Tools",
                "app_version": "1.2.0",
                "app_id": app["id"],
                "id": action_id,
                "is_valid": True,
                "isStartNode": index == 1,
                "label": label,
                "name": "repeat_back_to_me",
                "environment": "Shuffle",
                "parameters": [{"name": "call", "value": "$exec"}],
                "position": {"x": 450 + (index - 1) * 260, "y": 250},
                "priority": 3,
            }
        )
    branches = [
        {
            "id": node_id(spec["key"], "branch-trigger"),
            "source_id": trigger_id,
            "destination_id": action_ids[0],
        }
    ]
    branches.extend(
        {
            "id": node_id(spec["key"], f"branch-{index}"),
            "source_id": source,
            "destination_id": destination,
        }
        for index, (source, destination) in enumerate(zip(action_ids, action_ids[1:]), start=1)
    )
    return {
        "name": spec["name"],
        "description": spec["description"],
        "tags": [
            "soc-lab", "gateway-handoff", spec["key"],
            "approval-required" if spec["approval_required"] else "notify-only",
        ],
        "actions": actions,
        "triggers": [
            {
                "app_name": "Webhook",
                "name": "Webhook",
                "label": f"{spec['key']} authenticated intake",
                "id": trigger_id,
                "is_valid": True,
                "status": "running",
                "environment": "Shuffle",
                "trigger_type": "WEBHOOK",
                "parameters": [
                    {"name": "url", "value": f"http://127.0.0.1:5001/api/v1/hooks/webhook_{trigger_id}"},
                    {"name": "tmp", "value": f"webhook_{trigger_id}"},
                    {"name": "auth_headers", "value": f"X-SOC-LAB-TOKEN={webhook_token}"},
                    {"name": "custom_response_body", "value": ""},
                    {"name": "await_response", "value": "v1"},
                ],
                "position": {"x": 200, "y": 250},
            }
        ],
        "branches": branches,
        "start": action_ids[0],
        "is_valid": True,
        "execution_environment": "Shuffle",
        "workflow_variables": [],
        "execution_variables": [],
        "comments": [],
        "errors": [],
        "configuration": {"exit_on_error": True, "start_from_top": True, "skip_notifications": True},
    }


def start_hook(client: ShuffleClient, workflow: dict[str, Any], token: str) -> None:
    trigger = workflow["triggers"][0]
    payload = {
        "name": trigger["label"],
        "type": "webhook",
        "id": trigger["id"],
        "workflow": workflow["id"],
        "start": workflow["start"],
        "environment": "Shuffle",
        "auth": f"X-SOC-LAB-TOKEN={token}",
        "custom_response": "",
        "version": "v1",
        "version_timeout": 15,
    }
    result = client.request("POST", "/api/v1/hooks/new", payload)
    if isinstance(result, dict) and result.get("success") is False:
        reason = str(result.get("reason", ""))
        if "exist" not in reason.lower() and "running" not in reason.lower():
            raise RuntimeError(f"failed to start webhook: {reason}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=Path("/opt/soc-lab/secrets/shuffle.env"))
    parser.add_argument("--state", type=Path, default=Path("/opt/soc-lab/state/phase7-workflows.json"))
    args = parser.parse_args()

    config = load_env(args.env_file)
    client = ShuffleClient("http://127.0.0.1:5001", config["SHUFFLE_DEFAULT_APIKEY"])
    specs = json.loads(args.specs.read_text(encoding="utf-8"))
    apps = client.request("GET", "/api/v1/workflows/apps?limit=1000")
    app = next((item for item in apps if item.get("name") == "Shuffle Tools" and item.get("app_version") == "1.2.0"), None)
    if app is None or not app.get("activated"):
        raise RuntimeError("activated Shuffle Tools 1.2.0 app is required")

    workflows = client.request("GET", "/api/v1/workflows")
    state: dict[str, Any] = {"workflows": {}}
    for spec in specs:
        workflow = find_named(workflows, spec["name"])
        created = workflow is None
        payload = workflow_payload(spec, app, config["SHUFFLE_WEBHOOK_TOKEN"])
        if workflow is None:
            client.request("POST", "/api/v1/workflows", payload)
            workflows = client.request("GET", "/api/v1/workflows")
            workflow = find_named(workflows, spec["name"])
            if workflow is None:
                raise RuntimeError(f"workflow not found after creation: {spec['name']}")
        else:
            payload["id"] = workflow["id"]
            client.request("PUT", f"/api/v1/workflows/{workflow['id']}", payload)
        full = client.request("GET", f"/api/v1/workflows/{workflow['id']}")
        start_hook(client, full, config["SHUFFLE_WEBHOOK_TOKEN"])
        state["workflows"][spec["key"]] = {
            "workflow_id": full["id"],
            "webhook_id": full["triggers"][0]["id"],
            "created": created,
            "updated": not created,
            "handoff_steps": spec["handoff_steps"],
            "approval_required": spec["approval_required"],
            "response_action_enabled": False,
        }

    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(args.state, 0o640)
    print(json.dumps(state, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
