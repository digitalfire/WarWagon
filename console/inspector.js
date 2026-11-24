import { readArtifacts } from "./artifacts.js";

const run = document.querySelector("#run");
const template = document.querySelector("#run-template");
const state = document.querySelector("#load-state");
const open = document.querySelector("#open");
const sample = document.querySelector("#sample");
const files = document.querySelector("#files");

function element(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}

function statusBadge(node, verified, label) {
  node.textContent = label;
  node.classList.toggle("pass", verified === true);
  node.classList.toggle("fail", verified === false);
}

function showReports(panel, reports) {
  if (!reports.length) {
    panel.append(element("p", "No verifier result loaded. Open the trace and its verifier JSON files together."));
    return;
  }
  for (const { file, data } of reports) {
    const report = element("article", "", "report");
    const heading = element("div", "", "report-heading");
    const badge = element("span", "", "badge");
    statusBadge(badge, data.verified, data.verified ? "Verified" : "Rejected");
    heading.append(element("h3", data.claim_source === "model" ? "Model claim" : "Supplied claim"), badge);
    report.append(heading, element("p", data.verified ? "Evidence supported the claim." : data.reason));
    const details = document.createElement("details");
    const fields = element("dl", "", "stacked fields");
    fields.append(
      element("dt", "Verifier file"), element("dd", file),
      element("dt", "Expectation SHA-256"), element("dd", data.expectation_sha256, "mono digest")
    );
    if (data.claim_source === "supplied") {
      fields.append(element("dt", "Supplied claim SHA-256"),
        element("dd", data.supplied_claim_sha256, "mono digest"));
    }
    details.append(element("summary", "Verifier inputs"), fields);
    report.append(details);
    panel.append(report);
  }
}

function render({ trace, reports }, isSample) {
  const page = template.content.cloneNode(true);
  const field = name => page.querySelector(`[data-field="${name}"]`);
  const set = (name, value) => { field(name).textContent = value ?? "Unavailable"; };
  const data = trace.data;
  const observation = data.observation;
  const tool = data.tool_call;
  const args = tool?.function?.arguments;
  const claim = data.claim;
  const timestamp = Date.parse(observation?.timestamp_utc);
  const modelReports = reports.filter(report => report.data.claim_source === "model");
  const verified = modelReports[0]?.data.verified;
  const conflict = modelReports.some(report => report.data.verified !== verified);

  set("source", isSample ? "Recorded example" : "Imported run");
  set("timestamp", Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : null);
  set("model", data.model);
  set("target", typeof observation?.url === "string" ? observation.url : null);
  statusBadge(
    field("summary-verdict"), conflict ? undefined : verified,
    conflict ? "Mixed results" : verified === undefined ? "No result" : verified ? "Verified" : "Rejected"
  );
  set("tool", tool?.function?.name);
  set("arguments", typeof args === "string" ? args : args == null ? null : JSON.stringify(args, null, 2));
  set("call-id", tool?.id);
  set("tool-tokens", data.tool_invocation?.usage?.total_tokens);
  set("method", observation?.method);
  set("url", observation?.url);
  set("status", observation?.status_code ?? observation?.error_type);
  set("duration", typeof observation?.total_seconds === "number"
    ? `${(observation.total_seconds * 1000).toFixed(1)} ms` : null);
  set("redirects", observation?.redirects_followed);
  set("checkpoint", data.observation_reused === true ? "Observation reused"
    : data.observation_reused === false ? "Observation recorded" : null);
  set("claim-status", claim?.status_code == null ? "No parsed claim" : `HTTP ${claim.status_code}`);
  set("claim-digest", claim?.observation_sha256);
  set("claim-tokens", data.claim_invocation?.usage?.total_tokens);
  set("trace-digest", trace.digest);
  set("observation-digest", data.observation_sha256);
  set("file", trace.file);
  showReports(field("reports"), reports);
  run.replaceChildren(page);
  run.hidden = false;
}

async function exampleFiles() {
  return Promise.all(["trace.json", "model-verdict.json", "negative-verdict.json"].map(async name => {
    const response = await fetch(`./demo/${name}`);
    if (!response.ok) throw new Error(`Could not load the example file ${name}.`);
    return new File([await response.arrayBuffer()], name);
  }));
}

async function load(getFiles, isSample) {
  open.disabled = true;
  sample.disabled = true;
  state.textContent = "Checking the selected artifacts…";
  try {
    if (!globalThis.crypto?.subtle) {
      throw new Error("Open the inspector on localhost or HTTPS to check artifact hashes.");
    }
    render(await readArtifacts(await getFiles()), isSample);
    state.textContent = "";
  } catch (error) {
    state.textContent = run.hidden ? error.message : `${error.message} The previous run is still displayed.`;
  } finally {
    open.disabled = false;
    sample.disabled = false;
  }
}

open.addEventListener("click", () => files.click());
files.addEventListener("change", () => {
  const selected = Array.from(files.files);
  files.value = "";
  if (selected.length) load(() => selected, false);
});
sample.addEventListener("click", () => load(exampleFiles, true));
load(exampleFiles, true);
