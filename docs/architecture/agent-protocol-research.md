---
id: AIA-002
status: research
updated: 2026-11-23
related_rfc: RFC-0001
---
# Agent communication protocol — research design

## Design objective
Support autonomous specialists collaborating across multiple workers, models and machines without losing provenance or confusing hypotheses with facts.

## Envelope draft
```json
{
  "schema_version": "0.1.0",
  "event_id": "uuid",
  "event_type": "intent.proposed",
  "engagement_id": "uuid",
  "task_id": "uuid",
  "agent_run_id": "uuid",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "created_at": "RFC3339 timestamp",
  "payload_ref": "content-addressed reference",
  "context_revision": 1,
  "idempotency_key": "stable key"
}
```

## Categories
- Objective events: proposed, decomposed, satisfied, abandoned.
- Intent events: generated, challenged, selected, rejected.
- Task events: created, blocked, leased, heartbeat, checkpoint, completed, failed, canceled.
- Knowledge events: observed, asserted, disputed, verified, superseded.
- Model events: invocation requested, completed, errored, budget exceeded.
- Evaluation events: fixture started, score reported, strategy promoted.

## Semantics under investigation
At-least-once delivery with consumer deduplication; optimistic revision control on derived knowledge; append-only causal event log with materialized projections. Need to test whether ordered per-task streams and cross-task causal links are sufficient. Avoid promising globally ordered delivery.

## Acceptance experiments
Reordered events, duplicates, partition recovery, revoked leases, schema migration, delayed verification, worker crash during external tool execution.

## Non-goals for this document
No vendor-specific broker choice. No normative wire schema until RFC decision and peer review.
