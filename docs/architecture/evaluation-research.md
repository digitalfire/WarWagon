---
id: AIA-005
status: research
updated: 2026-11-23
related_rfc: RFC-0001
---
# Evaluation and agent improvement — research design

## Goal
Measure whether an intelligence component genuinely increases *verified* outcomes and reduces wasted reasoning.

## Experiment unit
Versioned fixture + reset recipe + ground-truth manifest + model/provider configuration + tool capability matrix + seeds + limits + immutable run trace + scoring version.

## Core metrics
Verified finding recall, precision, distinct paths discovered, false positives, agent overlap, tokens/time/tool cost, recovery after failures, provenance completeness, planner-selection regret, reproducibility, test side effects.

## Baselines and ablations
Single-agent tool loop; hierarchical planner; fact-intent explorer; hybrid frontier; without shared graph; without memory; without parallel workers. Keep total tokens and wall-clock windows separately controlled and report both.

## Evaluation requirements
No hidden reuse of benchmark answers; use held-out fixtures, multiple runs, replayable traces and confidence intervals where feasible. Independent verifier must not receive the planner's desired conclusion as fact.

## Promotion
Experimental → replicated research → shadow → canary → accepted strategy only after recorded measurements and council review. Reject claims of improvement based only on agent-generated narratives.
