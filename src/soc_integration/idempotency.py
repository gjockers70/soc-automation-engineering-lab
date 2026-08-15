"""Durable duplicate suppression using SQLite."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path


class IdempotencyConflict(ValueError):
    """Raised when one key is reused for different content."""


class IdempotencyStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS receipts (key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, alert_id TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
                )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    @staticmethod
    def payload_hash(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def record(self, key: str, payload: bytes, alert_id: str) -> bool:
        digest = self.payload_hash(payload)
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT payload_hash FROM receipts WHERE key = ?", (key,)
                ).fetchone()
                if existing:
                    if existing[0] != digest:
                        raise IdempotencyConflict("idempotency key was reused for a different payload")
                    return False
                connection.execute(
                    "INSERT INTO receipts (key, payload_hash, alert_id) VALUES (?, ?, ?)",
                    (key, digest, alert_id),
                )
                return True

    def release(self, key: str) -> None:
        """Remove an incomplete delivery so the sender can retry it."""
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("DELETE FROM receipts WHERE key = ?", (key,))
