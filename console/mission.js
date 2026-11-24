const types = ["Web application", "API & identity", "Cloud configuration"];
const limit = value => Number.isSafeInteger(value) && value > 0 && value <= 1440;

export function validateBrief(brief) {
  return types.includes(brief?.type)
    && typeof brief.title === "string" && !!brief.title.trim() && brief.title.length <= 100
    && typeof brief.objective === "string" && !!brief.objective.trim() && brief.objective.length <= 1000
    && typeof brief.scope === "string" && !!brief.scope.trim() && brief.scope.length <= 400
    && limit(brief.reviewMinutes);
}

export function readDrafts(raw) {
  try {
    const records = JSON.parse(raw ?? "[]");
    if (!Array.isArray(records)) return [];
    return records.filter(record => validateBrief(record)
      && typeof record.id === "string" && /^[a-f0-9-]{36}$/.test(record.id));
  } catch {
    return [];
  }
}

export function searchEngagements(records, query) {
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return records.filter(record => terms.every(term =>
    [record.title, record.id, record.scope, record.type].join(" ").toLowerCase().includes(term)));
}

const recorded = {
  id: "LOCAL-HTTP", title: "Local HTTP Evidence Review", type: "Web application",
  scope: "Recorded loopback HTTP observations",
};
const storageKey = "warwagon.engagement-briefs.v1";

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

export function mountMission(root) {
  const byId = id => root.querySelector("#" + id);
  const search = byId("engagement-search");
  const form = byId("brief-form");
  const steps = [...form.querySelectorAll("[data-brief-step]")];
  const indicators = [...root.querySelectorAll("[data-brief-indicator]")];
  const heading = byId("new-heading");
  const next = byId("brief-next");
  const back = byId("brief-back");
  const feedback = byId("brief-feedback");
  let drafts;
  try {
    drafts = readDrafts(localStorage.getItem(storageKey));
  } catch {
    drafts = [];
  }
  let editing = null;
  let step = 0;
  let runCount = null;
  let verifiedCount = null;

  function card(record) {
    const link = element("a", undefined, "panel mission-card");
    const caption = element("div", undefined, "mission-card-heading");
    const badge = element("span", record === recorded ? "Recorded" : "Draft", "badge");
    caption.append(element("span", record.type, "eyebrow"), badge);
    link.append(caption, element("h3", record.title), element("p", record.scope, "subtle"));
    if (record === recorded) link.append(element("p", record.id, "mono mission-id"));
    link.href = record === recorded ? "#runs" : "#new";
    if (record !== recorded) {
      link.addEventListener("click", () => edit(record));
    }
    return link;
  }

  function update() {
    const matches = searchEngagements([recorded, ...drafts], search.value);
    byId("mission-cards").replaceChildren(...[recorded, ...drafts.slice(0, 2)].map(card));
    byId("engagement-cards").replaceChildren(...matches.map(card));
    byId("engagement-count").textContent = matches.length + (matches.length === 1 ? " result" : " results");
    byId("engagement-empty").hidden = matches.length !== 0;
    byId("mission-recorded").textContent = "1";
    byId("mission-drafts").textContent = String(drafts.length);
    byId("mission-runs").textContent = runCount ?? "Unavailable";
    byId("mission-verified").textContent = verifiedCount ?? "Unavailable";
  }

  function values() {
    const fields = form.elements;
    return {
      type: fields.namedItem("type").value,
      title: fields.namedItem("title").value.trim(),
      objective: fields.namedItem("objective").value.trim(),
      scope: fields.namedItem("scope").value.trim(),
      reviewMinutes: Number(fields.namedItem("reviewMinutes").value),
    };
  }

  function showScope() {
    const { type, scope } = values();
    byId("scope-type").textContent = type;
    byId("scope-preview").textContent = scope || "No evidence scope entered yet.";
  }

  function showStep() {
    for (const [index, panel] of steps.entries()) {
      panel.hidden = index !== step;
      panel.disabled = index !== step;
      if (index === step) indicators[index].setAttribute("aria-current", "step");
      else indicators[index].removeAttribute("aria-current");
    }
    if (step === 1) showScope();
    back.hidden = step === 0;
    next.textContent = step === steps.length - 1 ? "Save local draft" : "Continue";
    if (step === steps.length - 1) {
      const brief = values();
      byId("brief-preview").replaceChildren(...[
        ["Type", brief.type], ["Title", brief.title], ["Objective", brief.objective],
        ["Evidence scope", brief.scope], ["Review time limit", brief.reviewMinutes + " minutes"],
      ].flatMap(([label, value]) => [element("dt", label), element("dd", value)]));
    }
  }

  function edit(record) {
    form.reset();
    feedback.textContent = "";
    editing = record?.id ?? null;
    heading.textContent = editing ? "Edit engagement draft" : "Create engagement";
    if (record) for (const [key, value] of Object.entries(record)) {
      const field = form.elements.namedItem(key);
      if (field) field.value = value;
    }
    step = 0;
    showStep();
  }

  back.addEventListener("click", () => {
    step--;
    showStep();
    steps[step].querySelector("legend").focus();
  });
  form.addEventListener("submit", event => {
    event.preventDefault();
    feedback.textContent = "";
    if (step === 1 && [...steps[step].querySelectorAll("[required]")].some(field => !field.value.trim())) {
      feedback.textContent = "Enter a title, objective, and evidence scope.";
      return;
    }
    if (step < steps.length - 1) {
      step++;
      showStep();
      steps[step].querySelector("legend").focus();
      return;
    }
    const brief = values();
    if (!validateBrief(brief)) {
      feedback.textContent = "Review the required fields and review time limit.";
      return;
    }
    let updated;
    try {
      const draft = { id: editing ?? crypto.randomUUID(), ...brief };
      const saved = readDrafts(localStorage.getItem(storageKey));
      updated = [draft, ...saved.filter(record => record.id !== draft.id)];
      localStorage.setItem(storageKey, JSON.stringify(updated));
    } catch {
      feedback.textContent = "This browser could not save the local draft.";
      return;
    }
    drafts = updated;
    edit();
    search.value = "";
    update();
    byId("engagement-feedback").textContent = "Engagement draft saved in this browser.";
    location.hash = "#engagements";
  });

  for (const link of root.querySelectorAll("[data-new-brief]")) {
    link.addEventListener("click", () => edit());
  }
  form.elements.namedItem("scope").addEventListener("input", showScope);
  search.addEventListener("input", update);
  edit();
  update();

  return {
    setRecords(records) {
      runCount = records.length;
      verifiedCount = records.filter(record => record.verdict === "Verified").length;
      const latest = records.filter(record => Number.isFinite(record.time))
        .reduce((last, record) => !last || record.time > last.time ? record : last, null);
      byId("mission-latest").textContent = latest ? latest.title + " · " + latest.verdict : records.length ? "No recorded run timestamps." : "No runs loaded.";
      update();
    },
  };
}
