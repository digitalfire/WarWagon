import { readArtifacts } from "./artifacts.js";

const examples = [
  {
    title: "Confirmation run",
    files: ["./demo/trace.json", "./demo/model-verdict.json", "./demo/negative-verdict.json"],
  },
  {
    title: "Checkpoint recovery run",
    files: ["./demo/runs/checkpoint-trace.json", "./demo/runs/checkpoint-model-verdict.json",
      "./demo/runs/checkpoint-negative-verdict.json"],
  },
];
const dateFormat = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium", timeStyle: "medium",
});

async function loadFile(path) {
  const url = new URL(path, import.meta.url);
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url.pathname}: HTTP ${response.status}`);
  return new File([await response.arrayBuffer()], url.pathname.split("/").pop());
}

export function runRecord(run, { title = run.trace.file, isExample = false } = {}) {
  const trace = run.trace.data;
  const observedAt = trace.observation?.timestamp_utc;
  const time = typeof observedAt === "string" ? Date.parse(observedAt) : NaN;
  const modelVerdicts = new Set(run.reports
    .filter(report => report.data.claim_source === "model")
    .map(report => report.data.verified));
  let verdict = "No result";
  let tone = "neutral";
  if (modelVerdicts.size > 1) {
    verdict = "Mixed results";
    tone = "mixed";
  } else if (modelVerdicts.has(true)) {
    verdict = "Verified";
    tone = "good";
  } else if (modelVerdicts.has(false)) {
    verdict = "Rejected";
    tone = "bad";
  }

  return {
    run, isExample, title, time,
    date: Number.isFinite(time) ? dateFormat.format(time) : "Unavailable",
    model: trace.model,
    target: typeof trace.observation?.url === "string" ? trace.observation.url : "Unavailable",
    verdict, tone,
  };
}

export function filterRuns(records, query) {
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return records
    .filter(record => {
      const fields = [
        record.title, record.run.trace.file, record.model, record.target,
        record.date, record.run.trace.data.observation?.timestamp_utc,
        record.verdict, record.run.trace.digest, record.isExample ? "Example" : "Imported",
      ].join(" ").toLowerCase();
      return terms.every(term => fields.includes(term));
    })
    .sort((a, b) => (Number.isFinite(b.time) ? b.time : -Infinity)
      - (Number.isFinite(a.time) ? a.time : -Infinity) || a.title.localeCompare(b.title));
}

export async function loadRunCatalog(fetchFile = loadFile) {
  const bundles = await Promise.allSettled(examples.map(async example => {
    const files = await Promise.all(example.files.map(path => fetchFile(path)));
    return runRecord(await readArtifacts(files), { title: example.title, isExample: true });
  }));
  return {
    records: bundles.filter(bundle => bundle.status === "fulfilled").map(bundle => bundle.value),
    unavailable: bundles.filter(bundle => bundle.status === "rejected").length,
  };
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}

function runRow(record, activate) {
  const row = document.createElement("tr");
  const name = document.createElement("td");
  const button = element("button", record.title, "runs-record");
  button.type = "button";
  button.addEventListener("click", () => activate(record));
  const meta = element("div", "", "runs-record-meta");
  const time = Number.isFinite(record.time) ? element("time", record.date) : element("span", record.date);
  if (Number.isFinite(record.time)) time.dateTime = new Date(record.time).toISOString();
  const separator = element("span", "·");
  separator.setAttribute("aria-hidden", "true");
  meta.append(element("span", record.model, "runs-model"), separator, time);
  name.append(button, meta);
  const result = document.createElement("td");
  const badge = element("span", record.verdict, "runs-status");
  badge.dataset.tone = record.tone;
  result.append(badge);
  row.append(name, result);
  return {row, button};
}

export async function mountRuns(root, { openRun }) {
  const workspace = element("section", "", "runs-workspace");
  const toolbar = element("div", "", "runs-toolbar");
  const search = document.createElement("input");
  search.type = "search";
  search.placeholder = "Run, model, or verdict";
  search.disabled = true;
  const label = element("label", "Search runs", "runs-search-label");
  label.append(search);
  const status = element("p", "Loading recorded runs…", "runs-summary");
  status.role = "status";
  toolbar.append(label, status);
  const tableWrap = element("div", "", "runs-table-wrap");
  tableWrap.tabIndex = 0;
  tableWrap.setAttribute("role", "region");
  tableWrap.setAttribute("aria-label", "Recorded runs table");
  tableWrap.hidden = true;
  const table = element("table", "", "runs-table");
  table.setAttribute("aria-label", "Recorded runs");
  const header = document.createElement("tr");
  for (const heading of ["Run", "Model verdict"]) {
    const cell = element("th", heading);
    cell.scope = "col";
    header.append(cell);
  }
  const head = document.createElement("thead");
  head.append(header);
  const body = document.createElement("tbody");
  table.append(head, body);
  tableWrap.append(table);
  workspace.append(toolbar, tableWrap);
  root.replaceChildren(workspace);

  const catalog = await loadRunCatalog();
  const exampleRecords = new Map(catalog.records.map(record => [record.run.trace.digest, record]));
  const records = new Map(exampleRecords);
  const failed = catalog.unavailable;
  let currentDigest;
  const visible = new Map();
  function selectRun(digest) {
    currentDigest = digest;
    for (const [key, { row, button }] of visible) {
      const current = key === digest;
      row.toggleAttribute("data-current", current);
      if (current) button.setAttribute("aria-current", "true");
      else button.removeAttribute("aria-current");
    }
  }

  function activate(record) {
    selectRun(record.run.trace.digest);
    openRun(record.run, record.isExample);
  }

  function update() {
    const matching = filterRuns([...records.values()], search.value);
    tableWrap.hidden = matching.length === 0;
    visible.clear();
    for (const record of matching) {
      visible.set(record.run.trace.digest, runRow(record, activate));
    }
    body.replaceChildren(...[...visible.values()].map(({ row }) => row));
    selectRun(currentDigest);
    const summary = !records.size ? "No runs are available."
      : !matching.length ? "No runs match your search."
      : `${matching.length} ${matching.length === 1 ? "run" : "runs"} shown.`;
    status.textContent = failed ? `${summary} ${failed} recorded ${failed === 1 ? "example" : "examples"} could not be loaded.` : summary;
  }

  search.disabled = false;
  search.addEventListener("input", update);
  update();
  return {
    selectRun,
    addRun(run, { isExample = false, preserveSearch = false } = {}) {
      const digest = run.trace.digest;
      const title = isExample ? exampleRecords.get(digest)?.title : undefined;
      records.set(digest, runRecord(run, { title, isExample }));
      if (!preserveSearch) search.value = "";
      update();
    },
  };
}
