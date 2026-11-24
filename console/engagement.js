export const workspaceLabels = {
  mission: "Mission Control",
  engagements: "Engagements",
  new: "New Engagement",
  lab: "Research Laboratory",
  overview: "Engagement",
  runs: "Engagement",
  arc: "ARC",
};

export function workspaceFromHash(hash) {
  const route = hash.slice(1);
  if (!route) return "mission";
  return Object.hasOwn(workspaceLabels, route) ? route : "runs";
}

function tokenCount(invocation) {
  const value = invocation.usage?.total_tokens;
  return Number.isInteger(value) && value >= 0 ? value : null;
}

export function summarizeRun(trace) {
  const invocations = [trace.tool_invocation, trace.claim_invocation]
    .filter(invocation => invocation && typeof invocation === "object");
  const tokens = invocations.map(tokenCount);
  return {
    modelCalls: invocations.length || null,
    tokens: tokens.length && tokens.every(value => value !== null)
      ? tokens.reduce((sum, value) => sum + value, 0) : null,
    httpStatus: Number.isInteger(trace.observation?.status_code) ? trace.observation.status_code : null,
  };
}
