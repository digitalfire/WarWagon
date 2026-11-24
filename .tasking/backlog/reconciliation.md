# Backlog reconciliation

Reviewed against main at `7e885e5` on November 23, 2026. The [active build
plan](../real-intelligence-build.md) remains the execution roadmap.

## What the archive count means

The master archive contains 2,000 IDs across 200 work packages. The AIA
archive contains 240 IDs across 80 epics. Each CSV matches its JSONL
counterpart by ID and field values. The two JSONL archives share zero IDs.
All 2,240 records have the historical status `todo`.

Every master package has two repeated-title pairs. The `PROTO` and
`DATA` rows share a title, as do `SPIKE` and `BUILD`. These account for
400 repeated titles spanning 800 rows. The pairs have different
acceptance criteria. When a package is promoted, keep each relevant
criterion under one issue for the deliverable and retain the source IDs.
Split the work only where separate dependencies or ownership warrant it.

## Reconcile before dispatch

| Source overlap | Merged evidence | Remaining work |
|---|---|---|
| ARC first-pass and dissent tracking (`RES-108`, `WW-R211`, `WW-R212`) | First-pass reviews, recovery, challenges, evidence responses, and dispositions exist. [ARC status](../../docs/context/current-state.md) · [Checkpoint recovery](https://github.com/digitalfire/WarWagon/pull/37) | Follow-up quality evaluation on fresh frozen proposals and independent judgments. [Paired scorecards](https://github.com/digitalfire/WarWagon/pull/40) |
| Hybrid planner (`WW-00-03`, `WW-AIA-03-03`, `WW-R205`), planner comparisons (`RES-101`, `WW-R209`, `WW-R214`), and leakage prevention (`RES-107`, `WW-R207`, `WW-R208`) | The simulated comparison already provides a regression baseline. [Planner benchmark](../../docs/benchmarks/planner-v1/README.md) | One held-out protocol for a benign model-driven comparison, with equal budgets, scorer-only labels, and comparable results for two strategies. |
| Evidence integrity (`WW-10-08`, `WW-AIA-06-06`) | The benign verifier binds verdicts to inputs and rejects unsupported, incomplete, or contradictory claims. [Verifier provenance](https://github.com/digitalfire/WarWagon/pull/39) · [Negative controls](https://github.com/digitalfire/WarWagon/pull/41) | Promote only new integrity requirements with a concrete acceptance case. The existing checks cover the fixed-route fixture. |
| Defensive triage | Offline strategy and queue comparisons exist. Live Wazuh ingestion passed on a controlled file change. [Triage results](../../benchmarks/triage/README.md) | Assemble a labeled real-alert corpus before claiming real-telemetry triage quality. Triage effectiveness and production integration are separate milestones. |

## Issue 7 handoff

[Issue #7](https://github.com/digitalfire/WarWagon/issues/7) is the only
open GitHub issue at this review. Live preflight, actual ARC calls, CI, and
a bounded HTTP evidence test are recorded. The issue still calls for a
model-driven vulnerability-assessment result with independent evidence,
or a precise environment blocker. The fixed-route HTTP test establishes
tool selection and evidence verification within its own scope.
See the [recorded fixture run](../../benchmarks/evidence_fixture/README.md).

If the handoff is split, link a successor that carries the outstanding
criterion before closing the umbrella as superseded. Record the evidence
already delivered and preserve the outstanding status in the successor.
