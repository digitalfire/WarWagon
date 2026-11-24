"""Durable, append-only WarWagon engagement ledger (SQLite, stdlib).

One canonical event contract is shared by HTTP replay, agent execution and the
React console. This module does not execute an assessment or create findings.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterator
from uuid import uuid4

SCHEMA_VERSION = 1
EVENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
STATES = ("created", "running", "completed", "failed", "canceled")
TRANSITIONS = {
    "created": {"running", "canceled", "failed"},
    "running": {"completed", "failed", "canceled"},
    "completed": set(), "failed": set(), "canceled": set(),
}
DEFAULT_PATH = Path("artifacts/warwagon-engagements.sqlite3")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class EngagementLedger:
    """Each operation uses its own transaction: safe across threads/processes.

    A global monotonically increasing sequence is used for SSE cursors; event
    identity and deduplication are scoped to each engagement.
    """

    def __init__(self, path: Path | str = DEFAULT_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS engagements (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    target TEXT NOT NULL,
                    model TEXT,
                    state TEXT NOT NULL CHECK(state IN ('created','running','completed','failed','canceled')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS engagement_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id TEXT NOT NULL REFERENCES engagements(id),
                    event_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL CHECK(schema_version = 1),
                    UNIQUE (engagement_id, event_id)
                );
                CREATE INDEX IF NOT EXISTS events_by_engagement_sequence
                  ON engagement_events(engagement_id, sequence);
            """)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(str(self.path), timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("PRAGMA journal_mode=WAL")
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _validate_id(event_id: str) -> None:
        if not isinstance(event_id, str) or not EVENT_ID_RE.fullmatch(event_id):
            raise ValueError("event ID must be a bounded nonblank identifier")

    @staticmethod
    def _validate_event(kind: str, origin: str, payload: dict) -> str:
        if not isinstance(kind, str) or not EVENT_ID_RE.fullmatch(kind):
            raise ValueError("invalid event kind")
        if not isinstance(origin, str) or not EVENT_ID_RE.fullmatch(origin):
            raise ValueError("invalid origin")
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        content = _json(payload)
        if len(content.encode("utf-8")) > 256_000:
            raise ValueError("event payload exceeds 256 KB")
        return content

    @staticmethod
    def _event(row: sqlite3.Row) -> dict:
        # Detect on-disk corruption before exposing an observation as evidence.
        # This unkeyed digest is integrity checking, NOT an authenticity signature.
        raw = row["payload_json"]
        if not isinstance(raw, str) or row["payload_sha256"] != _digest(raw):
            raise ValueError("stored event payload digest mismatch")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("stored event payload is not an object")
        return {
            "sequence": row["sequence"],
            "engagementId": row["engagement_id"],
            "eventId": row["event_id"],
            "kind": row["kind"],
            "origin": row["origin"],
            "payload": payload,
            "payloadSha256": row["payload_sha256"],
            "occurredAt": row["occurred_at"],
            "schemaVersion": row["schema_version"],
        }

    @staticmethod
    def _engagement(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"], "title": row["title"], "target": row["target"],
            "model": row["model"], "state": row["state"],
            "createdAt": row["created_at"], "updatedAt": row["updated_at"],
            "source": "recorded",
        }

    def _insert_event(
        self, db: sqlite3.Connection, engagement_id: str, event_id: str,
        kind: str, origin: str, payload: dict, at: str
    ) -> dict:
        self._validate_id(event_id)
        serialized = self._validate_event(kind, origin, payload)
        digest = _digest(serialized)
        existing = db.execute(
            "SELECT * FROM engagement_events WHERE engagement_id=? AND event_id=?",
            (engagement_id, event_id),
        ).fetchone()
        if existing is not None:
            if (existing["kind"], existing["origin"], existing["payload_sha256"]) != (kind, origin, digest):
                raise ValueError("idempotency key reused with different event content")
            return self._event(existing)
        db.execute(
            """INSERT INTO engagement_events
              (engagement_id, event_id, kind, origin, payload_json, payload_sha256, occurred_at, schema_version)
              VALUES (?,?,?,?,?,?,?,?)""",
            (engagement_id, event_id, kind, origin, serialized, digest, at, SCHEMA_VERSION),
        )
        row = db.execute(
            "SELECT * FROM engagement_events WHERE engagement_id=? AND event_id=?",
            (engagement_id, event_id),
        ).fetchone()
        return self._event(row)

    def create_engagement(
        self, title: str, target: str, *, model: str | None = None,
        engagement_id: str | None = None,
    ) -> dict:
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ValueError("title is required and must be at most 200 characters")
        if not isinstance(target, str) or not target.strip() or len(target) > 2048:
            raise ValueError("target is required and must be at most 2048 characters")
        if model is not None and (not isinstance(model, str) or len(model) > 200):
            raise ValueError("invalid model name")
        eid = engagement_id if engagement_id is not None else "eng-" + uuid4().hex
        self._validate_id(eid)
        now = _now()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    """INSERT INTO engagements(id,title,target,model,state,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?)""",
                    (eid, title.strip(), target.strip(), model, "created", now, now),
                )
                self._insert_event(
                    db, eid, "engagement.created", "engagement.created", "runtime",
                    {"title": title.strip(), "target": target.strip(), "model": model}, now,
                )
                row = db.execute("SELECT * FROM engagements WHERE id=?", (eid,)).fetchone()
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return self._engagement(row)

    def get_engagement(self, engagement_id: str) -> dict:
        self._validate_id(engagement_id)
        with self._connect() as db:
            row = db.execute("SELECT * FROM engagements WHERE id=?", (engagement_id,)).fetchone()
        if row is None:
            raise KeyError("engagement not found")
        return self._engagement(row)

    def list_engagements(self, limit: int = 100) -> list[dict]:
        if type(limit) is not int or limit < 1 or limit > 1000:
            raise ValueError("limit must be 1..1000")
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM engagements ORDER BY created_at DESC,id LIMIT ?", (limit,)
            ).fetchall()
        return [self._engagement(row) for row in rows]

    def append(
        self, engagement_id: str, kind: str, payload: dict, *,
        origin: str = "agent", event_id: str | None = None
    ) -> dict:
        self._validate_id(engagement_id)
        eid = event_id if event_id is not None else uuid4().hex
        now = _now()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT state FROM engagements WHERE id=?", (engagement_id,)
                ).fetchone()
                if row is None:
                    raise KeyError("engagement not found")
                # Idempotent retries remain valid even when the engagement is terminal.
                existing = db.execute(
                    "SELECT sequence FROM engagement_events WHERE engagement_id=? AND event_id=?",
                    (engagement_id, eid),
                ).fetchone()
                if row["state"] in ("completed", "failed", "canceled") and existing is None:
                    raise ValueError("cannot append to terminal engagement")
                event = self._insert_event(db, engagement_id, eid, kind, origin, payload, now)
                db.execute("UPDATE engagements SET updated_at=? WHERE id=?", (now, engagement_id))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return event

    def transition(self, engagement_id: str, new_state: str, *, reason: str = "") -> dict:
        self._validate_id(engagement_id)
        if new_state not in STATES:
            raise ValueError("invalid state")
        if not isinstance(reason, str) or len(reason) > 2000:
            raise ValueError("invalid reason")
        now = _now()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT state FROM engagements WHERE id=?", (engagement_id,)
                ).fetchone()
                if row is None:
                    raise KeyError("engagement not found")
                before = row["state"]
                if new_state not in TRANSITIONS[before]:
                    raise ValueError("invalid lifecycle transition")
                self._insert_event(
                    db, engagement_id, "transition:" + new_state,
                    "engagement." + new_state, "runtime",
                    {"from": before, "to": new_state, "reason": reason}, now,
                )
                db.execute(
                    "UPDATE engagements SET state=?,updated_at=? WHERE id=?",
                    (new_state, now, engagement_id),
                )
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return self.get_engagement(engagement_id)

    def events(self, engagement_id: str, *, after: int = 0, limit: int = 200) -> list[dict]:
        self._validate_id(engagement_id)
        if type(after) is not int or after < 0:
            raise ValueError("cursor must be a nonnegative integer")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("limit must be 1..1000")
        with self._connect() as db:
            if not db.execute("SELECT 1 FROM engagements WHERE id=?", (engagement_id,)).fetchone():
                raise KeyError("engagement not found")
            rows = db.execute(
                """SELECT * FROM engagement_events
                   WHERE engagement_id=? AND sequence>?
                   ORDER BY sequence ASC LIMIT ?""",
                (engagement_id, after, limit),
            ).fetchall()
        return [self._event(row) for row in rows]
