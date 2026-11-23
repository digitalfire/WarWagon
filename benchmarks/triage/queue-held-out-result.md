# Fresh analyst queue comparison

A separate contributor prepared [12 synthetic alerts](queue-held-out/alerts.json)
and [evaluation labels](queue-held-out/labels.json) after the guarded
strategy and queue policy were merged. They did not run the policy on
the cases before handing them over. Only scoring read the labels.

| Measure | Result |
| --- | ---: |
| Alerts deferred by guarded triage | 10 |
| Incidents among deferred alerts | 5 |
| Alerts added to the analyst queue | 5 |
| Missed incidents surfaced | 3 |
| Benign alerts queued | 2 |
| Miss coverage | 60% |
| Queue precision | 60% |

The queue surfaced Q01, Q03, and Q06. It also surfaced benign Q05 and
Q02. Two missed incidents remained outside the queue. Q04's source
timestamp was ahead of the observation, and Q12 had an unconfirmed
protective-control signal. Later evidence in the synthetic labels
confirmed both incidents. These cases motivate evaluating timestamp
validation and protective-control signal corroboration separately.

Queueing is a request for analyst review. This comparison measures
which alerts were surfaced, with disposition accuracy and review time
still unmeasured. The result is limited to this synthetic set.

Reproduce with the [triage and queue CLIs](README.md). Artifact digests:

- Alerts: `573ec80a3d89fbc0ac0ae3e08bcd310de7a746f287ad52939d0ec4cbe0172793`
- Guarded decisions: `ef9f2e0618825c225c3b88189c1193745686875ac8570cb2e45d3e7038ad7a3c`
- Review queue: `0bd1c3b8a151ec0929d20a533bb11da74efe8910753c21ff6f4006c3337113fb`
- Scoring labels: `6aad217a3c8c95350d4a493d8307ef5ceebbb271cae149c3bf42744ecb64b05e`
