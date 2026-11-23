# Fresh held-out triage comparison

The [16 synthetic alerts](guarded-held-out/alerts.json) and [labels](guarded-held-out/labels.json)
were authored after freezing the guarded candidate. The same author
prepared both policy and fixtures. All three strategies received identical
alert bytes. Only the scorer read labels.

| Strategy | Precision | Recall | False escalations | Missed alerts | Critical misses |
| --- | ---: | ---: | ---: | ---: | ---: |
| severity-threshold | 55.6% | 62.5% | 4 | 3 | 0 |
| evidence-aware | 42.9% | 37.5% | 4 | 5 | 2 |
| evidence-aware-guarded | 66.7% | 75.0% | 3 | 2 | 0 |

The guarded candidate escalated all four alerts labeled critical in
the input. Three required escalation under the evaluation labels,
and G03 was a false escalation. The original evidence-aware policy
missed G01 and G02 after accepting stale or out-of-scope approvals.
The guard recovered both, and it recovered two high-severity cases
with the same evidence problems.

The guarded policy still missed G08, which had only one current source,
and G14, which had corroboration older than the window. It also
escalated G12 after filtering stale approval. These cases show the tradeoff
of requiring fresh evidence. The critical guard applies to incoming
severity labels and cannot recover cases that were underclassified.
This is an offline synthetic result.

## Reproduce

Run all three policies against `benchmarks/triage/guarded-held-out/alerts.json`
using the [triage CLI](README.md) and distinct decision output files.
Score each one with `benchmarks/triage/guarded-held-out/labels.json`.

Artifact SHA-256 digests:

- Alert input: `93ee578eae83007a50a273468ec05f8f755b1b6e2152e0db417099817cee9369`
- Scoring labels: `e2b03b6a0fe5202feb73008e82cb8f290eda98bdcbe2e8b26238d2e395268f8f`
- Frozen implementation: `791af6b943a85d179f6cfd33759087665ef4e8d024714b20d95d8f102a6a48a4`
- severity-threshold decisions: `6ee14bb87a1a4418b595677323c1cee66b8d3b4d9e0ebb26f7a7d1348f972bb4`
- evidence-aware decisions: `752feab0d6fd0df31da7851b719b0129f3e4c579a26208c009e87052e7610928`
- evidence-aware-guarded decisions: `22f1cfb27794563bed5495047609bc045bfe66b94743792037def7be3ca0bf8e`
