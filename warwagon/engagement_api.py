"""Loopback-only read API and resumable SSE for durable engagement event history.

No arbitrary execution endpoints. POST remains unsupported in the parent API.
The stream tails the committed SQLite ledger with bounded polling windows.
"""
from __future__ import annotations

import json
import re
import time
from urllib.parse import parse_qs, urlsplit

from warwagon.engagement_store import EngagementLedger

ENGAGEMENT_ROUTE = re.compile(
    r"^/api/v1/engagements(?:/([A-Za-z0-9][A-Za-z0-9_.:-]{0,127})(/events)?)?$"
)
MAX_EVENT_CURSOR = 9223372036854775807


def _cursor(handler, query):
    """Last-Event-ID wins on reconnect, query after= is for initial snapshots."""
    header = handler.headers.get("Last-Event-ID")
    if header is not None and header != "":
        value = header
    else:
        fields = parse_qs(query, keep_blank_values=True, strict_parsing=True)
        if set(fields) - {"after"} or len(fields.get("after", [])) > 1:
            raise ValueError("invalid query parameter")
        value = fields.get("after", ["0"])[0]
    if not re.fullmatch(r"[0-9]{1,19}", value):
        raise ValueError("cursor must be a nonnegative decimal integer")
    number = int(value)
    if number > MAX_EVENT_CURSOR:
        raise ValueError("cursor out of range")
    return number


def _write_sse(handler, event_id=None, kind=None, data=None, comment=None):
    parts = []
    if comment is not None:
        parts.append(": " + comment.replace("\r", "").replace("\n", " "))
    if event_id is not None:
        parts.append(f"id: {event_id}")
    if kind is not None:
        parts.append(f"event: {kind}")
    if data is not None:
        parts.append("data: " + json.dumps(
            data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ))
    handler.wfile.write(("\n".join(parts) + "\n\n").encode("utf-8"))
    handler.wfile.flush()


def serve_engagement_get(
    handler, ledger: EngagementLedger, *,
    stream_seconds: float = 20.0,
    poll_seconds: float = 0.25
) -> bool:
    """True if this request matched an engagement route and was handled."""
    parsed = urlsplit(handler.path)
    if not parsed.path.startswith("/api/v1/engagements"):
        return False
    match = ENGAGEMENT_ROUTE.fullmatch(parsed.path)
    if not match:
        handler.write_json(404, {"error": "not_found"})
        return True
    eid, suffix = match.groups()
    try:
        if suffix == "/events":
            cursor = _cursor(handler, parsed.query)
        elif parsed.query:
            raise ValueError("queries supported only on /events")
        else:
            cursor = None
    except ValueError:
        handler.write_json(400, {"error": "invalid_cursor_or_query"})
        return True

    if eid is None:
        handler.write_json(200, {
            "schemaVersion": 1, "source": "recorded",
            "engagements": ledger.list_engagements(),
        })
        return True
    try:
        item = ledger.get_engagement(eid)
    except KeyError:
        handler.write_json(404, {"error": "engagement_not_found"})
        return True
    if suffix != "/events":
        try:
            snapshot = ledger.events(eid, after=0, limit=1000)
            has_more = bool(snapshot and ledger.events(
                eid, after=snapshot[-1]["sequence"], limit=1
            ))
        except (ValueError, json.JSONDecodeError):
            handler.write_json(422, {"error": "event_integrity_failure"})
            return True
        handler.write_json(200, {
            "schemaVersion": 1, "source": "recorded",
            "engagement": item, "events": snapshot, "hasMore": has_more,
        })
        return True

    if stream_seconds <= 0 or poll_seconds <= 0:
        raise ValueError("stream configuration must be positive")
    # Preflight integrity before sending irreversible SSE response headers.
    try:
        initial = ledger.events(eid, after=cursor, limit=500)
    except (ValueError, json.JSONDecodeError):
        handler.write_json(422, {"error": "event_integrity_failure"})
        return True
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Accel-Buffering", "no")
    handler.send_header("Connection", "close")
    handler.end_headers()
    handler.close_connection = True
    limit_time = time.monotonic() + stream_seconds
    next_heartbeat = time.monotonic() + min(5.0, stream_seconds / 2)
    try:
        _write_sse(handler, comment="WarWagon engagement events v1")
        batch = initial
        while time.monotonic() < limit_time:
            if batch is None:
                batch = ledger.events(eid, after=cursor, limit=500)
            if batch:
                for event in batch:
                    cursor = event["sequence"]
                    _write_sse(handler, event_id=cursor, kind="engagement.event", data=event)
                # Drain big backlogs quickly; avoid sleep between full batches.
                if len(batch) >= 500:
                    batch = None
                    continue
            batch = None
            now = time.monotonic()
            if now >= next_heartbeat:
                _write_sse(handler, comment="heartbeat")
                next_heartbeat = now + 5.0
            # The stream is a finite connection; clients reconnect with Last-Event-ID.
            time.sleep(min(poll_seconds, max(0, limit_time - now)))
    except (ValueError, json.JSONDecodeError):
        # A later event may have been modified after the stream began.
        # Send a terminal error, not an evidence-bearing record or endless retry.
        try:
            _write_sse(handler, kind="stream.error", data={"error": "event_integrity_failure"})
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
    except (BrokenPipeError, ConnectionResetError, OSError):
        # Expected browser disconnect/reconnect. Never mutate the ledger.
        pass
    return True
