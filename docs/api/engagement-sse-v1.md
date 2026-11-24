# LIVE-002 — Read-only live engagement SSE API

This API serves committed events from [LIVE-001](engagement-events-ledger-v1.md), not the existing static fixture replay and **not an assessment execution endpoint**.

## Local startup

```bash
python -m warwagon.console_api --port 8765 --engagement-db artifacts/warwagon-engagements.sqlite3
```

The original `/api/v1/runs` recorded-run viewer remains available. The API now also exposes:

- `GET /api/v1/engagements` — recorded engagement metadata from SQLite
- `GET /api/v1/engagements/{id}` — engagement and first 1,000 ordered events
- `GET /api/v1/engagements/{id}/events?after=N` — SSE stream of committed events with cursor-based replay

For SSE, each event has `id: <global SQLite sequence>`, `event: engagement.event` and JSON `data`. Clients should keep the last fully processed sequence and reconnect with `Last-Event-ID` or initial `?after=N`. The header takes precedence on reconnect. The cursor is a global sequence, **not** contiguous within an individual engagement; gaps are expected.

Streams poll for newly committed rows and close after a bounded interval (default 20 seconds). Browsers can reconnect automatically; clients must deduplicate events by event ID/sequence. Heartbeat comments contain no data and must not be counted as observations. Only committed SQLite rows are sent; events are not synthesized.

The endpoint is local loopback only, read-only, and does not create, start or control engagements. The first live lab runner is a separate milestone.

## Tests

```bash
python -m unittest tests.test_engagement_api -v
python -m unittest discover -s tests -v
```

These cover concurrent external event producer, cursor replay, malformed cursors, route coexistence with the previous recorded-run API and read-only enforcement. Use a temporary ledger file for all tests.

## Delivery considerations

- API should remain behind the local Vite development proxy for initial testing.
- Before exposure beyond localhost: authentication, authorization, backpressure, stronger input validation, bounded streams/client connections, redaction and auditing are needed.
- Inference/runtime events can include sensitive data; do not expose this dev server to the network.
- Explicitly distinguish **agent observation**, **unverified hypothesis**, and **independently verified finding** in all API projections.
