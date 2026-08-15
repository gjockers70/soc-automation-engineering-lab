"""Cross-alert incident fingerprint persistence."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from datetime import timezone
from pathlib import Path

from .enrichment import Indicator
from .models import WazuhAlert


class IncidentStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        with closing(sqlite3.connect(path, timeout=5)) as connection:
            with connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS incidents (fingerprint TEXT PRIMARY KEY, case_id TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
                )

    @staticmethod
    def fingerprint(alert: WazuhAlert, indicators: list[Indicator]) -> str:
        material = "|".join(
            [
                alert.timestamp.astimezone(timezone.utc).strftime("%Y%m%d%H"),
                alert.rule.id,
                alert.agent.id,
                *(f"{item.type}:{item.value}" for item in indicators),
            ]
        )
        return hashlib.sha256(material.encode()).hexdigest()

    def reserve(self, fingerprint: str) -> tuple[bool, str | None]:
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT case_id FROM incidents WHERE fingerprint = ?", (fingerprint,)
                ).fetchone()
                if existing:
                    return False, existing[0]
                connection.execute("INSERT INTO incidents (fingerprint) VALUES (?)", (fingerprint,))
                return True, None

    def complete(self, fingerprint: str, case_id: str) -> None:
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            with connection:
                connection.execute(
                    "UPDATE incidents SET case_id = ? WHERE fingerprint = ?", (case_id, fingerprint)
                )

    def release(self, fingerprint: str) -> None:
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            with connection:
                connection.execute(
                    "DELETE FROM incidents WHERE fingerprint = ? AND case_id IS NULL", (fingerprint,)
                )
