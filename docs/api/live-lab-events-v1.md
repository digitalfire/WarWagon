# WW-LIVE-005 — Real model/tool event producer

The CLI `python -m warwagon.live_lab` runs the **existing local WarWagon training fixture** through an actual configured tool-calling model and appends discrete events as execution proceeds. It does not assess external targets or create verified vulnerability findings.

## Local usage

From repository root, start the read-only API:

```bash
python -m warwagon.console_api --port 8765 --engagement-db artifacts/warwagon-engagements.sqlite3
```

In another terminal run a locally installed Ollama tool-calling model:

```bash
export WW_MODEL=YOUR_INSTALLED_MODEL
python -m warwagon.preflight --model "$WW_MODEL"
python -m warwagon.live_lab --model "$WW_MODEL" --database artifacts/warwagon-engagements.sqlite3
```

The model server defaults to `http://127.0.0.1:11434/v1`. No inference is started by the browser; it occurs only through the explicit CLI command. The fixture HTTP server is loopback-bound and started just for this run.

## Durable event types

- `engagement.created` and `engagement.running`
- `model.response` with provider-reported usage and whether tool calls were selected
- `tool.invocation` with the model-proposed function name and arguments
- `tool.observation` with the actual local HTTP tool result
- `agent.final` or `agent.limit`
- `fixture.oracle.result` (whether the *teaching fixture* contains the expected flaw)
- `agent.discovery.heuristic` (whether the agent's own observed trace and conclusion met the narrow lab scoring rule)
- `run.finished` or `run.failed`
- Terminal `engagement.completed` / `engagement.failed`

The `model.response` event does not expose hidden model reasoning; it records observable invocation metadata. **The fixture oracle does not prove that the model discovered a real-world vulnerability.** The heuristic is explicitly labelled. An execution may complete even if the mission objective was not satisfied; use `run.finished.payload.objectiveSatisfied` for the latter.

The event store is durable across process restarts and can be inspected via `/api/v1/engagements` and streaming `/api/v1/engagements/{id}/events` with `Last-Event-ID` / `?after=N`.

## Local tests

```bash
python -m unittest tests.test_live_lab_events -v
```

These tests use a scripted test double to exercise the complete real HTTP tool contract and verify durable events; they **do not claim model inference occurred in CI**.

## Remaining before full product UX

- React live engagement adapter (#56), separate from illustrative engagements.
- True multi-agent orchestration and worker execution rather than a single tool-calling loop.
- Stronger independent held-out finding verification, scope gates, resource budgets, deployment controls and audit requirements before broader targets.
