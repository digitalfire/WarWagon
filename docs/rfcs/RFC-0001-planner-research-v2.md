---
id: RFC-0001
revision: 2
status: research
updated: 2026-11-23
review_gate: G1
decision: none
---
# RFC-0001 — Planner and Multi-Agent Coordination Research (Revision 2)

> Research proposal only. No planner, coordination topology, or scheduler is accepted.

## 1. Research objective
Determine what architecture delivers the greatest *verified discovery value* on partially observable, branching security research tasks under finite compute, time, and tool budgets. A planner is assessed on actual reproducible outcomes and costs, not how convincing its reasoning sounds.

### Primary research question
For a set of held-out, authorized test fixtures, how do single-agent, hierarchical, shared-blackboard and hybrid-frontier approaches compare in verified outcomes, cost, reliability, and information sharing?

### Hypotheses (not findings)
- H1: Fact-intent search can improve coverage on tasks with independent branches and useful persistent discoveries.
- H2: Hierarchical planning can improve performance on tightly coupled tasks with long dependency chains.
- H3: Hybrid scheduling may dominate on heterogeneous tasks, but can suffer the largest coordination overhead.
- H4: A strong single-agent baseline can win on simpler tasks and must remain a production-capable fallback.
- H5: Better task deduplication and causal state tracking can increase useful work at fixed inference budgets.

## 2. Compared systems
**S0 Single agent:** one model context, serial tool use, same eligible tools and memory retrieval budget. No hidden privileged access.

**S1 Hierarchical:** one persistent task planner, specialized delegated workers, explicit dependency DAG, planner-controlled replan triggers.

**S2 Fact-intent graph:** agents claim eligible intents from shared state, publish observations and candidate facts, then propose further exploration; avoid reliance on a central role planning every step.

**S3 Hybrid:** multiple planning strategies generate typed proposals against a common snapshot, shared frontier selects a portfolio based on utility and diversity, scheduler assigns workers.

All strategies consume the same versioned environment interface, capability manifest, observation/evidence records and budget-accounting API.

## 3. Correctness and value metrics
**Primary:** Verified unique objectives completed / fixed benchmark budget, and verified finding recall against sealed ground truth.

**Secondary:** precision, time-to-first-verified, cost per verified outcome, distinct paths, coverage, failed actions, number of wasted duplicate tasks, cross-agent knowledge reuse, plan divergence, recovery success, false-positive severity, and evidence provenance completeness.

**Coordination overhead:** model tokens and wall time spent on agent communication, redundant deliberation, coordination state contention and duplicated work relative to useful verified actions.

**Critical:** measure wall-clock-equal and total-token-equal experiments separately. Parallelism can reduce wall clock while consuming more aggregate resources.

## 4. Architecture invariants
- A planner only proposes work. Scheduler owns the task lifecycle.
- Observation, asserted claim, and independently verified fact are distinct data types.
- A specialist can challenge or contradict another agent without rewriting history.
- Every decision is correlated with knowledge snapshot ID, planner version and model invocation ID.
- Task duplication is observable and measured; dedup is probabilistic with inspectable override.
- Worker leases and retry keys prevent accidental duplicate scheduling; external action idempotence is not assumed.
- A rejected hypothesis remains retrievable as historical evidence without becoming a planning fact.

## 5. Interface research
Draft port boundaries: `PlannerStrategy`, `FrontierSelector`, `TaskScheduler`, `KnowledgeSnapshotProvider`, `EvidenceVerifier`, `EvaluationRecorder`.

Planner inputs: goal, eligible capabilities, immutable knowledge revision, time/tool/token budgets, active tasks, historical outcome summary.

Planner outputs: zero or more proposals containing ID, claim/hypothesis dependencies, expected information gain, prerequisites, relevant asset/evidence refs, novelty fingerprint, predicted cost, target specialist capabilities, stop condition, model rationale refs.

Scheduler output: selected/deferred/rejected decision, lease reservation, causal event and reason code. No direct tool execution by planners.

## 6. Alternatives and competing designs
- Centralized vs decentralized knowledge synchronization.
- Event-driven replan vs periodic polling vs hybrid trigger thresholds.
- Greedy utility vs Pareto frontier vs diversity-constrained portfolio.
- Optimistic concurrency and per-task leases vs a strong centralized sequencer.
- Explicit graph nodes vs document blackboard + graph projections.
- Shared embeddings vs independent per-agent memories with reconciled factual summaries.

## 7. Failure and adversarial analysis
Speculative facts becoming evidence; conflicting entity identities; looping plans; self-reinforcing confirmation bias; context poisoning; parallel duplicate work; lost messages; temporary partitions; stale snapshots; planner domination; budget starvation; high model variance; benchmark memorization; incomplete observations; worker crash after an external side effect.

## 8. Research gates
G1 literature and sources; G2 independent architecture critique; G3 benchmark plan reviewed and fixture ground truth sealed; G4 local reference implementations; G5 repeated runs and significance report; G6 ADR decision by maintainer.

## 9. Questions to resolve
1. How should two conflicting hypotheses coexist in the frontier?
2. What constitutes a causally meaningful new fact and triggers replanning?
3. Can the planner identify useless parallelism before launching workers?
4. What is the canonical unit for novelty and information gain?
5. How much specialized memory should transfer between engagements?
6. Does a frontier become a hidden centralized bottleneck?
7. Can we distinguish task success due to model intelligence vs coordination strategy?

## 10. Requested reviewers
Agent intelligence, distributed systems, knowledge/data, evaluation scientist, security research, inference engineer, adversarial critic, research skeptic. All must review without seeing each other's initial opinions before synthesis; independence must be demonstrated with real run metadata.

## 11. Acceptance
No acceptance without runnable isolated fixtures, a sealed test set, documented baseline parity, independently recorded criticisms and quantitative runs. Source documents are maintained in docs/research and docs/reviews.
