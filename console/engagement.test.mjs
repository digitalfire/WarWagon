import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { summarizeRun, workspaceFromHash } from "./engagement.js";

test("links to Overview or ARC and preserves existing investigation hashes", () => {
  assert.equal(workspaceFromHash("#overview"), "overview");
  assert.equal(workspaceFromHash("#arc"), "arc");
  for (const hash of ["", "#runs", "#investigation", "#unknown"]) {
    assert.equal(workspaceFromHash(hash), "runs");
  }
});

test("summarizes the real sample using its recorded data", async () => {
  const trace = JSON.parse(await readFile(new URL("./demo/trace.json", import.meta.url), "utf8"));
  assert.deepEqual(summarizeRun(trace), { modelCalls: 2, tokens: 779, httpStatus: 204 });
});

test("preserves missing usage without implying a complete total", () => {
  assert.deepEqual(summarizeRun({
    tool_invocation: { usage: { total_tokens: 10 } },
    claim_invocation: {},
  }), { modelCalls: 2, tokens: null, httpStatus: null });
  assert.deepEqual(summarizeRun({}), { modelCalls: null, tokens: null, httpStatus: null });
});
