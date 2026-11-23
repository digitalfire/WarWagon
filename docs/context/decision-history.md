---
id: CONTEXT-DECISIONS-001
status: historical-summary
updated: 2026-11-23
---
# Why WarWagon is being built this way

This file preserves salient decision rationale from planning discussions; the detailed source of authority remains code, ADRs and git history.

## 1. The name and independent ownership
The project is **WarWagon**, published under **digitalfire**. Alternative names were rejected. It is not an Akrithen corporate product.

## 2. Agent intelligence is the core product
The design originally described operations console, intelligence core, specialized agent adapters, shared knowledge/evidence, and isolated execution. The maintainer chose to prioritize the **agent intelligence architecture** as the differentiator: reasoning, shared facts/intent, agent collaboration, model selection, memory, planner strategy comparison, verification and self-improvement through experiments.

## 3. Capability-first, not governance-first
Earlier specifications spent too much time on authorization boundaries, approvals and controls. The maintainer explicitly redirected work toward technical capability and extensibility. Keep essential testing authorization, execution isolation and provenance, but do not turn these into the research agenda.

## 4. Docs-as-code first
The maintainer chose Git-tracked **Markdown** rather than a separate wiki. Files should support architecture brainstorming, research, RFCs, ADRs, implementation plans, task dependencies and agent handoff. PR #1 established the docs structure.

## 5. Expert review council, not self-approval
The maintainer requested a team of specialist agents to challenge our architecture before it is final. PR #2 described roles and review evidence; PR #5 implemented separate model-call review dispatch. **Separate prompts to one model are not independently validated consensus.** Actual review results and dissent must be saved before claiming conclusions.

## 6. Competing planners, no premature winner
Candidates: (S0) strong single-agent tool loop; (S1) hierarchical delegation; (S2) fact-intent/shared-blackboard graph; (S3) hybrid frontier of planner strategies. It remains an open research question which is better or when each is appropriate. Benchmarks must normalize model/tool access, aggregate budget, evidence and fixture parity.

## 7. Synthetic benchmark was a stepping stone, not the product
PR #4 added deterministic scheduling proxy trials and CI. The maintainer challenged this because it does **not** measure LLM reasoning or penetration-testing performance. Decision: **stop adding synthetic benchmark features as the main workstream**; retain them only as regression tests. Build real model tool use, controlled lab assessments, blind scoring and actual comparative planners.

## 8. First implementation stack is provisional
PR #5 introduced a Python standard-library prototype and local Ollama-compatible API, a deliberately vulnerable localhost fixture, scoring, ARC runner, and CI. ADR-0003 is **proposed**, not accepted as the future production stack. Go control plane, PostgreSQL/graph systems, Temporal, React UI, Kubernetes etc. remain open for later decisions based on evidence.

## 9. Bottleneck is real inference evidence
PR #6 added model preflight and tool-call argument normalization. Next priority: prove actual model-generated tool calls, locally observed HTTP behavior, evidence-supported claims, and real reviewer responses. Do not use mock tests or fixture-oracle checks to claim agent intelligence.

## 10. Reasons to retain a strong single-agent baseline
Multi-agent overhead, duplicate tasks, benchmark leakage, retrieval/graph maintenance and planner-selection biases could overwhelm gains. Architectural complexity must earn its cost with held-out comparisons, not diagrams.

## Acceptance principle
No planning strategy becomes the default until a real-model head-to-head comparison, independent evidence scoring, reviewed experiment protocol and maintainer approval. Preserve alternatives and dissent.
