# LIVE-001 — Durable engagement event ledger

**Status:** implementation slice, SQLite-backed event storage. This is **not** a distributed agent scheduler or an active assessment service.

## Schema and guarantees
- `EngagementLedger(path)` creates an append-only, SQLite WAL event store.
- Each engagement stores its ID, title, target descriptor, optional model, lifecycle state, timestamps and source=`recorded`.
- Each event has immutable `sequence` (global, monotonically increasing), `engagementId`, per-engagement `eventId` (idempotency key), `kind`, `origin`, `payload`, `payloadSha256`, timestamp and `schemaVersion=1`.
- Events are appended through `BEGIN IMMEDIATE` transactions and are durable across process restarts.
- Repeating an event ID with bytewise canonical-equivalent content returns the original event; an event ID with conflicting content raises an error.
- `events(engagement_id, after=cursor, limit=N)` reads strictly newer events in canonical sequence order. A global cursor can have gaps for a particular engagement; consumers must compare `sequence > cursor`, not expect increments of exactly one.
- State transitions are `created -> running -> completed|failed|canceled`, with created allowed to be failed or canceled. Invalid transitions fail without modifying persistent state. No new events may be appended to terminal engagements; retrying an already committed event remains safe.
- Events preserve the original observation payload. They are **not** proof that a hypothesis or a vulnerability is verified. Separate verification records and evidence bindings will be necessary.

## Test

```bash
python -m unittest tests.test_engagement_store -v
python -m unittest discover -s tests -v
```

## Parallel work ownership

The event ledger contract is delivered for [#54](https://github.com/digitalfire/WarWagon/issues/54).

Other independent work packages:
- [#55](https://github.com/digitalfire/WarWagon/issues/55): SSE streaming API and cursor reconnect; imports this module and does not rewrite storage.
- [#56](https://github.com/digitalfire/WarWagon/issues/56): React actual engagement event adapter and Investigation Console display; depends on #55 SSE response.
- [#57](https://github.com/digitalfire/WarWagon/issues/57): independent tests and review.

A future real local lab runner must persist its own actual model/tool observations to the ledger. No autonomous execution or model inference is implied by creating an event store.
