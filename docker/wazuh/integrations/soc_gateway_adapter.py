"""Wazuh custom-integration adapter with bounded local spooling."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_RULE_IDS = {"100100", "100101", "100102"}


@dataclass(frozen=True)
class AdapterConfig:
    gateway_url: str
    token: str
    spool_dir: Path
    timeout_seconds: float = 5.0
    max_flush: int = 25


def read_environment(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def load_config(path: Path) -> AdapterConfig:
    values = read_environment(path)
    url = values.get("SOC_GATEWAY_URL", "")
    token = values.get("SOC_WEBHOOK_TOKEN", "")
    if not url.startswith(("http://", "https://")):
        raise ValueError("SOC_GATEWAY_URL must be HTTP or HTTPS")
    if len(token) < 32:
        raise ValueError("SOC_WEBHOOK_TOKEN must contain at least 32 characters")
    return AdapterConfig(
        gateway_url=url,
        token=token,
        spool_dir=Path(values.get("SOC_GATEWAY_SPOOL", "/var/ossec/queue/soc-gateway-spool")),
        timeout_seconds=float(values.get("SOC_GATEWAY_TIMEOUT_SECONDS", "5")),
        max_flush=int(values.get("SOC_GATEWAY_MAX_FLUSH", "25")),
    )


def normalize_alert(raw: dict[str, Any]) -> dict[str, Any]:
    rule = raw.get("rule") if isinstance(raw.get("rule"), dict) else {}
    agent = raw.get("agent") if isinstance(raw.get("agent"), dict) else {}
    rule_id = str(rule.get("id", ""))
    groups = {str(value) for value in rule.get("groups", [])}
    if rule_id not in ALLOWED_RULE_IDS or "soc_lab" not in groups:
        raise ValueError("alert is outside the SOC lab integration allowlist")
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    return {
        "id": str(raw.get("id", "")),
        "timestamp": raw.get("timestamp"),
        "rule": {
            "id": rule_id,
            "level": int(rule.get("level", 0)),
            "description": str(rule.get("description", "")),
        },
        "agent": {
            "id": str(agent.get("id", "")),
            "name": str(agent.get("name", "")),
        },
        "data": data,
        "synthetic": True,
    }


def idempotency_key(payload: dict[str, Any]) -> str:
    material = "|".join(
        [
            str(payload.get("id", "")),
            str(payload.get("timestamp", "")),
            str(payload.get("agent", {}).get("id", "")),
            str(payload.get("rule", {}).get("id", "")),
        ]
    )
    return "wazuh-" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def send(config: AdapterConfig, key: str, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    request = urllib.request.Request(
        config.gateway_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-SOC-LAB-TOKEN": config.token,
            "Idempotency-Key": key,
        },
    )
    with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
        if response.status != 202:
            raise RuntimeError(f"gateway returned HTTP {response.status}")


def spool(config: AdapterConfig, key: str, payload: dict[str, Any]) -> Path:
    config.spool_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
    destination = config.spool_dir / f"{key}.json"
    temporary = config.spool_dir / f".{key}.{os.getpid()}.tmp"
    temporary.write_text(
        json.dumps({"key": key, "payload": payload}, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    os.chmod(temporary, 0o640)
    temporary.replace(destination)
    return destination


def flush(config: AdapterConfig) -> int:
    if not config.spool_dir.exists():
        return 0
    delivered = 0
    for path in sorted(config.spool_dir.glob("wazuh-*.json"))[: config.max_flush]:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            send(config, str(record["key"]), record["payload"])
        except (
            OSError,
            RuntimeError,
            ValueError,
            KeyError,
            json.JSONDecodeError,
            urllib.error.URLError,
        ):
            continue
        path.unlink()
        delivered += 1
    return delivered


def process(alert_path: Path, config_path: Path) -> str:
    config = load_config(config_path)
    raw = json.loads(alert_path.read_text(encoding="utf-8"))
    payload = normalize_alert(raw)
    key = idempotency_key(payload)
    flush(config)
    try:
        send(config, key, payload)
        return "delivered"
    except urllib.error.HTTPError as exc:
        if 400 <= exc.code < 500:
            raise ValueError(f"gateway permanently rejected delivery with HTTP {exc.code}") from exc
        spool(config, key, payload)
        return "spooled"
    except (OSError, RuntimeError, urllib.error.URLError):
        spool(config, key, payload)
        return "spooled"


def main(argv: list[str] | None = None) -> int:
    arguments = argv or sys.argv[1:]
    if not arguments:
        print("soc_gateway_adapter category=configuration", file=sys.stderr)
        return 1
    config_path = Path(
        os.getenv("SOC_GATEWAY_CONFIG", "/var/ossec/etc/soc-gateway.env")
    )
    try:
        result = process(Path(arguments[0]), config_path)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(
            f"soc_gateway_adapter category={type(exc).__name__}",
            file=sys.stderr,
        )
        return 1
    print(f"soc_gateway_adapter result={result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
