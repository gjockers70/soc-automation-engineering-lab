"""IOC extraction and normalized local-MISP enrichment."""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class Indicator(BaseModel):
    value: str
    type: str


class InvalidIndicator(BaseModel):
    key: str
    value: str
    expected_type: str
    reason: str = "invalid_format"


class EnrichmentResult(BaseModel):
    indicator: str
    type: str
    sources: list[dict[str, str]] = Field(default_factory=list)
    reputation: str = "unknown"
    confidence: int = Field(default=0, ge=0, le=100)
    tags: list[str] = Field(default_factory=list)
    timestamp: str


KEY_TYPES = {
    "srcip": "ip", "source_ip": "ip", "dstip": "ip", "destination_ip": "ip", "ip": "ip",
    "domain": "domain", "query": "domain", "hostname": "domain",
    "url": "url", "uri": "url",
    "hash": "hash", "md5": "hash", "sha1": "hash", "sha256": "hash",
}


def _walk(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key.lower(), nested
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)


def _valid(value: str, indicator_type: str) -> bool:
    try:
        if indicator_type == "ip":
            ipaddress.ip_address(value)
            return True
        if indicator_type == "url":
            parsed = urlparse(value)
            return parsed.scheme in {"http", "https"} and bool(parsed.hostname)
        if indicator_type == "hash":
            return bool(re.fullmatch(r"(?:[A-Fa-f0-9]{32}|[A-Fa-f0-9]{40}|[A-Fa-f0-9]{64})", value))
        return bool(re.fullmatch(r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}", value))
    except ValueError:
        return False


def extract_indicators(data: dict[str, Any]) -> list[Indicator]:
    found: dict[tuple[str, str], Indicator] = {}
    for key, raw_value in _walk(data):
        indicator_type = KEY_TYPES.get(key)
        if not indicator_type or not isinstance(raw_value, str):
            continue
        value = raw_value.strip().lower() if indicator_type in {"domain", "hash"} else raw_value.strip()
        if _valid(value, indicator_type):
            found[(indicator_type, value)] = Indicator(value=value, type=indicator_type)
    return sorted(found.values(), key=lambda item: (item.type, item.value))


def invalid_indicator_candidates(data: dict[str, Any]) -> list[InvalidIndicator]:
    """Return explicit IOC fields whose string values fail format validation."""
    invalid: dict[tuple[str, str, str], InvalidIndicator] = {}
    for key, raw_value in _walk(data):
        indicator_type = KEY_TYPES.get(key)
        if not indicator_type or not isinstance(raw_value, str):
            continue
        value = raw_value.strip().lower() if indicator_type in {"domain", "hash"} else raw_value.strip()
        if value and not _valid(value, indicator_type):
            invalid[(key, indicator_type, value)] = InvalidIndicator(
                key=key,
                value=value,
                expected_type=indicator_type,
            )
    return sorted(invalid.values(), key=lambda item: (item.expected_type, item.key, item.value))


def misp_types(indicator: Indicator) -> list[str]:
    if indicator.type == "ip":
        return ["ip-src", "ip-dst"]
    if indicator.type == "hash":
        return [{32: "md5", 40: "sha1", 64: "sha256"}[len(indicator.value)]]
    return [indicator.type]


def extract_misp_attributes(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, list):
        return [item for item in response if isinstance(item, dict)]
    if not isinstance(response, dict):
        return []
    nested = response.get("response", response)
    if isinstance(nested, dict):
        nested = nested.get("Attribute", nested.get("attributes", []))
    return [item for item in nested if isinstance(item, dict)] if isinstance(nested, list) else []


def _metadata(attributes: list[dict[str, Any]]) -> tuple[str, int, set[str]]:
    reputation = "unknown"
    confidence = 0
    tags: set[str] = set()
    for attribute in attributes:
        for tag in attribute.get("Tag", []):
            if isinstance(tag, dict) and tag.get("name"):
                tags.add(str(tag["name"]))
        comment = str(attribute.get("comment", ""))
        if comment.startswith("soc_lab_metadata="):
            try:
                metadata = json.loads(comment.split("=", 1)[1])
                reputation = str(metadata.get("reputation", reputation))
                candidate_confidence = max(0, min(100, int(metadata.get("confidence", 0))))
                confidence = max(confidence, candidate_confidence)
                candidate_tags = metadata.get("tags", [])
                if isinstance(candidate_tags, list):
                    tags.update(str(tag) for tag in candidate_tags if isinstance(tag, str))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
    return reputation, confidence, tags


def normalize_misp(indicator: Indicator, response: Any) -> EnrichmentResult:
    attributes = extract_misp_attributes(response)
    reputation, confidence, tags = _metadata(attributes)
    sources = [
        {
            "name": "local-misp",
            "event_id": str(item.get("event_id", "")),
            "attribute_uuid": str(item.get("uuid", "")),
        }
        for item in attributes
    ]
    return EnrichmentResult(
        indicator=indicator.value,
        type=indicator.type,
        sources=sources,
        reputation=reputation if attributes else "unknown",
        confidence=confidence if attributes else 0,
        tags=sorted(tags) if attributes else [],
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
