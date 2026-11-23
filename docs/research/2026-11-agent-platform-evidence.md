---
id: RES-001
status: research
updated: 2026-11-23
---
# Initial evidence: durable agent runtimes, MCP, multi-agent evaluation

This note contains external research, **not accepted technology selections**.

## Durable workflows
Temporal documentation describes event-history-backed workflow replay with deterministic workflow definitions and activities that interact with external systems. Implication: WarWagon should compare a durable workflow engine with an explicit event-ledger scheduler, especially around side-effect reconciliation, replay evolution and long-running agent interruption.

Source: https://docs.temporal.io/durable-execution
Source: https://docs.temporal.io/workflows

## MCP version compatibility
The Model Context Protocol's 2026-07-28 revision introduces a stateless core, extension framework, authorization changes and updated long-running task mechanics. Implication: WarWagon's adapter contracts must define protocol-version negotiation, task handles, permissions, timeouts and discovery caching. Do not assume a long-running MCP call behaves like a durable WarWagon task.

Source: https://blog.modelcontextprotocol.io/posts/2026-07-28/
Source: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx

## Agent evaluation
Recent research emphasizes trajectory-level validity and reproduction rather than end-result-only scores. WarWagon needs environment-sealed fixtures, ground truth, recorded tool trajectories and baseline parity. These papers are research inputs, not proof any WarWagon planner is superior.

Source: https://doi.org/10.1145/3786335.3813231
Source: https://link.springer.com/article/10.1007/s10462-026-11571-0
Source: https://doi.org/10.1145/3770854.3785692

## Open research questions
1. How does a fact-intent graph planner compare with hierarchical delegation on branching tasks?
2. Does multi-agent execution increase verified coverage per token or merely duplicate work?
3. What subset of the cognitive loop must be durable vs reconstructable?
4. What is the smallest canonical data graph supporting explainable decisions?
5. Which benchmark tasks test genuine coordination rather than agent prompt verbosity?
