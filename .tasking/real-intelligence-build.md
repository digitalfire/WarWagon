---
id: BUILD-REAL-INT-001
status: active
updated: 2026-11-23
---
# Capability-first build priority — real intelligence

The deterministic benchmark remains a maintenance smoke test only. New primary work belongs to this plan.

| ID | Priority | Work | Acceptance evidence | State |
|---|---|---|---|---|
| WW-INT-001 | P0 | Real OpenAI-compatible model adapter | Live tool-call transcript + usage from configured provider | Prototype added; live run pending |
| WW-INT-002 | P0 | Single-agent observe→tool→replan loop | Model-selected tool trace against live local target | Prototype added; live run pending |
| WW-INT-003 | P0 | Pinned isolated vulnerable fixtures | Repeatable reset, observable HTTP API and negative controls | Initial stdlib fixture; pinning/extended targets pending |
| WW-INT-004 | P0 | Evidence-backed independent scorer | Validate agent-discovered evidence; ground truth hidden from agent | Minimal evidence correlation prototype; blind scorer pending |
| WW-INT-005 | P0 | Four real planner implementations | Same model/tool/budget, actual reasoning traces | Not started |
| WW-ARC-001 | P0 | Executable ARC reviewer runner | Nine real isolated model calls with traceable artifacts | First-pass validation, per-role failure records and verdict attribution implemented |
| WW-ARC-002 | P0 | Diverse/blinded reviewer deployment | Multiple distinct model contexts/providers, frozen packet | Not started |
| WW-ARC-003 | P0 | Independent synthesis/dissent protocol | Actual reviews, adversarial cross-exam, human decision | Evidence-linked first-pass report implemented; cross-exam and decision pending |
| WW-EVAL-001 | P0 | Measured model/tool budgets | Token, tool, latency, communication accounting | Partial; runtime token usage recorded |
| WW-EVAL-002 | P0 | First true comparative intelligence benchmark | Real model, held-out fixtures, independent verifier | Blocked by 004/005/001 |
| WW-OPS-001 | P1 | Durable trace persistence and run resumption | Kill/restart integration test | Not started |
| WW-INT-006 | P1 | Extend HTTP/browser/code analyzers | Controlled lab assessment coverage | Not started |

## Build-readiness decision
**Start coding now.** Sufficient planning exists for a vertical slice: model adapter, real tool loop, local fixture, review dispatcher. Open architectural decisions should be resolved via short, measured ADRs when a component needs them; do not hold the whole project pending a grand architecture freeze.

## Exit gate
A real model uses tools and supplies a finding with matched supporting observations; a separate scorer confirms a hidden expected weakness; at least two actual strategies are compared with identical budgets; independently instantiated ARC reviewers record evidence and disagreements.
