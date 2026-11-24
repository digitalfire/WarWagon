# WarWagon planner benchmark — reference harness v0.1

This runnable **synthetic simulator** compares four scheduling *heuristics*, NOT four real AI-agent systems. It is the initial infrastructure validation milestone toward BENCH-001 and RFC-0001. It should not be cited as evidence of relative real-world security testing performance.

## Run locally (Python 3.10+, no dependencies)
From repository root:

```bash
python -m unittest discover -s tests -v
python -m benchmarks.planner.reference --seeds 5 --budget 16 --workers 4 --output planner-results.json
```

The output contains 160 runs (8 fixture names × 5 seeds × 4 strategies) with deterministic trace digests. The JSON is a local artifact; do not commit large results to Git. CI should execute the same checks.

## What this validates
- Uniform action-budget ceilings, fixture seeds and output format.
- Strategy-specific candidate-ranking decisions.
- Deterministic trace reproducibility.
- Basic action, event, and time accounting.
- Simple regression testing and repeatable experiment CLI.

## Important limitations
- The strategies are **ranking proxies**: not AntiFox, ARTEX, Cairn, PentAGI, Strix, or real LLM agents.
- No API calls, models, tools, actual vulnerabilities, external targets, independent verification, or measured inference costs.
- `verified` is a *synthetic oracle state* from seeded generated nodes, not external evidence.
- Nodes and scores are available to ranking rules; this is not realistic partial observability. Fixtures share a generator and are not yet independently designed benchmark environments.
- Message counts are approximations; failed worker actions are counted under the current `retries` placeholder but **not retried**.
- One lane for single-agent vs multiple lanes for others means elapsed ticks are not an equal-compute throughput comparison. Action counts are capped equally; coordination cost is not deducted from budget.
- No statistically meaningful claims are supported by these preliminary runs.

## Research steps before meaningful benchmark results
1. Define sealed, independent fixture manifests and an objective observable state API.
2. Implement a shared event ledger and replayable planner strategy interface.
3. Replace heuristic proxies with actual planners under identical model/tool budgets.
4. Account for all planning, coordination and inference costs.
5. Support hidden ground truth, independent verification, failure recovery and held-out cases.
6. Perform independent ARC review and preregister comparison metrics.

See [benchmark methodology](../../docs/benchmarks/planner-v1/README.md) and [RFC-0001](../../docs/rfcs/RFC-0001-planner-research-v2.md).

See [benign service-health scoring](health.md) for the live Docker calibration
and the independent artifact scoring contract.
