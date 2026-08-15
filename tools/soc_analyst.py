"""Local analyst client for approvals, delivery recovery, and bounded triage."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    analyst: str | None = None,
) -> Any:
    base_url = os.getenv("SOC_GATEWAY_URL", "http://10.77.30.10:8010").rstrip("/")
    token = os.getenv("SOC_APPROVAL_TOKEN", "")
    if len(token) < 32:
        raise RuntimeError("SOC_APPROVAL_TOKEN is missing or too short")
    headers = {"X-SOC-APPROVAL-TOKEN": token}
    if analyst:
        headers["X-SOC-ANALYST"] = analyst
    with httpx.Client(base_url=base_url, timeout=10, verify=False) as client:
        response = client.request(method, path, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Operate the isolated SOC lab without placing credentials on the command line."
    )
    commands = root.add_subparsers(dest="command", required=True)

    approvals = commands.add_parser("approvals", help="List approval records")
    approvals.add_argument(
        "--status", choices=["pending", "approve", "reject", "escalate"]
    )

    decide = commands.add_parser("decide", help="Record an analyst decision")
    decide.add_argument("approval_id")
    decide.add_argument("decision", choices=["approve", "reject", "escalate"])
    decide.add_argument("--analyst", required=True)
    decide.add_argument("--note", required=True)

    replay = commands.add_parser("replay", help="Requeue one terminal failed delivery")
    replay.add_argument("idempotency_key")

    reconcile = commands.add_parser(
        "reconcile-handoff", help="Resolve one ambiguous Shuffle handoff after review"
    )
    reconcile.add_argument("idempotency_key")
    reconcile.add_argument("outcome", choices=["retry", "completed"])
    reconcile.add_argument("--execution-id")
    reconcile.add_argument("--note", required=True)

    triage = commands.add_parser("triage-request", help="Request bounded triage")
    triage.add_argument("incident_id")
    triage.add_argument("endpoint", choices=["ubuntu-web-01", "win11-01"])
    triage.add_argument(
        "collection", choices=["linux_bounded_triage", "windows_bounded_triage"]
    )
    triage.add_argument("--analyst", required=True)
    triage.add_argument("--reason", required=True)

    triage_list = commands.add_parser("triage-list", help="List bounded triage records")
    triage_list.set_defaults(command="triage-list")
    return root


def run(arguments: argparse.Namespace) -> Any:
    if arguments.command == "approvals":
        suffix = f"?approval_status={arguments.status}" if arguments.status else ""
        return request("GET", f"/v1/approvals{suffix}")
    if arguments.command == "decide":
        return request(
            "POST",
            f"/v1/approvals/{arguments.approval_id}/decision",
            payload={
                "decision": arguments.decision,
                "analyst": arguments.analyst,
                "note": arguments.note,
            },
        )
    if arguments.command == "replay":
        return request("POST", f"/v1/deliveries/{arguments.idempotency_key}/replay")
    if arguments.command == "reconcile-handoff":
        return request(
            "POST",
            f"/v1/deliveries/{arguments.idempotency_key}/handoff-reconciliation",
            payload={
                "outcome": arguments.outcome,
                "execution_id": arguments.execution_id,
                "note": arguments.note,
            },
        )
    if arguments.command == "triage-request":
        return request(
            "POST",
            "/v1/triage",
            analyst=arguments.analyst,
            payload={
                "incident_id": arguments.incident_id,
                "endpoint": arguments.endpoint,
                "collection": arguments.collection,
                "reason": arguments.reason,
            },
        )
    if arguments.command == "triage-list":
        return request("GET", "/v1/triage")
    raise RuntimeError("unsupported command")


def main() -> int:
    try:
        result = run(parser().parse_args())
    except (RuntimeError, httpx.HTTPError) as exc:
        print(f"soc_analyst error={type(exc).__name__}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
