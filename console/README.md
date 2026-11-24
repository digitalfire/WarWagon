# WarWagon React console

**Production frontend direction:** React 19 + TypeScript + Vite + Tailwind CSS v4, Radix primitives (shadcn-compatible), TanStack Query, Zustand, React Flow, Apache ECharts, Vitest and Playwright.

The default landing page is now a **real React component application**, not the original 97 KB script/HTML prototype. Domain models, store, reusable components and screens live in `src/`.

## Development

Requirements: Node.js 22+, npm.

```bash
cd console
npm install
npm run dev
```

Open the printed Vite local URL (normally `http://127.0.0.1:5173`). The migration removes the old instruction to serve `console/index.html` directly with Python: that index now requires Vite for module compilation.

```bash
npm run build
npm run preview
npm test
npm run test:ui
```

`npm run test:ui` requires a Playwright Chromium install (`npx playwright install chromium`).

## Where things live

- `index.html` — Vite React application.
- `src/domain/types.ts` — canonical frontend engagement/task/evidence contracts (prototype types, not authoritative backend schemas).
- `src/demo/fixtures.ts` — exactly three **illustrative** engagement archetypes.
- `src/state/workspace.ts` — Zustand page, tab, selection and local operator note state.
- `src/screens/MissionControl.tsx` — portfolio, engagement library and command overview.
- `src/screens/NewEngagement.tsx` — 4-step mission creator, limits and preview briefing.
- `src/screens/EngagementWorkspace.tsx` — task, plan, events, agents, findings, evidence, report and operator channel.
- `src/components/Investigation.tsx`, `Frontier.tsx`, `Verification.tsx` — three primary investigator workspaces.
- `src/components/IntelligenceGraph.tsx` — React Flow knowledge projection; selecting a hypothesis/finding opens its inspector.
- `src/screens/Supporting.tsx` — Research, ARC and integrations.
- `src/styles.css` — Tailwind v4 and WarWagon design tokens/responsive styling.
- `recorded-runs.html` and the existing `inspector.js`, `runs.js`, `artifacts.js`, `arc.js` — **unchanged real recorded-run and ARC evidence inspector**.
- `ux-reference.html` — frozen original high-fidelity v2 UI for design comparison only.

The Vite multi-page build includes the recorded inspector and the original UX reference. `public/demo` contains immutable copies of the current bundled example artifacts so the inspector can still load them from the built dist.

## Evidence integrity

The React UI is a UX preview using controlled **sample data**. No backend calls are made, no target is contacted, and operator directives are preview-only. Its example 'verified' cloud item is **not a real WarWagon vulnerability report**. The recorded inspector continues to parse actual local evidence fixture files and check verifier linkage/digests.

**Do not merge sample engagement state into recorded evidence.** Real integration requires: Engagement, PlanRevision, AgentTask, ModelInvocation, EventRecord, Observation, EvidenceArtifact, FactAssertion, FindingVerification, and OperatorDirective contracts; a typed OpenAPI client; an SSE stream with resumable cursors; provenance checks.

## Engineering follow-ups

1. Reconcile the frontend domain types with versioned backend schemas; generate an API client.
2. Introduce an adapter interface that maps actual verified run data into the same screens.
3. Wire task lineage, evidence inspector and validation status to real backend records. Keep missing data explicit.
4. Replace local concept directives with backend versioned command events and selective replanning.
5. Add end-to-end browser coverage to the continuous integration gate.

Avoid duplicating or discarding the recorded-artifact verifier. Do not suggest that screenshots or sample metrics demonstrate live agent capability.
