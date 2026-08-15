#!/usr/bin/env python3
"""Copy a file between two guests without exposing its content on the host."""

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
    parser.add_argument("source_domain")
    parser.add_argument("source_path")
    parser.add_argument("destination_domain")
    parser.add_argument("destination_path")
    args = parser.parse_args()

    source = call(
        args.source_domain,
        {"execute": "guest-file-open", "arguments": {"path": args.source_path, "mode": "r"}},
    )["return"]
    destination = call(
        args.destination_domain,
        {"execute": "guest-file-open", "arguments": {"path": args.destination_path, "mode": "w"}},
    )["return"]
    if not isinstance(source, int) or not isinstance(destination, int):
        raise RuntimeError("guest agent did not return valid file handles")

    try:
        while True:
            result = call(
                args.source_domain,
                {"execute": "guest-file-read", "arguments": {"handle": source, "count": 48 * 1024}},
            )["return"]
            if not isinstance(result, dict):
                raise RuntimeError("guest agent returned an invalid read result")
            encoded = result.get("buf-b64")
            if not isinstance(encoded, str):
                raise RuntimeError("guest agent did not return file data")
            data = base64.b64decode(encoded)
            if data:
                call(
                    args.destination_domain,
                    {
                        "execute": "guest-file-write",
                        "arguments": {
                            "handle": destination,
                            "buf-b64": base64.b64encode(data).decode("ascii"),
                        },
                    },
                )
            if result.get("eof") is True or not data:
                break
        call(
            args.destination_domain,
            {"execute": "guest-file-flush", "arguments": {"handle": destination}},
        )
    finally:
        call(args.source_domain, {"execute": "guest-file-close", "arguments": {"handle": source}})
        call(
            args.destination_domain,
            {"execute": "guest-file-close", "arguments": {"handle": destination}},
        )

    print("guest_file_copy=pass")


if __name__ == "__main__":
    main()
