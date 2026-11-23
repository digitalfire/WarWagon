---
id: CONTEXT-CODEX-001
updated: 2026-11-23
status: active-handoff
related_issue: 7
---
# Codex next action: real intelligence and ARC

## Start
Repository: `digitalfire/WarWagon`.
Primary task: [GitHub issue #7](https://github.com/digitalfire/WarWagon/issues/7).
Read: `AGENTS.md`, `docs/context/README.md`, `docs/context/project-charter.md`, `docs/context/decision-history.md`, `docs/context/current-state.md`, `docs/prototypes/local-setup.md`, `.tasking/real-intelligence-build.md`.

## Current progress

Issue #7 preserves the original acceptance order. The live inference
preflight has passed. ARC has produced structured reviews, retries, and
evidence-linked artifacts, and the reviewer pilot has one graded case.
The [active queue](../../.tasking/real-intelligence-build.md) and
[verified snapshot](current-state.md) track completed evidence and
remaining work. The live model-driven lab acceptance criterion remains
open.

## Original execution order from issue #7
1. **Preflight real LLM**. Discover actual model/API runtime availability, run preflight and capture model/version/usage or record precise environment blocker. Don't substitute mock success.
2. **Real lab agent**. Run against loopback training application. Confirm actual model-selected tool calls, observations and evidence-backed output. Keep trace and non-secret run manifest; distinguish fixture oracle from credited discovery.
3. **Real ARC**. Run nine isolated first-pass review roles. When available, allocate distinct models or providers, record source commit/prompt/outputs and disagreement. Do not imply external domain experts or independent consensus if the same model answers all prompts.
4. **First meaningful comparison**. Add a second genuine model-driven planning strategy, sealed fixture evaluation, independent evidence matcher, equal model/tool budgets and actual run summary. Keep S0 baseline. Don't spend cycles optimizing synthetic heuristics.
5. **Reviewable PRs and tasking**. Update docs and implementation status with actual observed results, tests and limitations. Keep architectural decisions reversible and proposed until evidence and maintainer review.

## Outputs to hand back
- Copyable local setup and preflight troubleshooting.
- Real model invocation record or explicit blocker.
- Local lab assessment trace and evidence/verification results.
- ARC review record and synthesis of actual observed dissent, without fabricated scores.
- First runnable real-model comparison manifest if ready.
- Small linked PRs with test evidence.

## Deliberate non-goals now
- Building full operations dashboard.
- Large Go/Kubernetes/Temporal infrastructure rewrite.
- Declaring a winner among AntiFox, Cairn or WarWagon using proxy tests.
- Unreviewed mass creation of thousands of issues.
- Proving a full autonomous penetration tester through one deliberately vulnerable teaching endpoint.

## Working philosophy
Capability-first, open-source, strong execution evidence, independently challenged decisions, maintainers retain approval, build in small vertical slices. Ask for human action only if a real blocker exists (model/server access, required credentials, hardware, ownership approval).
