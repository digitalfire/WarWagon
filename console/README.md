# Run inspector

Serve the static console from the repository root. No frontend package
installation is required.

~~~sh
python -m http.server 48766 --bind 127.0.0.1 --directory console
~~~

Open `http://127.0.0.1:48766/` in a modern browser. The initial view loads
an actual `qwen3.8:27b` Ollama run recorded on November 23, 2026
(America/New_York). The model selected the fixed HEAD tool, received
HTTP 204 from the Docker fixture, and returned a supported claim. The
existing verifier accepted the model claim and separately rejected a
supplied negative-control claim. The example export contains the
fixed loopback URL, tool call, model metadata, observation and status
claim, and the verifier results. It has no credentials or raw prompts.

**Open JSON files** accepts one v1 `benign_head_evidence_run` artifact
and any associated v1 `benign_head_evidence_verification` artifacts.
Select the run and its results together. The inspector hashes the
original run bytes and rejects results for a different trace. A trace
opened alone has no verifier status. Model and supplied claim verdicts
are displayed separately.

Imported files are read in the browser. The inspector displays verdict
artifacts with matching trace digests. It does not rerun the verifier,
authenticate verdict authorship, contact the observed service, or
invoke a model. For verification, use the
[existing CLI](../benchmarks/evidence_fixture/README.md).

Run the artifact-import tests with Node 22 or newer:

~~~sh
node --test console/artifacts.test.mjs
~~~
