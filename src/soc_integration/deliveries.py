"""Durable alert inbox and retry queue backed by SQLite."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .idempotency import IdempotencyConflict


def _utc(value: float | None = None) -> str:
    return datetime.fromtimestamp(value or time.time(), timezone.utc).isoformat()


@dataclass(frozen=True)
class Delivery:
    key: str
    payload_hash: str
    alert_id: str
    trace_id: str
    payload: dict[str, Any]
    status: str
    attempts: int
    next_attempt_at: str | None
    last_error: str | None
    result: dict[str, Any] | None
    created_at: str
    updated_at: str


class DeliveryStore:
    """Persist before acknowledgement and claim work with atomic transitions."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS deliveries (
                    key TEXT PRIMARY KEY,
                    payload_hash TEXT NOT NULL,
                    alert_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    next_attempt_at TEXT,
                    last_error TEXT,
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS deliveries_due
                    ON deliveries(status, next_attempt_at, created_at);
                CREATE TABLE IF NOT EXISTS shuffle_handoffs (
                    trace_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    execution_id TEXT,
                    updated_at TEXT NOT NULL
                );
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def payload_hash(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def enqueue(self, key: str, payload: bytes, alert_id: str, trace_id: str) -> bool:
        digest = self.payload_hash(payload)
        now = _utc()
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT payload_hash FROM deliveries WHERE key = ?", (key,)
            ).fetchone()
            if row:
                connection.rollback()
                if row["payload_hash"] != digest:
                    raise IdempotencyConflict(
                        "idempotency key was reused for a different payload"
                    )
                return False
            connection.execute(
                """INSERT INTO deliveries(
                    key, payload_hash, alert_id, trace_id, payload_json, status,
                    next_attempt_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'queued', ?, ?, ?)""",
                (key, digest, alert_id, trace_id, payload.decode("utf-8"), now, now, now),
            )
            connection.commit()
            return True

    def claim_due(self) -> Delivery | None:
        now = _utc()
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT * FROM deliveries
                   WHERE status IN ('queued', 'retrying')
                     AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                   ORDER BY created_at LIMIT 1""",
                (now,),
            ).fetchone()
            if row is None:
                connection.rollback()
                return None
            connection.execute(
                """UPDATE deliveries SET status = 'processing', attempts = attempts + 1,
                   updated_at = ? WHERE key = ?""",
                (now, row["key"]),
            )
            connection.commit()
        return self.get(str(row["key"]))

    def complete(self, key: str, result: dict[str, Any]) -> None:
        now = _utc()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """UPDATE deliveries SET status = 'completed', result_json = ?,
                   last_error = NULL, next_attempt_at = NULL, updated_at = ? WHERE key = ?""",
                (json.dumps(result, separators=(",", ":"), sort_keys=True), now, key),
            )

    def fail(self, key: str, error: str, max_attempts: int, delay_seconds: float) -> str:
        record = self.get(key)
        terminal = record.attempts >= max_attempts
        status = "failed" if terminal else "retrying"
        next_attempt = None if terminal else _utc(time.time() + delay_seconds)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """UPDATE deliveries SET status = ?, last_error = ?, next_attempt_at = ?,
                   updated_at = ? WHERE key = ?""",
                (status, error[:200], next_attempt, _utc(), key),
            )
        return status

    def recover_processing(self) -> int:
        """Return interrupted work to the queue when the service starts."""
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                """UPDATE deliveries SET status = 'retrying', next_attempt_at = ?,
                   last_error = 'worker_restart', updated_at = ? WHERE status = 'processing'""",
                (_utc(), _utc()),
            )
            return cursor.rowcount

    def requeue(self, key: str) -> bool:
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                """UPDATE deliveries SET status = 'queued', attempts = 0, next_attempt_at = ?,
                   last_error = NULL, updated_at = ? WHERE key = ? AND status = 'failed'""",
                (_utc(), _utc(), key),
            )
            return cursor.rowcount == 1

    def get(self, key: str) -> Delivery:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM deliveries WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            raise KeyError(key)
        return Delivery(
            key=row["key"], payload_hash=row["payload_hash"], alert_id=row["alert_id"],
            trace_id=row["trace_id"], payload=json.loads(row["payload_json"]),
            status=row["status"], attempts=row["attempts"],
            next_attempt_at=row["next_attempt_at"], last_error=row["last_error"],
            result=json.loads(row["result_json"]) if row["result_json"] else None,
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def counts(self) -> dict[str, int]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT status, COUNT(*) AS count FROM deliveries GROUP BY status"
            ).fetchall()
        return {str(row["status"]): int(row["count"]) for row in rows}

    def reserve_handoff(self, trace_id: str) -> tuple[bool, str | None]:
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, execution_id FROM shuffle_handoffs WHERE trace_id = ?",
                (trace_id,),
            ).fetchone()
            if row:
                connection.rollback()
                return False, str(row["execution_id"]) if row["execution_id"] else None
            connection.execute(
                "INSERT INTO shuffle_handoffs(trace_id, status, updated_at) VALUES (?, 'pending', ?)",
                (trace_id, _utc()),
            )
            connection.commit()
            return True, None

    def complete_handoff(self, trace_id: str, execution_id: str | None) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """UPDATE shuffle_handoffs SET status = 'completed', execution_id = ?,
                   updated_at = ? WHERE trace_id = ?""",
                (execution_id, _utc(), trace_id),
            )

    def release_handoff(self, trace_id: str) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "DELETE FROM shuffle_handoffs WHERE trace_id = ? AND status = 'pending'",
                (trace_id,),
            )

    def reconcile_handoff(
        self, trace_id: str, outcome: str, execution_id: str | None = None
    ) -> None:
        """Resolve an ambiguous handoff after an analyst checks Shuffle."""
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, execution_id FROM shuffle_handoffs WHERE trace_id = ?",
                (trace_id,),
            ).fetchone()
            if row is None:
                connection.rollback()
                raise KeyError(trace_id)
            if row["status"] == "completed":
                if outcome == "completed" and row["execution_id"] == execution_id:
                    connection.rollback()
                    return
                connection.rollback()
                raise ValueError("Shuffle handoff is already completed")
            if outcome == "retry":
                connection.execute(
                    "DELETE FROM shuffle_handoffs WHERE trace_id = ? AND status = 'pending'",
                    (trace_id,),
                )
            elif outcome == "completed" and execution_id:
                connection.execute(
                    """UPDATE shuffle_handoffs SET status = 'completed', execution_id = ?,
                       updated_at = ? WHERE trace_id = ? AND status = 'pending'""",
                    (execution_id, _utc(), trace_id),
                )
            else:
                connection.rollback()
                raise ValueError("invalid Shuffle handoff reconciliation")
            connection.commit()

    def oldest_pending_age(self) -> float:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """SELECT MIN(created_at) AS oldest FROM deliveries
                   WHERE status IN ('queued', 'processing', 'retrying')"""
            ).fetchone()
        if not row or not row["oldest"]:
            return 0.0
        created = datetime.fromisoformat(str(row["oldest"]))
        return max(0.0, (datetime.now(timezone.utc) - created).total_seconds())
