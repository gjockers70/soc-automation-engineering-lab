#!/usr/bin/env python3
"""Small standard-library MISP client for the isolated SOC lab."""

from __future__ import annotations

import ipaddress
import json
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class MispError(RuntimeError):
    """Raised when a MISP request or response cannot be processed."""


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


class MispClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        if not re.fullmatch(r"[A-Za-z0-9]{40}", api_key):
            raise ValueError("MISP API key must be 40 alphanumeric characters")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.ssl_context = ssl._create_unverified_context()

    def request(self, method: str, path: str, payload: Any | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/{path.lstrip('/')}",
            data=data,
            method=method,
            headers={
                "Authorization": self.api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "soc-lab-misp-client/1.0",
            },
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout, context=self.ssl_context
            ) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise MispError(f"MISP returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise MispError(f"MISP request failed: {exc}") from exc
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise MispError("MISP returned a non-JSON response") from exc


def client_from_env_file(path: Path, timeout: float = 10.0) -> MispClient:
    values = load_env(path)
    try:
        return MispClient(values["BASE_URL"], values["ADMIN_KEY"], timeout)
    except KeyError as exc:
        raise ValueError(f"missing required setting: {exc.args[0]}") from exc


def validate_indicator(value: str, indicator_type: str) -> str:
    value = value.strip()
    if indicator_type == "ip":
        ipaddress.ip_address(value)
    elif indicator_type == "domain":
        if len(value) > 253 or not re.fullmatch(
            r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}",
            value,
        ):
            raise ValueError("invalid domain indicator")
    elif indicator_type == "url":
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("invalid URL indicator")
    elif indicator_type == "hash":
        if not re.fullmatch(r"(?:[A-Fa-f0-9]{32}|[A-Fa-f0-9]{40}|[A-Fa-f0-9]{64})", value):
            raise ValueError("hash must be MD5, SHA-1, or SHA-256 hexadecimal")
        value = value.lower()
    else:
        raise ValueError(f"unsupported indicator type: {indicator_type}")
    return value


def misp_types(indicator_type: str, value: str) -> list[str]:
    if indicator_type == "ip":
        return ["ip-src", "ip-dst"]
    if indicator_type == "domain":
        return ["domain"]
    if indicator_type == "url":
        return ["url"]
    return [{32: "md5", 40: "sha1", 64: "sha256"}[len(value)]]


def extract_attributes(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, list):
        return [item for item in response if isinstance(item, dict)]
    if not isinstance(response, dict):
        return []
    nested = response.get("response", response)
    if isinstance(nested, dict):
        nested = nested.get("Attribute", nested.get("attributes", []))
    if isinstance(nested, list):
        return [item for item in nested if isinstance(item, dict)]
    return []


def normalize_result(
    indicator: str,
    indicator_type: str,
    attributes: list[dict[str, Any]],
    fixture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sources = []
    tags: set[str] = set()
    for attribute in attributes:
        sources.append(
            {
                "name": "local-misp",
                "event_id": str(attribute.get("event_id", "")),
                "attribute_uuid": str(attribute.get("uuid", "")),
            }
        )
        for tag in attribute.get("Tag", []):
            if isinstance(tag, dict) and tag.get("name"):
                tags.add(str(tag["name"]))
    if fixture:
        tags.update(str(tag) for tag in fixture.get("tags", []))
    return {
        "indicator": indicator,
        "type": indicator_type,
        "sources": sources,
        "reputation": fixture.get("reputation", "unknown") if fixture and attributes else "unknown",
        "confidence": int(fixture.get("confidence", 0)) if fixture and attributes else 0,
        "tags": sorted(tags) if attributes else [],
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
