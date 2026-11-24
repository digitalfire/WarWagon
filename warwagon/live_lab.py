"""Run the actual local WarWagon teaching fixture and persist LLM/tool events.

The producer is a CLI intentionally, not an unauthenticated HTTP launch route.
No inference is performed until invoked by a user on a configured model server.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from warwagon.agent import AgentRunner
from warwagon.engagement_store import DEFAULT_PATH, EngagementLedger
from warwagon.lab import FixtureServer, LabTool, verify_finding
from warwagon.model import ChatModel
from warwagon.scoring import score_discovery

GOAL = (
    "Investigate the local training web application's HTTP interface. "
    "Inspect / and find and verify any HTML encoding issue using non-destructive input. "
    "Cite actual observations."
)


def run_local_lab(model, ledger: EngagementLedger, *, max_steps: int = 12) -> dict:
    """Execute the model-proposed investigation, not a synthetic scripted assessment."""
    if type(max_steps) is not int or not 1 <= max_steps <= 60:
        raise ValueError("max_steps must be between 1 and 60")
    with FixtureServer() as fixture:
        engagement = ledger.create_engagement(
            "Local HTML teaching lab", f"http://127.0.0.1:{fixture.port}",
            model=model.model,
        )
        engagement_id = engagement["id"]
        ledger.transition(engagement_id, "running")

        def sink(kind: str, payload: dict):
            ledger.append(engagement_id, kind, payload, origin="local-agent")

        try:
            result = AgentRunner(
                model, LabTool(fixture.port), max_steps, event_sink=sink
            ).run(GOAL)
            oracle = verify_finding(fixture.port)
            discovery = score_discovery(result["trace"], oracle)
            # These are separate concepts. The fixture oracle does not grant
            # independent proof of real-world vulnerability discovery.
            ledger.append(
                engagement_id, "fixture.oracle.result", oracle,
                origin="fixture-verifier",
            )
            ledger.append(
                engagement_id, "agent.discovery.heuristic", discovery,
                origin="lab-scorer",
            )
            ledger.append(
                engagement_id, "run.finished",
                {"toolSteps": len([x for x in result["trace"] if x["kind"] == "tool"]),
                 "usage": result["usage"], "objectiveSatisfied": bool(discovery["credited"])},
                origin="runtime",
            )
            ledger.transition(engagement_id, "completed")
        except Exception as exc:
            ledger.append(
                engagement_id, "run.failed",
                {"errorType": type(exc).__name__, "message": str(exc)[:500]},
                origin="runtime",
            )
            ledger.transition(engagement_id, "failed", reason=type(exc).__name__)
            raise

    return {
        "engagementId": engagement_id,
        "state": ledger.get_engagement(engagement_id)["state"],
        "source": "actual_agent_run",
        "model": model.model,
        "agentDiscoveryHeuristic": discovery,
        "fixtureOracle": oracle,
        "usage": result["usage"],
        "eventCount": len(ledger.events(engagement_id, limit=1000)),
        "note": "Completed means execution ended, not a comprehensive security assessment.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.getenv("WW_MODEL", ""))
    parser.add_argument("--base-url", default=os.getenv(
        "WW_MODEL_BASE_URL", "http://127.0.0.1:11434/v1"
    ))
    parser.add_argument("--database", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--max-steps", type=int, default=12)
    args = parser.parse_args()
    if not args.model:
        parser.error("--model or WW_MODEL is required")
    model = ChatModel(args.base_url, args.model)
    result = run_local_lab(model, EngagementLedger(args.database), max_steps=args.max_steps)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
