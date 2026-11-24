# Benign service-health scoring

This calibration covers a narrow part of WW-INT-004 and WW-EVAL-002.
It checks whether a reported HTTP status is backed by the correct
observation and matches a separately configured service. The fixed
operation is an unauthenticated `HEAD /` on IPv4 loopback, with redirects
disabled. It uses the [existing probe](../../warwagon/http_probe.py) and
[Docker fixture](../evidence_fixture/README.md).

## Artifact contract

All four JSON artifacts contain their respective `kind` and
`"schema_version": 1`. Digests are lowercase SHA-256 of exact file bytes.

| Artifact kind | Fields | Producer |
|---|---|---|
| `planner_health_case` | `services` maps service IDs to distinct loopback port numbers | Benchmark owner |
| `planner_health_evidence` | `case_sha256`, `observations` list of unmodified probe records | Trusted benchmark harness |
| `planner_health_submission` | `case_sha256`, `evidence_sha256`, `claims` mapping each service ID to a `status_code` and a zero-based `observation_index` | Benchmark harness from planner claims |
| `planner_health_labels` | `case_sha256`, `status_by_service` mapping each case service to its configured status | Benchmark owner, scorer access only |

The benchmark owner freezes the case and labels before a run. The planner
receives the service IDs and ports, and the observations returned by its
calls. The harness owns the evidence file and supplies the final digests.
A valid digest binds a claim to the evidence file. Its authenticity
depends on the harness keeping that file outside the planner's write
access. Keep labels and fixture configuration outside planner context and
tool access. Reserve different cases for evaluation after developing
strategies with calibration cases.

~~~bash
python -m benchmarks.planner.score_health --case case.json --evidence evidence.json --submission submission.json --labels labels.json --output score.json
~~~

Precision is verified claims divided by submitted claims, including
claims about unexpected services. Recall is verified claims divided by
case services. Run status is unscorable if a valid observation conflicts
with the frozen configuration. The scorer retains per-service verdicts
and suppresses precision and recall in that case. A missing observation,
wrong-service reference, bad status claim, or failed probe earns no credit.

## Live Docker calibration

The existing fixture defaults to HTTP 204. Setting `FIXTURE_HEAD_STATUS`
to 200 or 503 selects other benign responses. Publish only to loopback.
For example, build one image and run two isolated instances:

~~~bash
docker build -t warwagon-planner-health:local benchmarks/evidence_fixture
docker run --detach --name health-cal-a --publish 127.0.0.1:48740:8080 --read-only --cap-drop ALL warwagon-planner-health:local
docker run --detach --name health-cal-b --publish 127.0.0.1:48741:8080 --read-only --cap-drop ALL --env FIXTURE_HEAD_STATUS=503 warwagon-planner-health:local
python -m warwagon.http_probe --port 48740 --output alpha-probe.json
python -m warwagon.http_probe --port 48741 --output beta-probe.json
~~~

Package the two probe objects as `observations` in the evidence file and
run the scorer against separately prepared labels. On November 23, 2026,
the two Docker logs recorded 204 and 503. Handwritten calibration claims
scored 2/2 with matching traces and 0/2 with swapped trace references.
This establishes the scoring behavior with live observations. The
planner runner, sealed evaluation cases, budget enforcement, and real
strategy comparison are still pending.
