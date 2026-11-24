# WarWagon console

Serve the static console from the repository root with Python. The
browser has no package installation step.

~~~sh
python -m http.server 48766 --bind 127.0.0.1 --directory console
~~~

Open `http://127.0.0.1:48766/` in a modern browser.

## Runs

Browse recorded benign Ollama runs and select one to see tool calls,
observations, claims, and verifier results. Search the catalog by model
or run details. The recorded examples used `qwen3.8:27b` to call a fixed
HEAD tool against the local Docker fixture. The independent verifier
accepted the HTTP 204 claims and rejected supplied negative controls.

**Open JSON files** accepts one v1 `benign_head_evidence_run` artifact and
its v1 `benign_head_evidence_verification` artifacts. Open them together
to see the associated results. The console checks each verdict's
trace digest against the exact run bytes. A trace opened alone has no
verifier result. Imported runs are available in the catalog for the
current page session. The example exports contain a loopback URL, tool
and model metadata, observations and claims, and verifier results.

Imported files are read in the browser. The console displays recorded
verdicts. To generate a verdict, use the
[existing CLI](../benchmarks/evidence_fixture/README.md).

## Architecture Review Council

The ARC workspace shows a recorded review of ADR-0001. It preserves the
invalid first pass alongside the valid retry, links the open challenge to
its evidence response, and displays the recorded smoke-test disposition
separately from the pending maintainer decision. The bundled view uses a
projection of retained artifacts with source digests. No raw review
responses or evidence file paths are bundled.

See [ARC governance](../docs/governance/architecture-review-council.md)
and the [prototype runbook](../docs/prototypes/real-agent-and-arc.md) for
the review lifecycle and artifact-producing commands.

## Tests

Run the console's artifact tests from its directory using Node 22 or newer.

~~~sh
cd console
node --test
~~~
