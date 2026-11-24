import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { validateArcPreview } from "./arc.js";

const preview = JSON.parse(await readFile(new URL("./demo/arc/docs-as-code.json", import.meta.url), "utf8"));

test("ARC demo retains all roles and the invalid response followed by a valid retry", () => {
  const { report, challenge, evidence, smokeDisposition } = validateArcPreview(preview);
  assert.equal(report.roles.length, 9);
  const skeptic = report.roles.find(role => role.role === "research-skeptic");
  assert.deepEqual(skeptic.attempts.map(attempt => [attempt.stage, attempt.status, attempt.verdict]), [
    ["first-pass", "invalid_response", null],
    ["retry", "valid", "conditional"],
  ]);
  assert.equal(challenge.status, "open");
  assert.equal(smokeDisposition.outcome, "needs-evidence");
  assert.equal(smokeDisposition.evidenceSha256, evidence.sha256);
  assert.equal(Object.hasOwn(preview, "decision"), false);
});

test("ARC preview rejects a mismatched proposal, challenge, attempt, or evidence link", () => {
  const badDigest = "0".repeat(64);
  for (const [section, field] of [
    ["report", "proposalSha256"],
    ["challenge", "reportSha256"],
    ["challenge", "targetArtifactSha256"],
    ["evidence", "challengeSha256"],
    ["smokeDisposition", "evidenceSha256"],
  ]) {
    const copy = structuredClone(preview);
    copy[section][field] = badDigest;
    assert.throws(() => validateArcPreview(copy), /references do not match/);
  }
});

test("ARC demo omits raw model output and machine paths", () => {
  const serialized = JSON.stringify(preview);
  assert.doesNotMatch(serialized, /"(response|path)"\s*:/i);
  assert.doesNotMatch(serialized, /wsl\.localhost|\/home\//i);
});

test("ARC preview rejects unsupported versions and incomplete attempt records", () => {
  assert.throws(() => validateArcPreview({ ...preview, schemaVersion: 2 }), /Unsupported/);
  const copy = structuredClone(preview);
  copy.report.roles[0].attempts = [];
  assert.throws(() => validateArcPreview(copy), /Incomplete/);
});
