# Tasking and autonomous coding-agent workflow

**Active work:** [Real Intelligence Build](real-intelligence-build.md).  
**Long-term archived planning records:** [Full Backlog (2,240 tasks)](backlog/README.md).  
**Additional scoped research:** [Planner research](planner-research-phase-1.md) and [Research queue](research-queue.md).

This directory provides tasking conventions for implementers and AI coding agents. GitHub Issues/PRs are the operational execution queue; specs, contracts, dependencies, and acceptance criteria remain in Git.

## Task fields
`id`, `title`, `status`, `priority`, `workstream`, `depends_on`, `spec_refs`, `file_ownership`, `deliverables`, `acceptance_criteria`, `validation_commands`, `blockers`, `issue_url`, `pr_url`.

## Task lifecycle
Backlog → Triaged → Ready (accepted dependencies and contracts) → Claimed → In progress → Review → Verified → Done. Blocked work records the missing decision. Agent work should be idempotent and scoped to separately owned files.

## Execution contract
Start by reading AGENTS.md and linked accepted specs. Don't implement speculative interfaces as if accepted. Produce tests, documentation and evidence for each change, then open a scoped PR. Never mark a task done based only on a generated summary.

## Immediate work tracks
- Real model invocation and tool-calling reliability
- Local training-fixture security assessment and evidence scoring
- Executable Architecture Review Council with actual reviewer traces
- Head-to-head model-driven planner evaluation and fair budget accounting
- Durable knowledge and state only as required for the live vertical slice

The v0.2 and AIA-001 planning exports are now imported under `backlog/`. They are historical planning data and **not automatically ready for dispatch**; their overlaps, old assumptions, dependencies and statuses still need reconciliation with current implementation.
