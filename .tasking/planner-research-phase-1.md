---
id: PLAN-RESEARCH-001
status: ready-for-research
updated: 2026-11-23
---
# Planner and coordination research: phase 1 task register

These are tasks for future coding/research agents, not completed work. An agent may claim only work with satisfied dependencies.

| ID | Work | Input | Deliverable | Completion criterion |
|---|---|---|---|---|
| WW-R201 | Pin upstream AntiFox/ARTEX and Cairn revisions | RES-201 | revision-specific architecture comparison | file and symbol references checked |
| WW-R202 | Detailed single-agent baseline | RFC-0001 | baseline state and memory design | parity with multi-agent tools |
| WW-R203 | Hierarchical strategy design | RFC-0001 | task DAG semantics and planner trigger | reviewed failure cases |
| WW-R204 | Blackboard strategy design | RFC-0001 | fact-intent lifecycle and claim protocol | contradiction tests defined |
| WW-R205 | Hybrid frontier design | RFC-0001 | utility + novelty + portfolio algorithm candidates | fairness and budget analysis |
| WW-R206 | Scheduler contract options | AIA-002 | lease/idempotency alternatives | crash window analysis |
| WW-R207 | Benchmark fixture manifest | BENCH-001 | fixture schema and reset contract | reproducible seed plan |
| WW-R208 | Benchmark ground truth isolation | BENCH-001 | scorer boundary and leak test | scorer-only truth accessible |
| WW-R209 | Equal-cost evaluation protocol | BENCH-001 | cost accounting rules | fixed-budget verification |
| WW-R210 | Failure injection matrix | BENCH-001 | fault scripts and expected invariants | recovery behavior specified |
| WW-R211 | Independent expert review first passes | GOV-001 | signed/identified reviews | review context recorded |
| WW-R212 | Critical synthesis | WW-R211 | dissent + decision matrix | no synthetic consensus |
| WW-R213 | Mock strategy contract prototype | CONTRACT-PLANNER-001 | deterministic mock strategy runners | test suite green |
| WW-R214 | Ablation harness | WW-R207/209/213 | 4-strategy equal-budget execution | raw trace and metrics |
| WW-R215 | ADR candidate recommendation | WW-R212/214 | provisional architecture decision | maintainer review pending |

## Dispatch order
Run R201–R210 in parallel where dependency-free. R211 follows frozen RFC packet; R212 follows reviews; R213 after contract critique; R214 after fixtures and baseline implementations; R215 after experiments. No mass autopopulation of thousands of GitHub issues yet.

## Agent PR checklist
Reference task ID, upstream version/hash where applicable, alternatives considered, exact reproducibility steps, synthetic fixture artifacts, tests actually executed, and review status.
