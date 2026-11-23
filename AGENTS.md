# WarWagon coding-agent instructions

Read in order: docs/README.md, docs/vision.md, docs/architecture/agent-intelligence.md, docs/architecture/canonical-data-model.md, docs/adr/README.md, docs/roadmap.md, .tasking/README.md.

Do not treat research notes or proposed ADRs as accepted decisions. Do not create incompatible parallel data models. Before work, identify exact spec revision, task ID, dependencies, files owned, acceptance criteria, and verification commands. Prefer small PRs; include tests, docs, known limitations, and exact evidence of completion. No claims of test execution unless actually run.

Coordinate parallel agents by distinct file ownership and versioned interfaces. Record blockers as issues or notes, never silently change contracts. Preserve reproducible logs, source provenance, and independent validation. Only run security tests in expressly authorized environments.
