import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const base = new URL("./", import.meta.url);
const read = path => readFile(new URL(path, base), "utf8");
test("defaults to the engagement-centric v2 frontend", async () => {
  const html = await read("index.html");
  for (const name of ["Mission Control", "New Engagement", "Investigation Console",
      "Reasoning Frontier", "Verification Studio", "Evidence", "Agent Command",
      "Research Laboratory", "Architecture Council", "Knowledge Graph"]) {
    assert.ok(html.includes(name), "missing essential workspace: " + name);
  }
  assert.match(html, /function consoleTab\(/);
  assert.match(html, /function frontierTab\(/);
  assert.match(html, /function verificationTab\(/);
  assert.match(html, /DEMO \/ NO BACKEND/);
  assert.match(html, /recorded-runs\.html/);
});
test("keeps the real run inspector and recorded artifact verifier available", async () => {
  const html = await read("recorded-runs.html");
  assert.match(html, /inspector\.js/);
  assert.match(html, /run-template/);
  assert.match(html, /engagement-timeline/);
  assert.match(html, /href="\.\/index\.html"/);
  assert.match(await read("inspector.js"), /readArtifacts/);
});
