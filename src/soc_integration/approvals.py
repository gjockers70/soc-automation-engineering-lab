"""Durable human-approval ledger and allow-listed lab response executor."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import ApprovalDecision, ApprovalProposal, ApprovalRecord


class ApprovalNotFound(KeyError):
    """Raised when an approval identifier does not exist."""


class ApprovalConflict(RuntimeError):
    """Raised when a finalized approval receives a different decision."""


class ApprovalStore:
    """Persist proposals and execute one reversible, application-only action."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    analyst TEXT,
                    analyst_note TEXT,
                    execution_result TEXT
                );
                CREATE TABLE IF NOT EXISTS lab_identities (
                    identity TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS approval_sources (
                    trace_id TEXT PRIMARY KEY,
                    approval_id TEXT NOT NULL UNIQUE,
                    FOREIGN KEY(approval_id) REFERENCES approvals(approval_id)
                );
                """
            )
            now = datetime.now(timezone.utc).isoformat()
            connection.execute(
                "INSERT OR IGNORE INTO lab_identities(identity, state, updated_at) VALUES (?, 'enabled', ?)",
                ("soc-response-test", now),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def create(self, proposal: ApprovalProposal) -> ApprovalRecord:
        approval_id = f"APR-{uuid4()}"
        created_at = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """INSERT INTO approvals(
                    approval_id, incident_id, action, target, reason, evidence_json,
                    confidence, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
                (
                    approval_id, proposal.incident_id, proposal.action, proposal.target,
                    proposal.reason, json.dumps(proposal.evidence), proposal.confidence, created_at,
                ),
            )
            connection.commit()
        return self.get(approval_id)

    def create_once(self, trace_id: str, proposal: ApprovalProposal) -> ApprovalRecord:
        """Create exactly one proposal for an automated trace."""
        approval_id = f"APR-{uuid4()}"
        created_at = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT approval_id FROM approval_sources WHERE trace_id = ?", (trace_id,)
            ).fetchone()
            if row:
                connection.rollback()
                return self.get(str(row["approval_id"]))
            connection.execute(
                """INSERT INTO approvals(
                    approval_id, incident_id, action, target, reason, evidence_json,
                    confidence, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
                (
                    approval_id,
                    proposal.incident_id,
                    proposal.action,
                    proposal.target,
                    proposal.reason,
                    json.dumps(proposal.evidence),
                    proposal.confidence,
                    created_at,
                )
            )
            connection.execute(
                "INSERT INTO approval_sources(trace_id, approval_id) VALUES (?, ?)",
                (trace_id, approval_id),
            )
            connection.commit()
        return self.get(approval_id)

    def list(self, status: str | None = None) -> list[ApprovalRecord]:
        query = "SELECT * FROM approvals"
        values: tuple[str, ...] = ()
        if status:
            query += " WHERE status = ?"
            values = (status,)
        query += " ORDER BY created_at"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, values).fetchall()
        return [self._record(row) for row in rows]

    def get(self, approval_id: str) -> ApprovalRecord:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,),
            ).fetchone()
        if row is None:
            raise ApprovalNotFound(approval_id)
        return self._record(row)

    def identity_state(self, identity: str) -> str:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT state FROM lab_identities WHERE identity = ?", (identity,),
            ).fetchone()
        if row is None:
            raise ApprovalNotFound(identity)
        return str(row["state"])

    def decide(self, approval_id: str, decision: ApprovalDecision) -> ApprovalRecord:
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,),
            ).fetchone()
            if row is None:
                raise ApprovalNotFound(approval_id)
            if row["status"] != "pending":
                if row["status"] == decision.decision:
                    return self._record(row)
                raise ApprovalConflict(f"approval is already finalized as {row['status']}")

            decided_at = datetime.now(timezone.utc).isoformat()
            execution_result: str | None = None
            status = decision.decision
            if decision.decision == "approve":
                if row["action"] != "disable_synthetic_account" or row["target"] != "soc-response-test":
                    raise ApprovalConflict("stored action or target is outside the response allowlist")
                identity = connection.execute(
                    "SELECT state FROM lab_identities WHERE identity = ?", (row["target"],),
                ).fetchone()
                if identity is None:
                    raise ApprovalNotFound(str(row["target"]))
                if identity["state"] == "enabled":
                    connection.execute(
                        "UPDATE lab_identities SET state = 'disabled', updated_at = ? WHERE identity = ?",
                        (decided_at, row["target"]),
                    )
                    execution_result = "disabled"
                else:
                    execution_result = "already_disabled"

            connection.execute(
                """UPDATE approvals SET status = ?, decided_at = ?, analyst = ?,
                   analyst_note = ?, execution_result = ? WHERE approval_id = ?""",
                (
                    status, decided_at, decision.analyst, decision.note,
                    execution_result, approval_id,
                ),
            )
            connection.commit()
            updated = connection.execute(
                "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,),
            ).fetchone()
        return self._record(updated)

    @staticmethod
    def _record(row: sqlite3.Row) -> ApprovalRecord:
        return ApprovalRecord(
            approval_id=row["approval_id"], incident_id=row["incident_id"],
            action=row["action"], target=row["target"], reason=row["reason"],
            evidence=json.loads(row["evidence_json"]), confidence=row["confidence"],
            status=row["status"], created_at=row["created_at"], decided_at=row["decided_at"],
            analyst=row["analyst"], analyst_note=row["analyst_note"],
            execution_result=row["execution_result"],
            response_action_executed=row["execution_result"] == "disabled",
        )
