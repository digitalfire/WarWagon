---
id: DATA-001
status: proposed
updated: 2026-11-23
---
# Canonical data model

The model must stay framework-agnostic and support durable agent collaboration.

| Entity | Meaning |
|---|---|
| Engagement | assessment context and objectives |
| Asset | subject being examined |
| Goal | measurable outcome, constraints and stopping rule |
| Hypothesis | falsifiable claim and uncertainty |
| IntentProposal | candidate work unit and estimated value |
| Task | dependency, scheduling, lease and state |
| AgentProfile / AgentRun | agent capability version and execution history |
| Observation | untrusted tool/model output with source |
| EvidenceArtifact | immutable digest and retrieval pointer |
| FactAssertion | claim, provenance and verification status |
| GraphEdge | typed relationship |
| Finding | evidence-backed disposition and affected asset |
| ModelInvocation | model settings, context, outputs and usage |
| Experiment | benchmark fixture and observed measurements |
| EventRecord | append-only causal state transition |

**Common fields:** stable ID, schema version, timestamp, revision, origin, correlation and causation IDs, engagement identity where applicable, evidence references where required.

**Invariants:** observations don't automatically become facts; findings require independent verification; model confidence alone isn't evidence; state transitions are recoverable; all API schemas are versioned; original evidence is not silently rewritten.

## Outstanding
SQL DDL, graph ontology, merging rules, event semantics, indexes, retention, projections, fixtures, compatibility tests.
