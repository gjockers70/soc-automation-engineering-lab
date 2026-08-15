"""Environment-backed, validated service configuration."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl, SecretStr, ValidationError


class Settings(BaseModel):
    webhook_token: SecretStr = Field(min_length=32)
    approval_token: SecretStr = Field(default=SecretStr("a" * 32), min_length=32)
    audit_path: Path = Path("/var/lib/soc-integration/audit.jsonl")
    idempotency_db: Path = Path("/var/lib/soc-integration/idempotency.sqlite3")
    request_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    retry_attempts: int = Field(default=3, ge=1, le=5)
    retry_backoff_seconds: float = Field(default=0.25, ge=0, le=5)
    wazuh_url: HttpUrl = "https://10.77.30.10:55000"  # type: ignore[assignment]
    wazuh_username: str = ""
    wazuh_password: SecretStr = SecretStr("")
    shuffle_url: HttpUrl = "http://127.0.0.1:5001"  # type: ignore[assignment]
    shuffle_api_key: SecretStr = SecretStr("")
    misp_url: HttpUrl = "https://10.77.30.10:8443"  # type: ignore[assignment]
    misp_api_key: SecretStr = SecretStr("")
    thehive_url: HttpUrl = "http://127.0.0.1:9000"  # type: ignore[assignment]
    thehive_organisation: str = "SOC-LAB"
    thehive_username: str = ""
    thehive_password: SecretStr = SecretStr("")
    verify_internal_tls: bool = False
    worker_poll_seconds: float = Field(default=0.5, ge=0.05, le=30)
    worker_max_attempts: int = Field(default=5, ge=1, le=20)
    worker_retry_backoff_seconds: float = Field(default=2.0, ge=0, le=300)
    shuffle_webhook_token: SecretStr = SecretStr("")
    shuffle_suspicious_login_webhook: HttpUrl | None = None
    shuffle_suspicious_file_webhook: HttpUrl | None = None
    shuffle_suspicious_domain_webhook: HttpUrl | None = None
    shuffle_account_activity_webhook: HttpUrl | None = None
    shuffle_security_alert_webhook: HttpUrl | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        values = {
            "webhook_token": os.getenv("SOC_WEBHOOK_TOKEN", ""),
            "approval_token": os.getenv("SOC_APPROVAL_TOKEN", ""),
            "audit_path": os.getenv("SOC_AUDIT_PATH", "/var/lib/soc-integration/audit.jsonl"),
            "idempotency_db": os.getenv("SOC_IDEMPOTENCY_DB", "/var/lib/soc-integration/idempotency.sqlite3"),
            "request_timeout_seconds": os.getenv("SOC_REQUEST_TIMEOUT_SECONDS", "5"),
            "retry_attempts": os.getenv("SOC_RETRY_ATTEMPTS", "3"),
            "retry_backoff_seconds": os.getenv("SOC_RETRY_BACKOFF_SECONDS", "0.25"),
            "wazuh_url": os.getenv("WAZUH_URL", "https://10.77.30.10:55000"),
            "wazuh_username": os.getenv("WAZUH_USERNAME", ""),
            "wazuh_password": os.getenv("WAZUH_PASSWORD", ""),
            "shuffle_url": os.getenv("SHUFFLE_URL", "http://127.0.0.1:5001"),
            "shuffle_api_key": os.getenv("SHUFFLE_API_KEY", ""),
            "misp_url": os.getenv("MISP_URL", "https://10.77.30.10:8443"),
            "misp_api_key": os.getenv("MISP_API_KEY", ""),
            "thehive_url": os.getenv("THEHIVE_URL", "http://127.0.0.1:9000"),
            "thehive_organisation": os.getenv("THEHIVE_ORGANISATION", "SOC-LAB"),
            "thehive_username": os.getenv("THEHIVE_USERNAME", ""),
            "thehive_password": os.getenv("THEHIVE_PASSWORD", ""),
            "verify_internal_tls": os.getenv("SOC_VERIFY_INTERNAL_TLS", "false"),
            "worker_poll_seconds": os.getenv("SOC_WORKER_POLL_SECONDS", "0.5"),
            "worker_max_attempts": os.getenv("SOC_WORKER_MAX_ATTEMPTS", "5"),
            "worker_retry_backoff_seconds": os.getenv("SOC_WORKER_RETRY_BACKOFF_SECONDS", "2"),
            "shuffle_webhook_token": os.getenv("SHUFFLE_WEBHOOK_TOKEN", ""),
            "shuffle_suspicious_login_webhook": os.getenv("SHUFFLE_SUSPICIOUS_LOGIN_WEBHOOK") or None,
            "shuffle_suspicious_file_webhook": os.getenv("SHUFFLE_SUSPICIOUS_FILE_WEBHOOK") or None,
            "shuffle_suspicious_domain_webhook": os.getenv("SHUFFLE_SUSPICIOUS_DOMAIN_WEBHOOK") or None,
            "shuffle_account_activity_webhook": os.getenv("SHUFFLE_ACCOUNT_ACTIVITY_WEBHOOK") or None,
            "shuffle_security_alert_webhook": os.getenv("SHUFFLE_SECURITY_ALERT_WEBHOOK") or None,
        }
        return cls.model_validate(values)


__all__ = ["Settings", "ValidationError"]
