# WarWagon frontend

## The two deliberately separated interfaces

- **[Engagement UX](index.html)** is the default high-fidelity mission-centric interface restored from the approved WarWagon v2 operator design. It has three sample engagements: autonomous web application, supervised API/identity, guided cloud configuration. Includes mission creation and briefing, live workspace, task/trace inspector, reasoning frontier, verification studio, evidence graph, agent command, research/ARC concepts and operator-directive previews. **All this data is clearly simulated. It does not launch assessments.**
- **[Recorded Run Inspector](recorded-runs.html)** preserves Codex's previously working evidence-integrity inspector, browser-side import of real JSON trace+verification files, run catalog, ARC review detail and their existing source modules. This is *recorded real-model artifact review*, not a live execution backend. The files and model invocations are distinguished from the simulated experience.

Use the link in the UX left sidebar to reach the Recorded Run Inspector; its sidebar has a return link. **Never join simulated findings into real provenance or label sample actions verified.**

## Run locally

```bash
python -m http.server 48766 --bind 127.0.0.1 --directory console
```

Open `http://127.0.0.1:48766/`. The artifact inspector lives at `http://127.0.0.1:48766/recorded-runs.html`. No npm build is required.

## Screens in the main UX

- Mission Control; engagement library; four-step create/briefing
- Three individual engagement types and overview/workspace
- Investigation Console with task-to-tool-to-evidence navigation
- Live Activity; Mission Plan; Reasoning Frontier; Intelligence Graph
- Agent Command; Findings; Verification Studio; Evidence; Report; Settings
- Research Laboratory, Agent Fleet, ARC concept and Models & Integrations

## Verified backend data and future integration

- Existing real run artifacts: bundled `demo/*.json` and imported user-selected JSON with digest checks, still handled by `inspector.js`, `artifacts.js`, `runs.js` and `arc.js` from `recorded-runs.html`.
- Existing CLI evidence generation: `benchmarks/evidence_fixture/README.md`.
- Current UX does **not** yet have live engagement APIs for `Engagement`, `Task`, `Observation`, `EvidenceArtifact`, `FactAssertion`, `Finding`, `OperatorDirective` or `PlanRevision`. Those should be versioned and added as adapters rather than replacing provenance-checked data with mocked responses.
- Avoid declaring completed autonomous assessments based on demo fixtures. The sample local `127.0.0.1:3000` target is illustrative.

## Checks

```bash
cd console
node --test
```

UI tests enforce the main screen set, demo/real-data separation and preserved recorded-run links. Unit tests for run parsing and digest-bound verification remain unchanged.
