import assert from "node:assert/strict";
import test from "node:test";
import { readDrafts, searchEngagements, validateBrief } from "./mission.js";

const brief = {
  id: "12345678-abcd-4567-abcd-123456789012",
  type: "API & identity", title: "Review run evidence",
  objective: "Review an existing trace", scope: "Recorded API evidence", reviewMinutes: 30,
};

test("drafts require an objective, evidence scope, and bounded review time", () => {
  assert.equal(validateBrief(brief), true);
  for (const invalid of [{ scope: "  " }, { reviewMinutes: 0 }, { reviewMinutes: 1441 },
    { reviewMinutes: 1.5 }, { type: "unknown" }]) {
    assert.equal(validateBrief({ ...brief, ...invalid }), false);
  }
});

test("stored drafts ignore malformed entries without losing valid records", () => {
  assert.deepEqual(readDrafts("not JSON"), []);
  assert.deepEqual(readDrafts("{}"), []);
  assert.deepEqual(readDrafts(JSON.stringify([brief, {}, { ...brief, id: "broken" }])), [brief]);
});

test("library search combines terms across title, type, ID, and scope", () => {
  assert.deepEqual(searchEngagements([brief], "  API recorded  "), [brief]);
  assert.deepEqual(searchEngagements([brief], "12345678 evidence"), [brief]);
  assert.deepEqual(searchEngagements([brief], "missing"), []);
});
