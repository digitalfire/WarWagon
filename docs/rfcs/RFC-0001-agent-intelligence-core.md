---
id: RFC-0001
status: research
owner: unassigned
updated: 2026-11-23
review_gate: G1
---
# RFC-0001 — Pluggable agent intelligence core

## Research question
What architecture maximizes verified investigative discovery under finite compute, with durable coordination and interchangeable reasoning engines?

## Candidate architectures
A. Hierarchical planner with delegated specialist subagents.
B. Fact-intent graph search with asynchronous workers.
C. Hybrid: strategy plugins propose typed candidate intents to a shared opportunity frontier.
D. Single powerful agent with an explicit tool loop as a low-complexity baseline.

## Proposed contracts, subject to review
`Goal`, `KnowledgeSnapshot`, `PlannerProposal`, `Intent`, `Task`, `AgentRun`, `Observation`, `EvidenceRef`, `Verification`, `StrategyEvaluation`.

## Experiments
- Branching investigation fixture with ground-truth findings and alternate paths.
- Controlled single-agent and multi-agent ablation.
- Parallelism=1/2/4/8 while holding total inference tokens and tool budget constant.
- Planner swap with identical knowledge snapshots.
- Worker kill/restart and message duplication tests.
- Verify confirmed findings per dollar, coverage, false positives, duplicates, recovery, action count and variance.

## Review request
ARC roles: intelligence architect, distributed systems architect, evaluation scientist, adversarial reviewer and security research engineer. Require independent first-pass review before synthesis.

## Open decisions
Best planner strategy, partial order of events, cognitive memory retrieval and expiry, fairness strategy for competing planner proposals, and pause/resume semantics.
