const runKind = "benign_head_evidence_run";
const reportKind = "benign_head_evidence_verification";
const isDigest = value => typeof value === "string" && /^[0-9a-f]{64}$/.test(value);

export async function readArtifacts(files) {
  let trace;
  const reports = [];
  for (const file of files) {
    const bytes = await file.arrayBuffer();
    let data;
    try {
      data = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
    } catch {
      throw new Error(`${file.name}: invalid UTF-8 JSON.`);
    }
    if (data?.schema_version !== 1) {
      throw new Error(`${file.name}: expected a version 1 run trace or verifier result.`);
    }

    if (data.kind === runKind) {
      if (trace) throw new Error("Open one run trace at a time.");
      if (typeof data.model !== "string" || !isDigest(data.observation_sha256)) {
        throw new Error(`${file.name}: invalid run metadata.`);
      }
      const digest = await crypto.subtle.digest("SHA-256", bytes);
      trace = { file: file.name, data, digest: Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("") };
    } else if (data.kind === reportKind) {
      if (
        typeof data.verified !== "boolean" ||
        !["model", "supplied"].includes(data.claim_source) ||
        !isDigest(data.trace_sha256) ||
        !isDigest(data.expectation_sha256) ||
        (data.verified ? data.reason !== null : typeof data.reason !== "string" || !data.reason) ||
        (data.claim_source === "supplied"
          ? !isDigest(data.supplied_claim_sha256)
          : data.supplied_claim_sha256 !== null)
      ) {
        throw new Error(`${file.name}: invalid verifier result.`);
      }
      reports.push({ file: file.name, data });
    } else {
      throw new Error(`${file.name}: unsupported artifact type.`);
    }
  }

  if (!trace) throw new Error("Select a run trace JSON file.");
  for (const report of reports) {
    if (report.data.trace_sha256 !== trace.digest) {
      throw new Error(`${report.file}: trace SHA-256 does not match the selected run.`);
    }
  }
  return { trace, reports };
}
