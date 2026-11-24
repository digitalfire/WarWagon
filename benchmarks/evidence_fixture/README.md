# Benign Docker evidence smoke test

The fixture has one expected result for HEAD at its root. The WarWagon
test exposes one argument-free tool for that fixed route and sends no
other fixture requests. It uses a local Ollama model.

Run from the repository root on the host that owns the published
loopback port. On Windows, use Windows Python if Docker and Ollama
are published on Windows loopback.

~~~bash
docker build -t warwagon-benign-evidence-fixture:local benchmarks/evidence_fixture
docker run --detach --name warwagon-ollama-evidence-fixture --publish 127.0.0.1:48739:8080 --read-only --cap-drop ALL --security-opt no-new-privileges warwagon-benign-evidence-fixture:local
python -m warwagon.evidence_smoke run --model qwen3.8:27b --checkpoint artifacts/evidence.sqlite --stop-after-observation
python -m warwagon.evidence_smoke run --model qwen3.8:27b --checkpoint artifacts/evidence.sqlite --output artifacts/evidence-trace.json
python -m warwagon.evidence_smoke verify artifacts/evidence-trace.json --expected benchmarks/evidence_fixture/expected.json --output artifacts/verification.json
~~~

The first process commits the model-selected call and HTTP observation
to SQLite and exits. The next process uses that observation to request
a final claim. Keep the checkpoint on the local filesystem and use a
new checkpoint for a new run. An interruption before a stage commits
can repeat that stage. Use new output filenames for repeated exports.

The verifier reads the expected status separately from the model
run. It checks the recorded fixed tool call, observation digest, HEAD
route, status, and claim. The verdict records SHA-256 hashes of the exact
trace, expectation, and supplied claim files it consumed. To test rejection, create a claim JSON containing the trace's
`observation_sha256` and a different `status_code`, then pass it with
`verify --claim PATH`. Exit status 1 means verification failed. The
output distinguishes model-supplied and externally supplied claims.

## Recorded execution

On Ollama 0.33.2, `qwen3.8:27b` selected the tool and reported 204 with
the correct observation digest. The tool and claim turns recorded 393
and 368 tokens. The isolated Docker container logged exactly one HEAD
request across the two processes. The verifier accepted the real 204
claim and rejected the supplied 200 claim. A cached re-export preserved
both model invocation records without additional HTTP or inference calls.

This validates tool selection, benign HTTP observation, checkpoint reuse,
and verification against a separate expectation. The synthetic fixture
does not satisfy the vulnerability-assessment criterion in
[issue #7](https://github.com/digitalfire/WarWagon/issues/7).
