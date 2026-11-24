# WarWagon planning backlogs — imported, not dispatched

This directory contains historical architecture-planning datasets generated before the current real-model-first implementation pivot. They are preserved for long-term scope and traceability.

## Available datasets

| File | Records | Purpose |
|---|---:|---|
| [master-backlog.csv](master-backlog.csv) | 2,000 | WarWagon v0.2 generated capability and engineering plan |
| [master-backlog.jsonl](master-backlog.jsonl) | 2,000 | Same master task records in agent-readable JSONL format |
| [agent-intelligence.csv](agent-intelligence.csv) | 240 | AIA-001 component-level planning tasks |
| [agent-intelligence.jsonl](agent-intelligence.jsonl) | 240 | Same AIA tasks in JSONL format |

**Total unique planned task IDs: 2,240.** These are **planning records, not 2,240 ready GitHub issues**. Many are template-generated tasks with incomplete ownership, rough estimates, and provisional design assumptions. A count is not proof of completeness, correctness or implementation readiness.

## Source provenance

- Master: original WarWagon v0.2 master backlog export (`backlog.jsonl`), 2,000 records; imported with original IDs, descriptions, dependencies, priorities and statuses intact.
- Intelligence: original AIA-001 `agent-intelligence-backlog.jsonl`, 240 records; imported with original IDs, descriptions and dependencies intact.
- CSV files were regenerated from the original JSONL records with the same field names and values. The JSONL files preserve the imported source records.
- Import validated each dataset's unique IDs and that all internal task dependencies reference IDs present in the same dataset. Dependencies in the AIA dataset use semicolons for multi-item references.

## Execution priority

**DO NOT assign tasks from these archived exports automatically.**

The executable queue for coding agents is [../real-intelligence-build.md](../real-intelligence-build.md), supplemented by current GitHub Issues and accepted architecture decisions. In particular, [issue #7](https://github.com/digitalfire/WarWagon/issues/7) describes the Codex real-inference/ARC handoff. Check live issues and git before assuming that task is still pending.

The master export contains early research and governance-oriented tasks, including work superseded by the capability-first pivot. The AIA export contains a stronger emphasis on research specifications than executable model-driven evaluation. Neither should replace the active roadmap.

## Reconciliation before work is dispatched

See the [first reconciliation pass](reconciliation.md) for measured overlaps,
merged evidence, and work to carry forward.

1. Compare candidate work against current `main`, [current-state](../../docs/context/current-state.md), accepted ADRs and active GitHub issues.
2. Mark as **already implemented**, **active**, **needs redesign**, **later**, **duplicate**, or **superseded**; retain original IDs.
3. Add unambiguous code ownership, concrete test commands, acceptance evidence, realistic dependencies and current contract refs.
4. Create or link a GitHub Issue only for ready tasks; populate `issue_url` in a separate, reviewed tracking layer instead of overwriting source history.
5. Have ARC critique high-impact design changes before declaring the architecture accepted.

Do not infer project completion from the original `status: todo` fields. The import preserved historical status rather than reconciling it with current code.
