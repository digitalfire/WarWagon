# WarWagon documentation

**Documentation as code:** Markdown and Mermaid in Git. This directory is the source of truth for brainstorming, architecture, and future implementation handoffs.

## Start here
- [Project vision](vision.md)
- [System overview](architecture/system-overview.md)
- [Agent intelligence architecture — AIA-001](architecture/agent-intelligence.md)
- [Canonical data model — DATA-001](architecture/canonical-data-model.md)
- [Architecture decisions](adr/README.md)
- [Research notes](research/README.md)
- [RFC proposals](rfcs/README.md)
- [Roadmap](roadmap.md)
- [Tasking conventions](../.tasking/README.md)
- [Coding-agent handoff](../AGENTS.md)

## Lifecycle
Idea → Research note → RFC → ADR → Versioned contract → Work item → PR → Verified benchmark.

## Document states
`idea`, `proposed`, `accepted`, `superseded`, `implemented`. Research and proposals are *not* implementation authority. Accepted ADRs and versioned schemas outrank drafts; conflicting decisions require review.

All architectural docs should identify a stable ID, status, date, dependencies, open questions, and links. Record alternatives and benchmarks, including failed experiments. Do not invent measured outcomes.
