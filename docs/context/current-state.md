---
id: CONTEXT-STATE-001
updated: 2026-11-23
status: snapshot
---
# Project implementation status and evidence

This snapshot covers `main` at `a795615` after PR #16. The [active queue](../../.tasking/real-intelligence-build.md) sets execution priorities. The imported [planning backlog](../../.tasking/backlog/README.md) preserves historical task records. Check GitHub and Actions again when starting work.

## Merged milestones
- PR #1: README, documentation tree, AGENTS.md, ADR/RFC conventions.
- PR #2: architecture review council proposal, research standards, intelligence research documents.
- PR #3: planner research RFC and benchmark design.
- PR #4: deterministic four-heuristic reference benchmark, unit tests, CI. **Synthetic only.**
- PR #5: Python OpenAI-compatible LLM client, single-agent tool-calling loop, localhost HTML output-encoding teaching fixture, minimal evidence scoring, nine-role ARC dispatcher, tests, roadmap.
- PR #6: tool arguments may be object or JSON string; normalized for replay; real-model preflight, local PowerShell runbook and regression tests.

- [PR #9](https://github.com/digitalfire/WarWagon/pull/9) added ARC response validation, scoped credentials, and per-role failure records.
- [PR #10](https://github.com/digitalfire/WarWagon/pull/10) added single-role retries linked to the original artifact and frozen proposal.
- [PR #11](https://github.com/digitalfire/WarWagon/pull/11) added a deterministic ARC report that preserves attempts and groups current verdicts by role.
- [PR #12](https://github.com/digitalfire/WarWagon/pull/12) imported 2,240 historical planning records and retained the active execution queue.
- [PR #13](https://github.com/digitalfire/WarWagon/pull/13) records provider-reported ARC model labels and optional fingerprints alongside configured labels.
- [PR #14](https://github.com/digitalfire/WarWagon/pull/14) validates the harmless structured probe and records response metadata and elapsed time.
- [PR #15](https://github.com/digitalfire/WarWagon/pull/15) added challenge records linked to a specific ARC review item.
- [PR #16](https://github.com/digitalfire/WarWagon/pull/16) added evidence responses linked to exact challenge bytes and explicitly supplied files.

## Run commands (from repository root)
```bash
python -m unittest discover -s tests -v
python -m warwagon.preflight --model YOUR_INSTALLED_TOOL_CAPABLE_MODEL
python -m warwagon.agent --model YOUR_INSTALLED_TOOL_CAPABLE_MODEL --output artifacts/lab-agent-run.json
python -m warwagon.arc --model YOUR_INSTALLED_TOOL_CAPABLE_MODEL --proposal docs/rfcs/RFC-0001-planner-research-v2.md --output artifacts/arc-review.json
```
Default model URL: `http://127.0.0.1:11434/v1`; override with `WW_MODEL_BASE_URL`. Exact model tag must match what is installed.

## Verification and recorded evidence

- Both GitHub Actions workflows passed on the reviewed commits for PRs #9–#16. The prototype workflow uses unit tests with test doubles and fixture checks. The planner reference workflow measures deterministic simulation behavior. [Prototype CI for PR #16](https://github.com/digitalfire/WarWagon/actions/runs/45272804067) · [Planner reference CI for PR #16](https://github.com/digitalfire/WarWagon/actions/runs/45272804116)
- A live Ollama 0.33.2 preflight with Qwen `qwen3.8:27b` returned the expected harmless structured `report_probe` call with 351 reported tokens. The local handoff artifact is `ollama-preflight.json`. It establishes tool-call compatibility for that probe.
- Live ARC smoke runs reviewed [ADR-0001](../adr/0001-docs-as-code.md). The multi-model first pass recorded eight valid `conditional` verdicts and one invalid research-skeptic response from `llama3:latest`. A targeted retry with `qwen2.5:32b-instruct-q4_K_M` returned a valid `conditional` verdict. The report retained both attempts and showed nine current `conditional` verdicts with zero unresolved reviewer roles. The local handoff artifacts are `arc-pr9-review.json`, `arc-pr9-retry.json`, and `arc-report.json`.
- An additional live ARC retry recorded provider-reported model `qwen3.8:27b` and fingerprint `fp_ollama` in `arc-identity-smoke.json`. Provider labels and fingerprints are attribution metadata. Model-weight identity and independent consensus remain unverified.
- An offline smoke test linked `arc-challenge.json` to the recorded ARC report, then linked an authored evidence response to the exact challenge and ADR-0001 bytes. The challenge stayed open, and the response documented that the ADR alone did not provide both requested example commit histories. A maintainer disposition is still pending.

These local artifacts were preserved in the Codex handoff workspace. Reproduction commands and artifact semantics are in the [prototype runbook](../prototypes/real-agent-and-arc.md).

## Outstanding acceptance and dependencies

[Issue #7](https://github.com/digitalfire/WarWagon/issues/7) remains open. The live preflight and ARC smoke runs establish working inference access and traceable review outcomes. The issue still requires a recorded model-driven lab run with observable tools and independently matched evidence, or a precise documented environment blocker. Neither was recorded at this snapshot.

- Blind held-out assessment scoring and comparative model-driven planner evidence remain outstanding. The deterministic benchmark continues to serve as a regression check.
- ARC has recorded first-pass reviews, retries, and evidence-linked challenges and responses. Independent model-weight identity, a disposition for the recorded challenge, and a maintainer decision remain outstanding.
- Durable multi-agent coordination, a production intelligence graph, and a deployed UI remain roadmap items.

## Important caveat
A fixture-oracle confirmation means the vulnerability exists in the teaching app; it does **not** by itself mean the agent found it. `agent_discovery_score` is a minimal heuristic and must not be treated as scientifically valid independent verification.
