---
proposal: RFC-0001
status: review-pending
updated: 2026-11-23
---
# Independent reviewer assignments — pending

No autonomous review agents have been deployed or completed an independent review. These are reviewer instructions for a future run.

## Shared review packet
- docs/rfcs/RFC-0001-agent-intelligence-core.md
- docs/rfcs/RFC-0001-planner-research-v2.md
- docs/architecture/planner-strategy-contract-v0.md
- docs/benchmarks/planner-v1/README.md
- docs/research/planner-literature-2026-11.md
- docs/governance/architecture-review-council.md

## Roles and assigned questions
- **Intelligence architect:** Are our cognitive architectures meaningfully distinct? What planner strategies are missing?
- **Distributed systems architect:** Can we recover intent and task state without double-running side-effecting work?
- **Knowledge architect:** Can graph semantics avoid circular evidence and propagate contradictory claims?
- **Security research engineer:** Do fixtures resemble long-horizon authorized investigation without letting tool integration dominate?
- **Evaluation scientist:** Can runs attribute improvements causally? How much repetition is needed?
- **Inference engineer:** How do model heterogeneity and context compression change ranking?
- **Adversarial reviewer:** Find the most severe exploit of planner/benchmark assumptions.
- **Research skeptic:** Identify undocumented claims, unclear citations and missing baselines.

## Independent-run procedure
Each specialist gets a clean isolated context with the same frozen repo SHA and review packet, but not other specialist verdicts. Record model ID, prompt digest, source commit, timestamp, observed evidence and verdict. Only after all first passes are complete may synthesis compare reviews. A single-model role-playing simulation must be labeled as such.

## Exit criteria
At least one actual review per mandatory perspective, dissent record, reproducible experimental proposal and maintainer resolution of blockers before an ADR can be accepted.
