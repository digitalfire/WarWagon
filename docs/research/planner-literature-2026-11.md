---
id: RES-201
status: research
updated: 2026-11-23
evidence_level: E1
---
# Planner and multi-agent architecture source dossier (Nov 2026)

These are public source/documentation claims, not independent WarWagon benchmarks.

## AntiFox / ARTEX
Official AntiFox documentation describes a global asset graph, task exploration graph, an event-triggered planner and multiple workers. Design lesson: asset truth and task progress may be separate views, but shared event updates need consistent revision semantics. We should reproduce behavior rather than assume the architecture is superior.
- https://github.com/AntiFox-AI/antifox/blob/main/README.en.md
- https://github.com/AntiFox-AI/antifox

## Cairn
Official Cairn README and paper describe a shared blackboard with explicit fact-intent state-space exploration. Design lesson: separating confirmed facts from future intents can make decentralized task selection inspectable.
- https://github.com/oritera/Cairn
- https://arxiv.org/abs/2609.32700

## Multi-agent benchmark evidence
ProtocolBench (ICML 2026) evaluates protocol choices along success, latency, communication overhead and failure robustness. It supports including communication cost and fault tolerance in WarWagon's scoring — not a specific winning planner.
- https://proceedings.mlr.press/v306/du26l.html

'Capable language models can outgrow the benefits of collaboration' (Nature Machine Intelligence, 2026) reports scenarios where agent coordination loses advantages as individual models become more capable. Implication: retain a strong single-agent baseline and use task-adaptive coordination.
- https://www.nature.com/articles/s42256-026-01268-y

'Worse Together' (2026 preprint) finds coordination failures in shared-resource, multi-user multi-agent settings; its domain isn't penetration testing, so extrapolation requires caution.
- https://arxiv.org/abs/2610.00583

MultiAgentBench (ACL 2025) advocates milestone-based multi-agent collaboration metrics.
- https://aclanthology.org/2025.acl-long.421/

## Runtime recovery
Temporal documents replay-based durable workflows, with determinism requirements. This is a research candidate, not approval for Temporal.
- https://docs.temporal.io/durable-execution

## Confidence and gaps
Evidence is E1 for claims about third-party repositories and papers reviewed through their public descriptions. E2+ requires checked-out pinned revisions, tests and reproduced measurements. No independent run was performed here. Open questions include model confounds, benchmark contamination, language/framework differences, and fair tool parity.
