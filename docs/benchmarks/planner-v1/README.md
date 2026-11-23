---
id: BENCH-001
status: proposed
updated: 2026-11-23
---
# Planner benchmark v1 — experimental protocol

This is a specification, not a completed benchmark.

## Design
Run S0 single-agent, S1 hierarchy, S2 blackboard graph and S3 hybrid frontier on the same locally controlled fixtures with *sealed ground truth*. Initial environments use simulated assets and deliberately vulnerable local test services; never public systems.

## Fixture strata
1. **Simple linear** — one obvious prerequisite chain; tests coordination overhead.
2. **Wide branching** — independent discoveries with redundant alternatives; tests parallel exploration.
3. **Deep dependencies** — multi-step linked objectives and prerequisites.
4. **Partial observability** — incomplete and ambiguous observations with required verification.
5. **Contradictory evidence** — stale claims and alternative explanations.
6. **Dynamic state** — fixture changes after a recorded milestone.
7. **Worker failure** — lease expiration, crash, duplicate delivery and restart.
8. **Long context** — evidence too large for one model window; tests retrieval and provenance.

## Parity controls
- Same model/provider/model version, tool schemas, context budget policy, hardware class, allowed actions, fixture reset, hidden truth, model temperature and run seed where supported.
- Same aggregate token/tool budget in one evaluation; separately compare equal wall-time budgets.
- Minimum pilot: 5 seeds per fixture/strategy; design full study sample size after measuring pilot variability.
- Hold out additional test fixtures not exposed to planner prompts or example demonstrations.
- Independent verifier consumes raw evidence, not agent self-assessment, and cannot access answer keys except scoring process.
- Full run manifests and raw event logs are reproducible.

## Required metrics
Unique verified objectives; recall/precision; time-to-first-confirmation; median and variance; overlap and wasted work; message bytes; token cost; model/tool calls; recovery rate; provenance completeness; CI for comparisons where feasible.

## Explicit anti-gaming controls
Keep validation harness and hidden ground truth separate from worker environment; test for answer leakage, leaked benchmark fixture strings, self-reported success without artifact evidence, exploitation of scoring shortcuts, and unstable model versions.

## Failure injection
Duplicate event 10x; delayed message; worker crash before/after tool result; timeout; stale snapshot; two workers claiming same intent; context truncation; evidence corruption; conflicting model outputs.

## Artifacts
Fixture manifest, truth file accessible only to scorer, planner run traces, metrics JSON, environment reset script, comparison notebook/report, randomization record and experiment hashes.

## Decision threshold (proposed)
No architectural promotion on a single demo. A candidate must improve a pre-registered primary metric without materially degrading evidence correctness, and the improvement must replicate across held-out fixture classes. If outcomes are mixed, keep both strategies available and adapt based on task characteristics.
