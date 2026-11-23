---
id: ADR-0003
status: proposed
date: 2026-11-23
---
# ADR-0003 — Python-first real intelligence vertical slice

## Decision proposal
Implement the first executable intelligence experiment in Python 3.12, using a local loopback training fixture, an OpenAI-compatible model interface, structured function calls, JSON traces, and GitHub Actions tests. Do **not** delay first real-model experiments for a production-grade Go control plane, Temporal, distributed broker, graph database, or UI.

## Motivation
WarWagon's primary hypothesis is that agent cognition, knowledge sharing and planning strategy improve verified security assessment outcomes. The fastest meaningful falsification is to run actual models on reproducible tasks, not polish infrastructure unrelated to that question.

## Alternatives
A. Full Go+Python microservices immediately: more realistic long-term stack, slower research feedback and larger integration footprint.
B. Python-first experimental kernel: fewer dependencies, fast model/tool iterations, easier reproducibility; long-term runtime may be replaced.
C. Existing AntiFox/PentAGI fork: fast feature availability but inherits orchestration assumptions and licensing/integration concerns.

## Stack by phase
- **Now:** Python 3.12, Python standard library, HTTP local lab, OpenAI-compatible chat API (local Ollama or external HTTPS), JSON run manifests, GitHub Actions.
- **Next:** event history in SQLite or PostgreSQL after replay semantics are specified, typed tool connectors and sealed independent scoring.
- **Later (benchmark-driven):** Go control plane, durable workflows, Kubernetes, streaming bus, graph search and frontend only when they offer demonstrated utility.

## Exit
Live model produces observations, a supported claim and independently scored evidence. A second real planning strategy competes at equal budgets, with raw traces and a repeatable run manifest.

## Open decisions
Which real tool-calling local model? How should aggregate token budgets be enforced across providers? How to pin model version and inference runtime? Which fixture benchmark is sufficiently hard and held out? Can ARC reviewers be run on independent providers?

No claim of technology approval until maintainer acceptance.
