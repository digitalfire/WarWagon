import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { filterRuns, loadRunCatalog, runRecord } from "./runs.js";

async function readDemo(path) {
  return new File([await readFile(new URL(path, import.meta.url))], path.split("/").pop());
}

test("loads both saved Ollama runs with their bound positive and negative verdicts", async () => {
  const {records, unavailable} = await loadRunCatalog(readDemo);
  assert.equal(unavailable, 0);
  assert.deepEqual(records.map(record => record.title), ["Confirmation run", "Checkpoint recovery run"]);
  assert.equal(new Set(records.map(record => record.run.trace.digest)).size, 2);
  for (const record of records) {
    assert.equal(record.isExample, true);
    assert.equal(record.model, "qwen3.8:27b");
    assert.equal(record.verdict, "Verified");
    assert.equal(record.tone, "good");
    assert.deepEqual(record.run.reports.map(report => [report.data.claim_source, report.data.verified]),
      [["model", true], ["supplied", false]]);
  }
});

test("keeps the independent example when a second trace is changed", async () => {
  const {records, unavailable} = await loadRunCatalog(async path => {
    const file = await readDemo(path);
    return path.includes("checkpoint-trace") ? new File([file, "\n"], file.name) : file;
  });
  assert.equal(unavailable, 1);
  assert.deepEqual(records.map(record => record.title), ["Confirmation run"]);
});

test("filters by multiple case-insensitive terms and sorts most recent records first", async () => {
  const {records} = await loadRunCatalog(readDemo);
  const older = records.find(record => record.title === "Checkpoint recovery run");
  const newer = records.find(record => record.title === "Confirmation run");
  assert.deepEqual(filterRuns([older, newer], ""), [newer, older]);
  assert.deepEqual(filterRuns(records, "   CHECKPOINT   qwen3   verif "), [older]);
  assert.deepEqual(filterRuns(records, "no result"), []);
  assert.deepEqual(filterRuns(records, older.run.trace.digest.slice(0, 9)), [older]);
});

test("keeps supplied claim verdicts separate from the model result", async () => {
  const {records: [record]} = await loadRunCatalog(readDemo);
  const imported = runRecord({ ...record.run, reports: [record.run.reports[1]] });
  assert.equal(imported.isExample, false);
  assert.equal(imported.title, record.run.trace.file);
  assert.equal(imported.verdict, "No result");
  assert.equal(imported.tone, "neutral");
});

test("reports model rejection or disagreement without selecting a preferred verdict", async () => {
  const {records: [record]} = await loadRunCatalog(readDemo);
  const [accepted] = record.run.reports;
  const rejected = { ...accepted, data: { ...accepted.data, verified: false } };
  const modelRejected = runRecord({ ...record.run, reports: [rejected] });
  const modelConflict = runRecord({ ...record.run, reports: [accepted, rejected] });
  assert.deepEqual([modelRejected.verdict, modelRejected.tone], ["Rejected", "bad"]);
  assert.deepEqual([modelConflict.verdict, modelConflict.tone], ["Mixed results", "mixed"]);
});
