---
id: AIA-003
status: research
updated: 2026-11-23
related_rfc: RFC-0001
---
# Planning and opportunity frontier — research design

## Principle
The planner produces *proposals*, not irreversible tool commands. Selection occurs in a shared frontier where novelty, evidence quality, expected information gain, dependency readiness, costs and strategy diversity can be compared.

## Candidate strategy interfaces
```text
PlannerStrategy.propose(goal, knowledge_snapshot, budget, history)
  -> proposals[], assumptions[], rationale_refs[]
OpportunityFrontier.select(proposals, in_flight_tasks, dependencies, capacity)
  -> selected[], deferred[], rejected[]
```

## Proposed proposal fields
ID, objective ID, strategy ID and version, hypothesis/asset refs, preconditions, expected evidence, target specialist capabilities, estimated token/tool/time cost, novelty fingerprint, uncertainty, priority justification, termination condition, provenance, dependencies.

## Portfolio selection hypotheses
- Diversity-aware selection may outperform greedy top score.
- Repeated or low-information attempts should be down-ranked without permanently suppressing changed conditions.
- Context reuse might increase performance but introduce stale beliefs; track snapshot revisions.
- Planner tournaments are only meaningful under equal test budgets and blinded ground truth.

## Failure/ablation tests
Duplicate proposals, contradictory agent conclusions, stale graph projection, objective drift, budget exhaustion, dynamic change during execution, slow planner, no valid candidate actions.

## Unresolved choices
Ranking objective and weight learning, fairness across tasks, online vs offline strategy selection, confidence calibration, stochastic exploration and human steerability.
