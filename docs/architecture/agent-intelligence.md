---
id: AIA-001
version: 1.0-draft
status: proposed
updated: 2026-11-23
depends_on: [ARCH-001, DATA-001]
---
# Agent Intelligence Architecture (AIA-001)

WarWagon is a **persistent intelligence substrate with interchangeable planners, models and execution engines**, not a collection of disconnected LLM chats.

## Cognitive cycle
**Observe → Orient → Hypothesize → Propose → Rank → Delegate → Execute → Verify → Learn → Replan.**

Each transition emits versioned, traceable state. Models make proposals; separately owned services enforce task and knowledge lifecycle.

## Components
| Component | Responsibility |
|---|---|
| Goal compiler | Convert outcome to testable objective and stop conditions |
| Planner strategy host | Run hierarchical, fact-intent or hybrid strategies |
| Opportunity frontier | Rank novelty, information gain, cost, diversity; deduplicate |
| DAG scheduler | Resolve dependencies, leases, retries, cancellation and recovery |
| Agent runtime | Run specialist cognitive turns and checkpoints |
| Context compiler | Build bounded, provenance-aware model context |
| Model router | Select provider/model using quality, cost, latency and capabilities |
| Knowledge service | Store observations, hypotheses, verified claims, graph edges |
| Verification engine | Confirm, reject or mark inconclusive candidate findings |
| Evaluation service | Compare planners and model configurations on identical fixtures |

## Intelligence strategy
Planning input: `Objective`, versioned `KnowledgeSnapshot`, specialist capabilities, budget, prior outcomes.
Planning output: `IntentProposal[]` with prerequisites, expected observations, uncertainty, novelty, resource estimate and stop condition.

Competing planner strategies run behind one contract. Compare with identical environment state, seed, time budget, model configuration and scoring criteria. Avoid assuming additional agent count improves quality.

## Agent communication
Typed envelopes: `PROPOSE`, `OBSERVE`, `CHALLENGE`, `DELEGATE`, `REQUEST_VERIFICATION`, `HANDOFF`, `COMPLETE`. Each contains stable event ID, schema version, sender, destination, correlation/causation IDs, evidence refs, expiry and acknowledgment policy. Assume at-least-once delivery and idempotent consumption.

## Memory taxonomy
- Working: active bounded task context.
- Episodic: historical runs and outcomes.
- Semantic: provenance-linked accepted claims and asset relationships.
- Procedural: tested plans, methods and tool usage.
- Experimental: benchmark trials, parameters and statistical comparisons.

Distinguish hypotheses from verified facts in every retrieval result. Context compilation must record exact revisions and citation pointers.

## Runtime state
`created → queued → leased → running → checkpointed → completed|failed|canceled`.
Worker failure must reconcile external side effects before retry. Record checkpoints, artifact digests, task lineage and model/provider versions.

## Evaluation milestone
Against a reproducible local fixture: three cooperating agents propose nonduplicate work; two planners produce comparable traces; one grounded finding is independently verified; a killed worker resumes without losing history; reports include all event and evidence references.

## Next design contracts
PlannerStrategy, AgentEnvelope, KnowledgeSnapshot, TaskLease, Observation, EvidenceArtifact, FindingVerification, ModelInvocation, BenchmarkManifest. Schemas and testing fixtures are pending.
