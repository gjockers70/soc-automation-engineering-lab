#!/usr/bin/env python3
"""Invoke a Phase 7 authenticated webhook and report its execution record."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from shuffle_common import ShuffleClient, load_env


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=Path("/opt/soc-lab/secrets/shuffle.env"))
    parser.add_argument("--state", type=Path, default=Path("/opt/soc-lab/state/phase7-workflows.json"))
    args = parser.parse_args()

    config = load_env(args.env_file)
    state = json.loads(args.state.read_text(encoding="utf-8"))["workflows"][args.key]
    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))[args.key]
    url = f"http://127.0.0.1:5001/api/v1/hooks/webhook_{state['webhook_id']}"
    body = json.dumps(inputs).encode()

    unauthenticated = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(unauthenticated, timeout=15)
        raise RuntimeError("webhook accepted a request without the required header")
    except urllib.error.HTTPError as exc:
        if exc.code != 401:
            raise

    authenticated = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "X-SOC-LAB-TOKEN": config["SHUFFLE_WEBHOOK_TOKEN"]},
        method="POST",
    )
    with urllib.request.urlopen(authenticated, timeout=30) as response:
        response_body = response.read().decode(errors="replace")
        webhook_status = response.status

    client = ShuffleClient("http://127.0.0.1:5001", config["SHUFFLE_DEFAULT_APIKEY"])
    execution = None
    terminal_statuses = {"ABORTED", "FAILURE", "FAILED", "FINISHED", "SUCCESS"}
    for _ in range(30):
        executions = client.request("GET", f"/api/v1/workflows/{state['workflow_id']}/executions")
        if executions:
            if isinstance(executions, dict):
                executions = executions.get("executions", [])
            execution = max(executions, key=lambda item: item.get("started_at", 0), default=None)
            if execution and str(execution.get("status", "")).upper() in terminal_statuses:
                break
        time.sleep(2)
    if execution is None:
        raise RuntimeError("no Shuffle execution record was created")
    if str(execution.get("status", "")).upper() not in {"FINISHED", "SUCCESS"}:
        raise RuntimeError(f"Shuffle execution did not finish successfully: {execution.get('status')}")

    result = {
        "playbook": args.key,
        "workflow_id": state["workflow_id"],
        "webhook_id": state["webhook_id"],
        "unauthenticated_status": 401,
        "authenticated_status": webhook_status,
        "webhook_response_present": bool(response_body),
        "execution_id": execution.get("execution_id"),
        "execution_status": execution.get("status"),
        "synthetic_input": inputs.get("synthetic") is True,
        "approval_required": True,
        "response_action_executed": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
