---
id: PLAN-INT-001
status: planning
updated: 2026-11-23
---
# Real intelligence engineering milestones and illustrative schedule

This is **engineering planning**, not a promise that agents will continue working autonomously between conversations. Work requires an active developer/agent runtime and available model inference.

## Gate 0 — runnable research prototype (current PR)
Python model adapter, tool-calling loop, local vulnerable fixture, trace capture, minimal evidence scoring, executable role-isolated ARC review runner and CI. No live provider inference has yet run from this environment.

## Gate 1 — actual model smoke run (suggested 1–3 engineering days after a working tool-calling model endpoint is connected)
Perform model selection, run against local fixture, inspect full tool trace, log inference use, resolve model API compatibility. Run nine ARC reviewer calls with frozen proposal and record separate first-pass outputs. This is a software exercise, not an external target assessment.

## Gate 2 — credible single-agent evaluation (suggested 3–7 additional engineering days)
Introduce held-out locally controlled fixtures, blind scorer and claim/evidence schema; add 10+ varied problems, repeated runs and real cost accounting. Distinguish model luck and fixture memorization.

## Gate 3 — first true comparative planner benchmark (suggested 1–3 additional engineering weeks)
Implement at least hierarchical and blackboard planners using one common observation and tool contract, keep strong single-agent baseline, compare equal token/tool/time limits, report variance and fault/recovery cases. Hybrid is added only if distinct planning approaches earn it.

## Gate 4 — production architecture (later, conditional)
Choose persistence, durable workflow system, agent queues, knowledge graph representation, isolation architecture and full model router based on benchmark evidence and workload.

## Architecture decision budget
No need to wait for full architecture agreement to code Gate 0/1. Resolve only: model/tool API, run trace schema, evidence/claim contract, fixture/scorer interface, ARC review record format. Everything else can remain RFC/experimental.

## Staffing caveat
Intervals are indicative engineering effort, not calendar commitments. Model availability, upstream interface changes, agent implementation quality and independent review can significantly change durations.
