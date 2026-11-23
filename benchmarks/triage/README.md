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
