export function workspaceFromHash(hash) {
  if (hash === "#arc") return "arc";
  if (hash === "#overview") return "overview";
  return "runs";
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
