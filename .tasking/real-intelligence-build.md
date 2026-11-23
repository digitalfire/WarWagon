---
id: BUILD-REAL-INT-001
status: active
updated: 2026-11-23
---
# Capability-first build priority — real intelligence

The deterministic benchmark remains a maintenance smoke test only. New primary work belongs to this plan.

| ID | Priority | Work | Acceptance evidence | State |
|---|---|---|---|---|
| WW-INT-001 | P0 | Real OpenAI-compatible model adapter | Live tool-call transcript + usage from configured provider | Harmless Ollama probe passed; strict response validation and timing merged in PR #14 |
| WW-INT-002 | P0 | Single-agent observe→tool→replan loop | Model-selected tool trace against live local target | Prototype added; live run pending |
| WW-INT-003 | P0 | Pinned isolated vulnerable fixtures | Repeatable reset, observable HTTP API and negative controls | Initial stdlib fixture; pinning/extended targets pending |
| WW-INT-004 | P0 | Evidence-backed independent scorer | Validate agent-discovered evidence; ground truth hidden from agent | Minimal evidence correlation prototype; blind scorer pending |
| WW-INT-005 | P0 | Four real planner implementations | Same model/tool/budget, actual reasoning traces | Not started |
| WW-ARC-001 | P0 | Executable ARC reviewer runner | Nine real isolated model calls with traceable artifacts | Nine roles produced valid live reviews across first passes and retries; run artifacts and failures preserved |
| WW-ARC-002 | P0 | Diverse/blinded reviewer deployment | Multiple distinct model contexts/providers, frozen packet | RTX 5090 profile validated with Qwen and Gemma; label-masked pilot recorded; independent replication pending |
| WW-ARC-003 | P0 | Independent synthesis/dissent protocol | Actual reviews, adversarial cross-exam, human decision | Reports, challenges, evidence responses, integrity checks, and disposition records merged; maintainer decision pending |
| WW-EVAL-001 | P0 | Measured model/tool budgets | Token, tool, latency, communication accounting | ARC attempt, retry, token, and latency accounting by configured model shipped; tool and communication budgets pending |
| WW-EVAL-002 | P0 | First true comparative intelligence benchmark | Real model, held-out fixtures, independent verifier | Blocked by WW-INT-004 and WW-INT-005; live inference preflight passed under WW-INT-001 |
| WW-OPS-001 | P1 | Durable trace persistence and run resumption | Kill/restart integration test | Not started |
| WW-INT-006 | P1 | Extend HTTP/browser/code analyzers | Controlled lab assessment coverage | Not started |

## Current evidence

The [review-index pilot](../benchmarks/arc/review-index-pilot.md) compared
two local reviewers on one frozen architecture proposal. The
[repeatable runner](../benchmarks/arc/README.md) preserves invalid
attempts and produces a model-label-masked packet for assessment.
Broader reviewer-quality claims require fresh cases and independent
judgment. The pilot does not exercise or close the planner benchmark.

See the [implementation snapshot](../docs/context/current-state.md)
for merged changes and evidence, and [issue #7](https://github.com/digitalfire/WarWagon/issues/7)
for the outstanding lab acceptance criterion.

The [offline defensive triage calibration](../benchmarks/triage/README.md)
establishes a severity baseline and separate scoring path for synthetic
alerts. The [first held-out comparison](../benchmarks/triage/held-out-result.md)
measured higher aggregate precision and recall for the evidence-aware
candidate, with one new critical miss on stale approval evidence.
Freshness and scope checks remain open before live use.

## Build-readiness decision
**Start coding now.** Sufficient planning exists for a vertical slice: model adapter, real tool loop, local fixture, review dispatcher. Open architectural decisions should be resolved via short, measured ADRs when a component needs them; do not hold the whole project pending a grand architecture freeze.

## Exit gate
A real model uses tools and supplies a finding with matched supporting observations; a separate scorer confirms a hidden expected weakness; at least two actual strategies are compared with identical budgets; independently instantiated ARC reviewers record evidence and disagreements.
