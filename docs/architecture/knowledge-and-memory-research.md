---
id: AIA-004
status: research
updated: 2026-11-23
related_rfc: RFC-0001
---
# Knowledge, graph and cognitive memory — research design

## Required distinctions
`Observation` = collected output, potentially unreliable; `Hypothesis` = testable inference; `Assertion` = claimed state with provenance; `VerifiedFact` = claim accepted by explicit validation process; `Finding` = scoped evidence-backed security conclusion.

## Graph projections
Asset graph: assets, services, interfaces, dependencies and identities. Investigation graph: goals, hypotheses, intents, tests and outcomes. Evidence/provenance graph: claim, artifact, collector, validator and counterevidence. No duplicate authoritative source; projections derive from canonical records.

## Five memory scopes
Working: task-local rolling context. Episodic: executed sequences and outcomes. Semantic: verified knowledge and relationships. Procedural: reusable tested methods. Experimental: evaluated variants and benchmark results.

## Research problems
Entity resolution across noisy observations; competing facts; time validity; copy-on-write snapshots; cross-engagement privacy; confidence calibration; relevance vs novelty retrieval; graph query performance; traceability to raw bytes.

## Experiment matrix
Contradictory observations, duplicate asset names, revoked facts, evolving services, memory poisoning inputs, massive graph fan-out, stale embeddings, evidence immutability. Measure retrieval correctness and provenance completeness, not just answer fluency.
