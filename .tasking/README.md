# Tasking and autonomous coding-agent workflow

This directory defines how agent-executable tasks are prepared and tracked. GitHub Issues/PRs will eventually be the operational queue; specs, contracts and acceptance criteria remain in Git.

## Task fields
`id`, `title`, `status`, `priority`, `workstream`, `depends_on`, `spec_refs`, `file_ownership`, `deliverables`, `acceptance_criteria`, `validation_commands`, `blockers`, `issue_url`, `pr_url`.

## Task lifecycle
Backlog → Ready (accepted dependencies and contracts) → Claimed → In progress → Review → Verified → Done. Blocked work records the missing decision. Agent work should be idempotent and scoped to separately owned files.

## Execution contract
Start by reading AGENTS.md and linked accepted specs. Don't implement speculative interfaces as if accepted. Produce tests, documentation and evidence for each change, then open a scoped PR. Never mark a task done based only on a generated summary.

## Initial work tracks
- Knowledge/event schema design
- Planner strategy and intent contracts
- Durable runtime and lifecycle
- Reproducible evaluation harness
- Typed adapters and model routing

Prior v0.2 and AIA-001 task exports should be imported only after deduplication and dependency review.
