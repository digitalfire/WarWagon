const previewUrl = new URL("./demo/arc/docs-as-code.json", import.meta.url);
const digestPattern = /^[a-f0-9]{64}$/;
const isDigest = value => typeof value === "string" && digestPattern.test(value);

export function validateArcPreview(preview) {
  if (preview?.kind !== "arc_review_preview" || preview.schemaVersion !== 1) {
    throw new Error("Unsupported ARC preview format.");
  }

  const { proposal, report, challenge, evidence, smokeDisposition } = preview;
  const roles = report?.roles;
  if (!proposal || !report || !challenge || !evidence || !smokeDisposition ||
      !Array.isArray(roles) || roles.length === 0 ||
      roles.some(role => typeof role?.role !== "string" ||
        !Array.isArray(role.attempts) || role.attempts.length === 0 ||
        role.attempts.some(attempt => !isDigest(attempt?.artifactSha256) ||
          typeof attempt.status !== "string" || typeof attempt.model !== "string" ||
          !["first-pass", "retry"].includes(attempt.stage) ||
          (attempt.status === "valid" && typeof attempt.verdict !== "string")))) {
    throw new Error("Incomplete ARC preview.");
  }

  const target = roles.find(role => role.role === challenge.targetRole);
  if ([proposal, report, challenge, evidence, smokeDisposition].some(record => !isDigest(record.sha256)) ||
      report.proposalSha256 !== proposal.sha256 ||
      challenge.reportSha256 !== report.sha256 ||
      !target?.attempts.some(attempt => attempt.artifactSha256 === challenge.targetArtifactSha256) ||
      evidence.challengeSha256 !== challenge.sha256 ||
      !isDigest(evidence.artifactSha256) ||
      smokeDisposition.challengeSha256 !== challenge.sha256 ||
      smokeDisposition.evidenceSha256 !== evidence.sha256) {
    throw new Error("ARC preview references do not match.");
  }
  return preview;
}

function node(tag, text, className) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (className) result.className = className;
  return result;
}

function addField(list, label, value, className) {
  list.append(node("dt", label), node("dd", value, className));
}

function addProvenance(section, entries) {
  const details = node("details", undefined, "arc-provenance");
  const list = node("dl", undefined, "stacked fields");
  for (const [label, digest] of entries) {
    addField(list, label, digest, "mono digest");
  }
  details.append(node("summary", "Artifact provenance"), list);
  section.append(details);
}

function card(heading) {
  const panel = node("section", undefined, "panel arc-card");
  panel.setAttribute("aria-label", heading);
  panel.append(node("h2", heading));
  return panel;
}

function block(heading, ...items) {
  const result = node("div", undefined, "arc-block");
  result.append(node("h3", heading), ...items);
  return result;
}

function readable(value) {
  const text = value.replace(/[-_]/g, " ");
  return text[0].toUpperCase() + text.slice(1);
}

function attemptDetails(title, roles, expanded = false) {
  const details = node("details", undefined, "arc-attempts");
  details.open = expanded;
  const list = node("ul", undefined, "arc-attempt-list");
  for (const role of roles) {
    for (const attempt of role.attempts) {
      const item = node("li");
      const badge = node("span", readable(attempt.verdict ?? attempt.status),
        attempt.status === "valid" ? "badge" : "badge fail");
      const label = node("strong", readable(role.role));
      item.append(label, badge, node("p", readable(attempt.stage) + " · " + attempt.model, "arc-attempt-meta"));
      if (attempt.error) item.append(node("p", attempt.error, "arc-attempt-meta"));
      list.append(item);
    }
  }
  details.append(node("summary", title), list);
  return details;
}

function renderArcPreview(root, preview) {
  const { proposal, report, challenge, evidence, smokeDisposition } = preview;
  const grid = node("div", undefined, "arc-grid");

  const proposalCard = card(proposal.id);
  proposalCard.append(node("p", proposal.title, "arc-proposal-title"));
  const totals = new Map();
  let unresolved = 0;
  for (const role of report.roles) {
    const verdict = role.attempts.findLast(attempt => attempt.status === "valid")?.verdict;
    if (verdict) totals.set(verdict, (totals.get(verdict) ?? 0) + 1);
    else unresolved++;
  }
  const counts = node("dl", undefined, "stacked fields arc-summary");
  for (const [verdict, count] of totals) addField(counts, readable(verdict) + " verdicts", count);
  addField(counts, "Unresolved roles", unresolved);
  proposalCard.append(counts);
  addProvenance(proposalCard, [["Proposal SHA-256", proposal.sha256], ["Review report SHA-256", report.sha256]]);

  const activity = card("Review activity");
  const firstPass = report.roles.flatMap(role => role.attempts).filter(attempt => attempt.stage === "first-pass");
  const validFirstPass = firstPass.filter(attempt => attempt.status === "valid").length;
  activity.append(block("First-pass reviews", node("p",
    validFirstPass + " of " + firstPass.length + " first-pass attempts produced valid reviews.")));
  const rolesWithRetriesOrErrors = report.roles.filter(role =>
    role.attempts.some(attempt => attempt.stage === "retry" || attempt.status !== "valid"));
  if (rolesWithRetriesOrErrors.length) {
    activity.append(attemptDetails("Retries and invalid responses", rolesWithRetriesOrErrors, true));
  }
  activity.append(attemptDetails("All reviewer attempts", report.roles));

  const discussion = card("Challenge and decision");
  const challengeHeader = node("div", undefined, "arc-inline");
  challengeHeader.append(node("span", readable(challenge.status), "badge arc-open"),
    node("p", readable(challenge.challenger) + " challenged " + readable(challenge.targetRole).toLowerCase() + "."));
  const target = readable(challenge.targetField) + ", item " + (challenge.targetIndex + 1);
  discussion.append(block("Challenge", challengeHeader, node("p", challenge.summary), node("p", target, "arc-attempt-meta")),
    block("Requested evidence", node("p", challenge.requestedEvidence)),
    block("Evidence response", node("p", evidence.summary), node("p", evidence.title, "arc-attempt-meta")));
  const smoke = node("details", undefined, "arc-provenance");
  smoke.append(node("summary", "Smoke-test disposition · " + readable(smokeDisposition.outcome)),
    node("p", smokeDisposition.rationale));
  discussion.append(block("Maintainer decision", node("p", "Pending for this challenge"), smoke));
  addProvenance(discussion, [
    ["Challenged attempt SHA-256", challenge.targetArtifactSha256],
    ["Challenge SHA-256", challenge.sha256],
    ["Response SHA-256", evidence.sha256],
    ["Evidence artifact SHA-256", evidence.artifactSha256],
    ["Smoke-test disposition SHA-256", smokeDisposition.sha256],
  ]);

  grid.append(proposalCard, activity, discussion);
  root.replaceChildren(grid);
}

export async function mountArc(root) {
  const notice = node("p", "Loading ARC review…", "notice");
  notice.setAttribute("role", "status");
  root.replaceChildren(notice);
  try {
    const response = await fetch(previewUrl);
    if (!response.ok) throw new Error("Could not load the ARC review.");
    renderArcPreview(root, validateArcPreview(await response.json()));
  } catch (error) {
    notice.textContent = error.message;
  }
}
