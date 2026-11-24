"""Persist completed ARC review attempts across process restarts."""

from contextlib import contextmanager
import json
import sqlite3


@contextmanager
def open_checkpoint(path, manifest):
    path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(path, timeout=1)
    try:
        with database:
            database.execute("BEGIN IMMEDIATE")
            database.execute(
                "CREATE TABLE IF NOT EXISTS manifest (id INTEGER PRIMARY KEY CHECK (id = 1), document TEXT NOT NULL)"
            )
            database.execute(
                "CREATE TABLE IF NOT EXISTS attempts (role TEXT PRIMARY KEY, document TEXT NOT NULL)"
            )
            expected = json.dumps(manifest, sort_keys=True)
            row = database.execute("SELECT document FROM manifest WHERE id = 1").fetchone()
            if row is None:
                database.execute("INSERT INTO manifest VALUES (1, ?)", (expected,))
            elif row[0] != expected:
                raise ValueError("checkpoint belongs to a different ARC proposal or reviewer configuration")
        yield database
    finally:
        database.close()


def get_or_record(database, role, invoke):
    # Hold a write transaction through the call to serialize competing resumptions.
    with database:
        database.execute("BEGIN IMMEDIATE")
        row = database.execute("SELECT document FROM attempts WHERE role = ?", (role,)).fetchone()
        if row is not None:
            record = json.loads(row[0])
            if (
                not isinstance(record, dict)
                or record.get("role") != role
                or record.get("status") not in ("valid", "request_failed", "invalid_response")
            ):
                raise ValueError(f"checkpoint contains an invalid attempt for {role}")
            return record, True
        record = invoke()
        database.execute("INSERT INTO attempts VALUES (?, ?)", (role, json.dumps(record)))
        return record, False
