---
id: GOV-001
status: proposed
updated: 2026-11-23
---
# Architecture Review Council (ARC)

## Purpose
Conduct independent, adversarial technical review of WarWagon proposals. The objective is stronger capability, extensibility, reproducibility and technical correctness, not automatic agreement. The council is a **proposed review workflow**, not an assertion that any autonomous reviewers are presently running.

## Review roles
| Role | Required critique |
|---|---|
| Principal Agent Intelligence Architect | cognition loop, planner diversity, autonomy, failure modes, multi-agent coordination |
| Distributed Systems Architect | message delivery, idempotency, durability, replay, scheduling, concurrency |
| Knowledge and Data Architect | canonical semantics, provenance, graph ontology, consistency, queries |
| Offensive Security Research Engineer | realism, coverage, tool fidelity, experimental fixtures, evidence validity in authorized labs |
| AI/ML Evaluation Scientist | datasets, ablations, leakage, baseline parity, confidence, statistical validity |
| Model and Inference Engineer | context design, routing, local inference, cost/quality tradeoffs |
| Plugin and Developer Experience Engineer | versioning, API/SDK design, interoperability, contributor experience |
| Adversarial Reviewer (Red Team) | attack assumptions, prompt injection risks, hallucinations, critical failure scenarios |
| Research Editor / Skeptic | sources, factual verification, missing alternatives, unsupported conclusions |

Assign independent models or isolated agent contexts where possible; a set of role prompts applied to one model does not establish independent consensus. Evidence must be inspectable.

## Submission
Every RFC includes a question, success metric, candidate approaches, source references, interface sketch, threats to validity, impact, reversible path and falsifiable experiment.

## Review workflow
1. **Author** produces a proposal and benchmark hypothesis.
2. **Independent reviewers** submit separate review notes without seeing each other's initial verdicts.
3. **Adversarial challenge** tests strongest counterexamples and forces alternative designs to be articulated.
4. **Synthesis editor** records agreements, disagreements and unresolved factual claims.
5. **Prototype/benchmark** compares candidates with identical controlled conditions where applicable.
6. **Decision authority** (maintainer for now) accepts, rejects or requests revision; reviewers advise, they do not self-approve.
7. **Revisit trigger** defined for future contradictory evidence.

## Review gates
- G0 Idea: unconstrained brainstorming welcome; no implementation authority.
- G1 Research ready: citations, alternatives and hypothesis recorded.
- G2 Design review ready: contracts, failure modes, metrics and review notes.
- G3 Experimental: isolated prototype and reproducible data.
- G4 Accepted ADR: decision owner approval with traceable evidence.
- G5 Implementation ready: versioned contract, task dependencies and test criteria.

No technology is automatically required because of popularity or documentation claims.

## Scoring rubric (1–5 each)
- Capability ceiling and extensibility (25%)
- Measurable correctness and evidence quality (20%)
- Scalability, reliability and recovery (15%)
- Interoperability and modularity (15%)
- Experimental rigor / reproducibility (15%)
- Engineering cost and maintainability (10%)

Scores inform debate; a critical unresolved correctness failure blocks acceptance even when average scores are high. Document minority opinions.

## Mandatory review artifacts
`docs/reviews/<rfc-id>/<role>.md`, `synthesis.md`, `evidence.md`, and decision link. Agent-written reviews carry model/provider, prompt revision, context and date. Never invent reviews or mark a proposed design as approved without recorded reviewer output.
