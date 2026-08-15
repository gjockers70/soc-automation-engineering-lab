#!/usr/bin/env python3
"""Write one local file to a guest through the QEMU guest agent."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess


def call(domain: str, payload: dict[str, object]) -> dict[str, object]:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("--mode", default="w")
    args = parser.parse_args()

    opened = call(
        args.domain,
        {
            "execute": "guest-file-open",
            "arguments": {"path": args.destination, "mode": args.mode},
        },
    )
    handle = opened["return"]
    if not isinstance(handle, int):
        raise RuntimeError("guest agent did not return a file handle")

    try:
        with open(args.source, "rb") as source:
            while chunk := source.read(48 * 1024):
                call(
                    args.domain,
                    {
                        "execute": "guest-file-write",
                        "arguments": {
                            "handle": handle,
                            "buf-b64": base64.b64encode(chunk).decode("ascii"),
                        },
                    },
                )
        call(
            args.domain,
            {"execute": "guest-file-flush", "arguments": {"handle": handle}},
        )
    finally:
        call(
            args.domain,
            {"execute": "guest-file-close", "arguments": {"handle": handle}},
        )


if __name__ == "__main__":
    main()
