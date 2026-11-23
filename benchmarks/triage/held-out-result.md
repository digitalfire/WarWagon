# Held-out defensive triage comparison

Both strategies used the exact same [16 synthetic alerts](held-out/alerts.json).
Only the scorer received the [labels](held-out/labels.json). The candidate
implementation was frozen before authoring and running this case set.
The same author prepared policy and fixtures; the cases were held out
from tuning and were not independently curated.

| Strategy | True positives | False positives | True negatives | False negatives | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| severity-threshold | 4 | 4 | 4 | 4 | 50.0% | 50.0% |
| evidence-aware | 5 | 2 | 6 | 3 | 71.4% | 62.5% |

The candidate recovered H03 and H07, which the severity-only rule missed.
It avoided three false escalations (H01, H08, H11) and introduced one
(H09) by escalating conflicting evidence. It also missed H15, a critical
alert the baseline would escalate. Two sources agreed on an approval
whose scope was stale. Both strategies missed H04 and H13, where the
initial evidence had only one distinct source.

These results describe this synthetic comparison only. The H15
regression blocks using the deferral rule in a live workflow without
evidence freshness and scope checks. Preserve this result when testing
that improvement on fresh cases.

Reproduction commands are in the [triage runbook](README.md).
SHA-256 digests:

- Alert input: `828dcecb3de90594f5469908b6478e639dcc34cc013e8e9f9f1391aee61aca84`
- Scoring labels: `ba94dc0a269273eefabe57d8ba768253be7fc260589e58fbd58ea861b8cbc181`
- Frozen reference implementation: `d5471c9e4e25c5ce92217ab5f193f868f9b491d2332cdf1270ffcbae871e3a33`
- Baseline decisions: `c69b2526ae5baf3d1b6185f4053493bf2d4477da43937258c7b266bcfd4fcec5`
- Candidate decisions: `b21ea33e84c1769f1c924c7fe3db586914241f626d26ae340c225be9b49ef336`
