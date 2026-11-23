# Real intelligence milestone — lab agent and executable ARC

**Status:** implementation prototype. This supersedes expanding synthetic benchmark heuristics as WarWagon's active priority.

## Requirements
Python 3.10+ and an actual OpenAI-compatible tool-calling model endpoint. Default targets local Ollama's OpenAI-compatible endpoint `http://127.0.0.1:11434/v1`, or a user-configured HTTPS endpoint. No model, credentials or inference service is bundled.

## Start an actual assessment run
1. Start an OpenAI-compatible model server with a tool-calling capable model.
2. Run:
```bash
export WW_MODEL="your-installed-model"
python -m warwagon.agent --model "$WW_MODEL" --output artifacts/lab-agent-run.json
```
The runner starts a deliberately vulnerable HTTP teaching fixture on `127.0.0.1` with ephemeral port and restricts its tool to the fixture's three paths. It lets the real model select tool calls, inspects returned observations, and records traces and token usage if the model reports it.

The independent fixture verification validates that the issue exists. A separate conservative agent-discovery scorer now requires a concrete reflected HTML tool observation **and** an agent finding statement. This is an early deterministic scoring rule, not a blinded expert verifier or general vulnerability scorer.

## Run actual ARC first-pass reviews
```bash
python -m warwagon.arc --model "$WW_MODEL" --proposal docs/rfcs/RFC-0001-planner-research-v2.md --output artifacts/arc-review.json
```
For separate reviewer models/providers, supply `--reviewers-file config/arc-reviewers.example.json` after replacing the example model IDs with actual installed models and endpoint URLs. Nine separate API calls use isolated message histories, role-specific instructions and the same frozen proposal file. Outputs include exact model name, proposal digest, raw response, usage and prompt digest. These are real calls when an actual provider is configured, but using one model with nine prompts is **not independent-model consensus**. A full council requires diverse independent model/provider runs, blind cross-review, critic synthesis, actual recorded dissent and maintainer approval.

ARC validates each first-pass response against the expected verdicts and four lists.
A failed request or invalid response stays in the artifact under its role, and
later reviewers still run with fresh message histories. The command exits with
status 1 if any role lacks a valid review. Compare `verdict_roles` to locate
disagreement, then read the individual critiques for the reasons behind it.
A single JSON code fence is accepted when it encloses the entire review.
Reviewer profiles use the optional `api_key_env` field to name a credential
environment variable. Profiles without that field make unauthenticated calls.
The single-model mode still uses `WW_MODEL_API_KEY`.
Endpoint hashes identify configured endpoints without exposing full URLs.
Provider-reported model names are recorded when supplied. Multiple endpoint
or model labels alone cannot establish independent model weights.

## Retry a failed ARC reviewer

Pass the original artifact and an unsuccessful role. Use the same proposal
file and choose a new output path. You can select another model or reuse the
reviewer profiles.

~~~bash
python -m warwagon.arc --model "$WW_MODEL" \
  --proposal docs/adr/0001-docs-as-code.md \
  --retry-from artifacts/arc-review.json --retry-role research-skeptic \
  --output artifacts/arc-retry.json
~~~

The retry artifact contains only the new attempt, the prior review record and
the original artifact digest. The command checks the proposal digest before
calling the provider. Its exit status applies to the retried role.

## Assemble an ARC evidence report

~~~bash
python -m warwagon.arc_report artifacts/arc-review.json \
  --retry artifacts/arc-retry.json --output artifacts/arc-report.json
~~~

Supply multiple retry files in parent-first order. The report checks each
retry against the digest and review record of the latest unsuccessful
attempt for that role. It preserves all attempts, groups current valid
verdicts by role, and lists unresolved roles. An invalid response remains
inspectable in its original form. The report is a deterministic evidence
summary. Deliberation and a maintainer decision are separate steps.

## Record an ARC challenge

~~~bash
python -m warwagon.arc_challenge artifacts/arc-report.json \
  --role distributed-systems --field blockers --index 0 \
  --challenger research-skeptic \
  --challenge "The scope of the recovery blocker is unclear." \
  --requested-evidence "List the recovery scenarios and their tests." \
  --output artifacts/arc-challenge.json
~~~

The challenge links the frozen proposal, report, and current review attempt
by digest and identifies the exact list item. It preserves the original text
and requests specific evidence in a separate open record. Roles are
caller-supplied labels. The command neither authenticates a reviewer nor
resolves or rewrites a review.

## Test without a model
```bash
python -m unittest discover -s tests -v
```
Unit tests use a clearly labeled test-double, not an LLM.

## Explicit gaps before we can compare planner intelligence
- Current agent is a **single real-model tool loop**, not four implemented real planning strategies.
- The only available target is a tiny controlled HTML-encoding fixture; no comprehensive web-app assessment functionality.
- A minimal agent-observation scorer is present; independent held-out scoring and robust false-positive evaluation remain pending.
- No durable coordination, multi-agent intelligence, graphical ARC console, model benchmark sample size, or production release.
- ARC dispatch is an executable command, but not a deployed always-on agent service and not a completed council verdict.
- Current results should not be represented as autonomous vulnerability-discovery benchmarks.

## Next benchmark gate
Run the same actual model with a measured fixed token/tool budget through two independently implemented planning strategies, using a sealed observation API and blind scorer. Keep a strong single-agent baseline. Archive full traces and ARC critiques.
