import { readArtifacts } from "./artifacts.js";
import { mountArc } from "./arc.js";
import { summarizeRun, workspaceFromHash } from "./engagement.js";
import { mountRuns, runRecord } from "./runs.js";

const run = document.querySelector("#run");
const template = document.querySelector("#run-template");
const state = document.querySelector("#load-state");
const open = document.querySelector("#open");
const sample = document.querySelector("#sample");
const files = document.querySelector("#files");
let loadRevision = 0;
const index = mountRuns(document.querySelector("#run-index"), {
  openRun(value, isExample) {
    loadRevision++;
    state.textContent = "";
    open.disabled = false;
    sample.disabled = false;
    render(value, isExample);
    run.querySelector("#run-title").focus();
  },
});
let arcMounted = false;

function showWorkspace() {
  const current = workspaceFromHash(location.hash);
  for (const link of document.querySelectorAll("[data-workspace]")) {
    if (link.dataset.workspace === current) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  for (const name of ["overview", "runs", "arc"]) {
    document.querySelector("#" + name + "-workspace").hidden = name !== current;
  }
  document.querySelector("#engagement-header").hidden = current === "arc";
  document.querySelector("#workspace-crumb").textContent = current === "arc" ? "ARC" : "Engagement";
  document.querySelector("#engagement-link").dataset.currentSection = String(current !== "arc");

  if (current === "arc" && !arcMounted) {
    arcMounted = true;
    void mountArc(document.querySelector("#arc-detail"));
  }
}

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

function render(value, isSample) {
  const { trace, reports } = value;
  const page = template.content.cloneNode(true);
  const field = name => page.querySelector(`[data-field="${name}"]`);
  const set = (name, value) => { field(name).textContent = value ?? "Unavailable"; };
  const data = trace.data;
  const observation = data.observation;
  const tool = data.tool_call;
  const args = tool?.function?.arguments;
  const claim = data.claim;
  const { date, time, verdict, tone } = runRecord(value);
  const { modelCalls, tokens, httpStatus } = summarizeRun(data);
  const metrics = {
    "engagement-target": observation?.url,
    "metric-calls": modelCalls,
    "metric-tokens": tokens,
    "metric-response": httpStatus == null ? null : "HTTP " + httpStatus,
    "metric-verdict": verdict,
  };
  for (const [id, metric] of Object.entries(metrics)) {
    document.getElementById(id).textContent = metric ?? "Unavailable";
  }
  const events = [
    tool?.function?.name && "Tool called · " + tool.function.name,
    observation && (httpStatus == null ? "Observation recorded" : "Observed HTTP " + httpStatus),
    claim?.status_code != null && "Model claimed HTTP " + claim.status_code,
    "Recorded model verdict · " + verdict,
  ].filter(Boolean);
  document.querySelector("#engagement-timeline").replaceChildren(...events.map(event => element("li", event)));

  set("source", isSample ? "Recorded example" : "Imported run");
  set("timestamp", date);
  if (Number.isFinite(time)) field("timestamp").dateTime = new Date(time).toISOString();
  set("model", data.model);
  set("target", typeof observation?.url === "string" ? observation.url : null);
  statusBadge(field("summary-verdict"), tone === "good" ? true : tone === "bad" ? false : undefined, verdict);
  field("summary-verdict").classList.toggle("mixed", tone === "mixed");
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
  const revision = ++loadRevision;
  open.disabled = true;
  sample.disabled = true;
  state.textContent = "Checking the selected artifacts…";
  try {
    if (!globalThis.crypto?.subtle) {
      throw new Error("Open the inspector on localhost or HTTPS to check artifact hashes.");
    }
    const value = await readArtifacts(await getFiles());
    if (revision !== loadRevision) return;
    render(value, isSample);
    state.textContent = "";
    if (!isSample) run.querySelector("#run-title").focus();
    const runsIndex = await index;
    if (revision !== loadRevision) return;
    runsIndex.addRun(value, { isExample: isSample, preserveSearch: isSample });
    runsIndex.selectRun(value.trace.digest);
  } catch (error) {
    if (revision !== loadRevision) return;
    state.textContent = run.hidden ? error.message : `${error.message} The previous run is still displayed.`;
  } finally {
    if (revision === loadRevision) {
      open.disabled = false;
      sample.disabled = false;
    }
  }
}

open.addEventListener("click", () => files.click());
files.addEventListener("change", () => {
  const selected = Array.from(files.files);
  files.value = "";
  if (selected.length) load(() => selected, false);
});
sample.addEventListener("click", () => load(exampleFiles, true));
window.addEventListener("hashchange", showWorkspace);
showWorkspace();
load(exampleFiles, true);
