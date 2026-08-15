"""Durable, analyst-initiated records for bounded Velociraptor triage."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import TriageRecord, TriageRequest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TriageStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        with closing(self._connect()) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS triage_requests (
                    request_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    collection TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def create(self, request: TriageRequest, analyst: str) -> TriageRecord:
        request_id = f"TRI-{uuid4()}"
        now = _now()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """INSERT INTO triage_requests(
                    request_id, incident_id, endpoint, collection, reason,
                    requested_by, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'requested', ?, ?)""",
                (
                    request_id, request.incident_id, request.endpoint,
                    request.collection, request.reason, analyst, now, now,
                ),
            )
        return self.get(request_id)

    def get(self, request_id: str) -> TriageRecord:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM triage_requests WHERE request_id = ?", (request_id,)
            ).fetchone()
        if row is None:
            raise KeyError(request_id)
        return TriageRecord(**dict(row))

    def list(self) -> list[TriageRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM triage_requests ORDER BY created_at"
            ).fetchall()
        return [TriageRecord(**dict(row)) for row in rows]

    def update(self, request_id: str, status: str, summary: str | None = None) -> TriageRecord:
        allowed = {"collecting", "completed", "failed"}
        if status not in allowed:
            raise ValueError("invalid triage status")
        if status == "completed" and not summary:
            raise ValueError("completed triage requires a sanitized summary")
        current = self.get(request_id)
        if current.status in {"completed", "failed"}:
            if current.status == status and current.summary == summary:
                return current
            raise ValueError("triage request is already finalized")
        transitions = {
            "requested": {"collecting", "completed", "failed"},
            "collecting": {"completed", "failed"},
        }
        if status not in transitions[current.status]:
            raise ValueError("invalid triage status transition")
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                """UPDATE triage_requests SET status = ?, summary = ?, updated_at = ?
                   WHERE request_id = ?""",
                (status, summary, _now(), request_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(request_id)
        return self.get(request_id)
