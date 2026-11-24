import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { readArtifacts } from "./artifacts.js";

async function demo(name) {
  return new File([await readFile(new URL(`./demo/${name}`, import.meta.url))], name);
}

test("loads the real Ollama trace and both independently produced verdicts in any order", async () => {
  const run = await readArtifacts(await Promise.all([
    demo("negative-verdict.json"), demo("trace.json"), demo("model-verdict.json"),
  ]));
  assert.equal(run.trace.data.tool_call.function.name, "observe_fixture_head");
  assert.equal(run.trace.data.observation.status_code, 204);
  assert.equal(run.trace.data.claim.status_code, 204);
  assert.deepEqual(run.reports.map(report => [report.data.claim_source, report.data.verified]), [
    ["supplied", false], ["model", true],
  ]);
});

test("refuses to attach a positive verdict when the trace bytes change", async () => {
  const trace = await demo("trace.json");
  const altered = new File([trace, "\n"], trace.name);
  await assert.rejects(
    readArtifacts([altered, await demo("model-verdict.json")]),
    /trace SHA-256 does not match/
  );
});

test("opens an unverified trace and preserves the absence of a verdict", async () => {
  const run = await readArtifacts([await demo("trace.json")]);
  assert.equal(run.reports.length, 0);
});

test("rejects a result without a trace and rejects multiple traces", async () => {
  await assert.rejects(readArtifacts([await demo("model-verdict.json")]), /Select a run trace/);
  const trace = await demo("trace.json");
  await assert.rejects(readArtifacts([trace, trace]), /Open one run trace/);
});

test("rejects corrupted input and malformed verifier booleans", async () => {
  await assert.rejects(
    readArtifacts([new File(["{"], "bad.json")]),
    /invalid UTF-8 JSON/
  );
  const valid = JSON.parse(await (await demo("model-verdict.json")).text());
  const malformed = new File([JSON.stringify({ ...valid, verified: "true" })], "bad-result.json");
  await assert.rejects(
    readArtifacts([await demo("trace.json"), malformed]),
    /invalid verifier result/
  );
});
