#!/usr/bin/env python3
"""Run a local PowerShell script through a Windows QEMU guest agent."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path


def agent_command(domain: str, payload: dict[str, object]) -> dict[str, object]:
    result = subprocess.run(
        [
            "virsh",
            "-c",
            "qemu:///system",
            "qemu-agent-command",
            domain,
            json.dumps(payload, separators=(",", ":")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def decode_output(result: dict[str, object], field: str) -> str:
    encoded = result.get(field)
    if not isinstance(encoded, str):
        return ""
    return base64.b64decode(encoded).decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("script", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    encoded_script = base64.b64encode(
        args.script.read_text(encoding="utf-8").encode("utf-16le")
    ).decode("ascii")
    started = agent_command(
        args.domain,
        {
            "execute": "guest-exec",
            "arguments": {
                "path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "arg": [
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-EncodedCommand",
                    encoded_script,
                ],
                "capture-output": True,
            },
        },
    )
    pid = started.get("return", {}).get("pid")  # type: ignore[union-attr]
    if not isinstance(pid, int):
        raise RuntimeError("guest agent did not return a process id")

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        status = agent_command(
            args.domain,
            {"execute": "guest-exec-status", "arguments": {"pid": pid}},
        ).get("return", {})
        if isinstance(status, dict) and status.get("exited") is True:
            sys.stdout.write(decode_output(status, "out-data"))
            sys.stderr.write(decode_output(status, "err-data"))
            return int(status.get("exitcode", 1))
        time.sleep(1)

    raise TimeoutError(f"guest command exceeded {args.timeout} seconds")


if __name__ == "__main__":
    raise SystemExit(main())
