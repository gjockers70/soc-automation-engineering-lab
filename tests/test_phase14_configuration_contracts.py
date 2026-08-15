from __future__ import annotations

from datetime import timezone

import pytest
from pydantic import ValidationError

from soc_integration.config import Settings
from soc_integration.enrichment import (
    Indicator,
    extract_indicators,
    invalid_indicator_candidates,
    misp_types,
    normalize_misp,
)
from soc_integration.models import WazuhAlert, WebhookReceipt
from soc_integration.scoring import score_alert, thehive_severity


def valid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOC_WEBHOOK_TOKEN", "w" * 32)
    monkeypatch.setenv("SOC_APPROVAL_TOKEN", "a" * 32)


def test_settings_load_typed_environment_and_keep_secrets_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid_environment(monkeypatch)
    monkeypatch.setenv("SOC_RETRY_ATTEMPTS", "5")
    monkeypatch.setenv("SOC_REQUEST_TIMEOUT_SECONDS", "2.5")
    monkeypatch.setenv("SOC_VERIFY_INTERNAL_TLS", "true")
    settings = Settings.from_env()
    assert settings.retry_attempts == 5
    assert settings.request_timeout_seconds == 2.5
    assert settings.verify_internal_tls is True
    assert settings.webhook_token.get_secret_value() == "w" * 32
    assert "w" * 32 not in repr(settings)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("SOC_WEBHOOK_TOKEN", "short"),
        ("SOC_APPROVAL_TOKEN", "short"),
        ("SOC_RETRY_ATTEMPTS", "6"),
        ("SOC_REQUEST_TIMEOUT_SECONDS", "0"),
        ("SOC_RETRY_BACKOFF_SECONDS", "6"),
    ],
)
def test_settings_reject_unsafe_bounds(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    valid_environment(monkeypatch)
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings.from_env()


def test_alert_contract_requires_timezone_and_synthetic_flag(
    synthetic_alert_payload: dict,
) -> None:
    without_timezone = {**synthetic_alert_payload, "timestamp": "2026-08-14T12:00:00"}
    with pytest.raises(ValidationError):
        WazuhAlert.model_validate(without_timezone)
    non_synthetic = {**synthetic_alert_payload, "synthetic": False}
    with pytest.raises(ValidationError):
        WazuhAlert.model_validate(non_synthetic)


def test_alert_contract_preserves_extra_source_context(synthetic_alert_payload: dict) -> None:
    payload = {**synthetic_alert_payload, "location": "synthetic-auth.log"}
    alert = WazuhAlert.model_validate(payload)
    assert alert.timestamp.astimezone(timezone.utc).hour == 17
    assert alert.model_extra == {"location": "synthetic-auth.log"}


def test_receipt_cannot_claim_a_response_action() -> None:
    with pytest.raises(ValidationError):
        WebhookReceipt(
            status="accepted",
            alert_id="phase14-001",
            idempotency_key="phase14-key",
            response_action_executed=True,
        )


def test_all_ioc_types_are_normalized_and_deduplicated(
    synthetic_alert_payload: dict,
) -> None:
    data = {
        **synthetic_alert_payload["data"],
        "nested": {"source_ip": "198.51.100.44", "domain": "PHASE14.TEST"},
    }
    indicators = extract_indicators(data)
    assert [(item.type, item.value) for item in indicators] == [
        ("domain", "phase14.test"),
        ("hash", "a" * 64),
        ("ip", "198.51.100.44"),
        ("url", "https://phase14.test/download"),
    ]
    assert [misp_types(item) for item in indicators] == [
        ["domain"],
        ["sha256"],
        ["ip-src", "ip-dst"],
        ["url"],
    ]


def test_malformed_iocs_are_reported_without_enrichment() -> None:
    invalid = invalid_indicator_candidates(
        {
            "srcip": "999.1.1.1",
            "domain": "not a domain",
            "url": "file:///tmp/test",
            "sha256": "abcd",
        }
    )
    assert {(item.expected_type, item.reason) for item in invalid} == {
        ("ip", "invalid_format"),
        ("domain", "invalid_format"),
        ("url", "invalid_format"),
        ("hash", "invalid_format"),
    }


def test_untrusted_misp_metadata_is_bounded() -> None:
    result = normalize_misp(
        Indicator(value="phase14.test", type="domain"),
        {
            "response": {
                "Attribute": [
                    {
                        "event_id": "14",
                        "uuid": "synthetic-14",
                        "comment": (
                            'soc_lab_metadata={"reputation":"suspicious",'
                            '"confidence":999,"tags":"not-a-list"}'
                        ),
                    }
                ]
            }
        },
    )
    assert result.confidence == 100
    assert result.tags == []


@pytest.mark.parametrize(
    ("rule_level", "confidence", "expected_score", "expected_severity"),
    [
        (0, 0, 0, "low"),
        (7, 0, 28, "low"),
        (8, 0, 32, "medium"),
        (15, 0, 60, "high"),
        (15, 100, 90, "critical"),
    ],
)
def test_scoring_boundaries_are_stable(
    rule_level: int,
    confidence: int,
    expected_score: int,
    expected_severity: str,
) -> None:
    enrichments = []
    if confidence:
        enrichments = [
            normalize_misp(
                Indicator(value="phase14.test", type="domain"),
                {
                    "response": {
                        "Attribute": [
                            {
                                "event_id": "14",
                                "uuid": "synthetic-14",
                                "comment": (
                                    "soc_lab_metadata="
                                    f'{{"reputation":"suspicious","confidence":{confidence}}}'
                                ),
                            }
                        ]
                    }
                },
            )
        ]
        expected_score += 2
    result = score_alert(rule_level, enrichments)
    assert (result.score, result.severity) == (expected_score, expected_severity)
    assert thehive_severity(result.severity) in {1, 2, 3}
