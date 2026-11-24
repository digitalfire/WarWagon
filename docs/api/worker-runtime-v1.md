# WW-LIVE-006 — Two-agent local lab runtime

**Purpose:** Execute two separate, model-driven specialist investigations in parallel on WarWagon's existing loopback-only training application, with durable task ownership and shared resource accounting. This is deliberately **not** a production distributed scheduler or arbitrary-target pentesting launcher.

## Run

From repository root, with the existing local Ollama model server running:

```bash
python -m warwagon.preflight --model YOUR_INSTALLED_TOOL_MODEL
python -m warwagon.console_api --port 8765
```

In another terminal:

```bash
python -m warwagon.worker_runtime \
  --model YOUR_INSTALLED_TOOL_MODEL \
  --workers 2 \
  --model-calls 20 \
  --tokens 100000 \
  --seconds 120 \
  --max-steps 8 \
  --http-rps 30
```

Open the React UI and select **Live Engagement Events**. The runtime creates a single persisted engagement with two distinct lab tasks (mapping and HTML-output-encoding assessment). Both workers use the same shared SQLite budget and the same rate limiter. The model chooses actual HTTP tool calls; execution produces task/claim/model/tool/observation/lab-oracle events. Results are not scripted when the live model CLI is used.

## Worker contract

- Tasks: `queued → running → completed|failed|blocked` with immutable task ID and goal.
- Atomic `BEGIN IMMEDIATE` lease claims ensure one worker owns a task at a time. Reclaimed expired leases get an incremented attempt.
- Heartbeats renew leases while inference is running. A superseded worker is fenced from committing events or terminal state. A process crash eventually releases the lease through timeout.
- SQLite task mutation and corresponding event append are performed in **the same transaction**, preserving audit lineage without a write gap. This prototype uses the ledger's internal transactional event writer; a stable public repository interface should replace this coupling later.
- Shared call reservations are hard-capped and charged before model invocation. Failed model calls still consume a reservation.
- Reported token consumption is debited after a model response. **Token cap is soft at the individual in-flight model-call boundary:** one or two concurrent calls can exceed remaining reported tokens, because the model provider exposes actual usage only after completion. No further calls are reserved after the reported threshold. Unknown provider usage is marked `usageComplete=false`, never reported as zero verified consumption.
- Shared HTTP rate limit applies to all workers in this process; it is a 1-second sliding window, not a cluster-wide/global limiter.
- The engagement time deadline is checked before reserving model calls. A call already in flight can finish after the deadline.
- Worker tasks are predefined local-lab specialist goals. A planner that dynamically creates its own task DAG and model recovery checkpoints are not yet implemented. A restarted task would rerun from its goal; current CLI creates a new engagement rather than automatically resuming a prior model context.

## Demonstrated testing

```bash
python -m unittest tests.test_worker_runtime -v
python -m unittest discover -s tests -v
```

Tests use **scripted model test doubles**, not real LLM inference. They validate actual local HTTP tool invocation, simultaneous workers, atomic lease claims, stale-lease fencing, crash-window reclaim, call-budget contention, token accounting and failure events.

The runtime records the fixture's independent oracle separately from the agent's narrow trace-derived heuristic. No general finding should be called independently verified based only on a fixture oracle.

## Next gates

1. Replace fixed task goals with versioned agent-generated IntentProposals and a held-out scorer.
2. Add resumable model context/checkpoint and durable outbox without internal ledger coupling.
3. Enforce strict token limits with provider-specific output controls and per-call reservations.
4. Scale limits across processes/machines, implement true cancellation and task retry policy.
5. Execute actual two-agent runs against an installed local model and compare with single-agent baseline under equal budgets.
