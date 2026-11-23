---
id: CONTEXT-STATE-001
updated: 2026-11-23
status: snapshot
---
# Project implementation status and evidence

This snapshot reflects GitHub state checked while preparing Codex handoff. Verify `main` and Actions status again when starting work.

## Merged milestones
- PR #1: README, documentation tree, AGENTS.md, ADR/RFC conventions.
- PR #2: architecture review council proposal, research standards, intelligence research documents.
- PR #3: planner research RFC and benchmark design.
- PR #4: deterministic four-heuristic reference benchmark, unit tests, CI. **Synthetic only.**
- PR #5: Python OpenAI-compatible LLM client, single-agent tool-calling loop, localhost HTML output-encoding teaching fixture, minimal evidence scoring, nine-role ARC dispatcher, tests, roadmap.
- PR #6: tool arguments may be object or JSON string; normalized for replay; real-model preflight, local PowerShell runbook and regression tests.

As of this snapshot PR #6 was merged to `main` at commit `3e5d306b192cda566f8d9bcdedc44f47ace49084`.

## Run commands (from repository root)
```bash
python -m unittest discover -s tests -v
python -m warwagon.preflight --model YOUR_INSTALLED_TOOL_CAPABLE_MODEL
python -m warwagon.agent --model YOUR_INSTALLED_TOOL_CAPABLE_MODEL --output artifacts/lab-agent-run.json
python -m warwagon.arc --model YOUR_INSTALLED_TOOL_CAPABLE_MODEL --proposal docs/rfcs/RFC-0001-planner-research-v2.md --output artifacts/arc-review.json
```
Default model URL: `http://127.0.0.1:11434/v1`; override with `WW_MODEL_BASE_URL`. Exact model tag must match what is installed.

## What passed
GitHub Actions unit test workflows, including mock model and fixture behavior, were observed successful for PR #5 and PR #6. PR #4 ran the deterministic simulation benchmark in CI.

## What has NOT yet been demonstrated
- No verified **live real-model** assessment trace from the developer's Ollama server was produced in this chat.
- No real ARC reviewer verdicts have been captured; the nine role definitions and dispatcher are not a completed council.
- No blind, held-out general vulnerability scoring.
- No genuine four-strategy LLM planner head-to-head.
- No durable multi-agent coordination, production intelligence graph or deployed UI.
- No benchmark result substantiates real-world assessment superiority.

## Blockers and dependencies
1. A working tool-calling inference endpoint accessible to the execution environment (user already runs Ollama locally, but its model/GPU configuration was not provided).
2. Capture a live `preflight` result and an agent run with actual HTTP observations; diagnose compatibility, model performance or tool-use failures based on the trace.
3. Record actual ARC runs with independent contexts and where possible separate models/providers.
4. Build held-out locally controlled fixtures and a scorer that only awards claims supported by agent-observed evidence.
5. Implement distinct real model-driven planners and comparable budget accounting.

## Important caveat
A fixture-oracle confirmation means the vulnerability exists in the teaching app; it does **not** by itself mean the agent found it. `agent_discovery_score` is a minimal heuristic and must not be treated as scientifically valid independent verification.
