# Offline defensive alert triage baseline

This is an eight-alert synthetic calibration case. It defines a baseline
and a separate scorer to make comparison possible on a fixed alert input.
The severity baseline escalates high and critical alerts. A deferred
alert is a triage decision, with no effect on any live system.

~~~bash
python -m benchmarks.triage.reference baseline benchmarks/triage/fixtures/alerts.json --output artifacts/triage-baseline.json
python -m benchmarks.triage.reference score benchmarks/triage/fixtures/alerts.json artifacts/triage-baseline.json benchmarks/triage/fixtures/labels.json --output artifacts/triage-score.json
~~~

The baseline reads alerts only. The scorer checks exact input digests and
complete ID coverage, then reports the confusion counts, precision,
recall, missed alerts, and false alarms. A ratio without a denominator
is reported as null.

The checked-in labels are visible to maintainers and used for
calibration. For a comparison claim, freeze fresh fixtures and keep
their labels out of candidate inputs. Use the same corpus and scoring
rules for each candidate, then record repeated runs, measured model
cost and latency, and the evidence supporting each escalation.


## Evidence-aware candidate

The candidate uses typed evidence with source labels. Unexpected activity
from two distinct sources triggers escalation, as does a conflict between
an unexpected-activity record and approval or duplicate context. Matching
approval or duplicate records from two distinct sources can defer an
alert. Other cases use the severity baseline. Its decision includes a
reason code and the IDs of the evidence used.

Source labels are caller-supplied. Distinct labels do not establish
independence, freshness, or matching approval scope. This candidate runs
only on local benchmark files.

~~~bash
python -m benchmarks.triage.reference baseline benchmarks/triage/held-out/alerts.json --output artifacts/triage-held-out-baseline.json
python -m benchmarks.triage.reference candidate benchmarks/triage/held-out/alerts.json --output artifacts/triage-held-out-candidate.json
python -m benchmarks.triage.reference score benchmarks/triage/held-out/alerts.json artifacts/triage-held-out-baseline.json benchmarks/triage/held-out/labels.json --output artifacts/triage-held-out-baseline-score.json
python -m benchmarks.triage.reference score benchmarks/triage/held-out/alerts.json artifacts/triage-held-out-candidate.json benchmarks/triage/held-out/labels.json --output artifacts/triage-held-out-candidate-score.json
~~~

See the [held-out result](held-out-result.md) for measured outcomes and
the failure cases.


## Guarded candidate

Run `guarded` with the same alert input and score its decisions as above.
For noncritical alerts, evidence can change severity only when the scope
exactly matches and the timezone-aware timestamp falls within 24 hours
before the alert's observation time, inclusive. The policy excludes
missing, future, stale, or mismatched evidence and records why. Critical
alerts always escalate. Labels and timestamps are caller-supplied data.

See the [fresh held-out comparison](guarded-held-out-result.md) for the
three-strategy comparison and critical-alert gate.


## Analyst review queue

~~~bash
python -m benchmarks.triage.review_queue benchmarks/triage/guarded-held-out/alerts.json artifacts/triage-guarded.json --output artifacts/triage-review-queue.json
~~~

The queue links to the exact alerts and guarded decisions. It surfaces
deferred alerts with unexpected-activity evidence that is eligible but
uncorroborated, too old, or missing the timestamp or alert context needed
to assess it. Future and mismatched-scope records are excluded. Results
are ordered by severity and alert ID. The command does not change the
decision file or escalate an alert.


## Score the analyst queue

Use a fresh alert file to generate guarded decisions and a review queue
with the commands above. Only the final command reads the separate labels.

~~~bash
python -m benchmarks.triage.queue_score benchmarks/triage/queue-held-out/alerts.json artifacts/triage-guarded.json benchmarks/triage/queue-held-out/labels.json artifacts/triage-review-queue.json --output artifacts/triage-queue-score.json
~~~

The score separates analyst workload (number of queued alerts) from miss
coverage (the share of deferred incidents surfaced for review). A queued
incident is still awaiting analyst review. See the
[fresh queue comparison](queue-held-out-result.md).
