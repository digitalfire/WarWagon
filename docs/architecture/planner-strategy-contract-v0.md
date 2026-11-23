---
id: CONTRACT-PLANNER-001
status: proposed
version: 0.1.0
updated: 2026-11-23
---
# PlannerStrategy contract research

Language-agnostic **design sketch**, not implementation ABI.

```typescript
interface PlannerStrategy {
  manifest(): PlannerManifest;
  propose(request: PlanRequest): Promise<PlanResponse>;
}

type PlanRequest = {
  schemaVersion: "0.1.0";
  requestId: string;
  objectiveRef: string;
  knowledgeSnapshotRef: string;
  knowledgeRevision: number;
  activeTaskRefs: string[];
  eligibleCapabilities: string[];
  budget: { tokenCap: number; toolCallCap: number; deadlineMs: number };
  strategyParameters: Record<string, unknown>;
};

type IntentProposal = {
  proposalId: string;
  objectiveRef: string;
  strategyId: string;
  reasoningArtifactRef?: string;
  hypothesisRefs: string[];
  prerequisiteTaskRefs: string[];
  expectedEvidenceKinds: string[];
  capabilityRequirements: string[];
  noveltyFingerprint?: string;
  estimatedTokens?: number;
  estimatedToolCalls?: number;
  estimatedRuntimeMs?: number;
  terminationCriterion: string;
};

type PlanResponse = {
  schemaVersion: "0.1.0";
  snapshotRevision: number;
  proposals: IntentProposal[];
  abstentionReason?: string;
  modelInvocationRefs: string[];
};
```

## Deliberate constraints
No direct execute() entry point. Planners may abstain. Numeric utility scores must have a defined calibration scheme before use. Local clocks are not accepted as an ordering source; use event revisions/causal IDs. Proposal schema carries no raw model secrets or uncited 'verified' facts.

## Candidate frontier selector
Select from all pending proposals using dependency eligibility, semantic deduplication, diversity and cost; record selected/deferred/rejected and reason codes, with appeal path when new evidence changes eligibility.

## Contract tests needed
Schema validation, empty proposal, repeated proposal ID, stale revision, conflicting dependency, duplicate fingerprint, partial evaluation timeout, unknown strategy version, budget exhaustion, replay determinism and malformed evidence links.

## Open decisions
Sync vs async proposes, long-running planner streaming, event topology, UUID/ULID identity, ranking calibration, caller permissions, proposal expiry, graph snapshot consistency.
