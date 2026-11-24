"""WarWagon real-model acceptance harness for a bounded two-worker local lab.

A green report establishes a *recorded integration run* with the configured
model endpoint and tool observations. It is not proof of independent model
intelligence, independent finding verification, or provider authenticity.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from warwagon.engagement_store import DEFAULT_PATH, EngagementLedger
from warwagon.model import ChatModel
from warwagon.preflight import check as preflight_check
from warwagon.worker_runtime import TaskQueue, run_two_worker_lab

TEST_MODEL_RE = re.compile(r"(?:test.double|scripted|mock|fake.model)", re.I)


def audit_run(ledger: EngagementLedger, engagement_id: str, *, expected_model: str) -> dict:
    """Review persisted evidence without emitting raw requests, responses or secrets."""
    engagement = ledger.get_engagement(engagement_id)
    queue = TaskQueue(ledger)
    tasks = queue.tasks(engagement_id)
    budget = queue.budget(engagement_id)
    events = []
    cursor = 0
    while True:
        page = ledger.events(engagement_id, after=cursor, limit=500)
        if not page:
            break
        events.extend(page)
        cursor = page[-1]["sequence"]
    kinds = [event["kind"] for event in events]
    model_events = [e for e in events if e["kind"] == "model.response"]
    invocations = [e for e in events if e["kind"] == "tool.invocation"]
    observations = [e for e in events if e["kind"] == "tool.observation"]
    claims = [e for e in events if e["kind"] == "task.claimed"]
    worker_ids = {e["payload"].get("workerId") for e in claims if e["payload"].get("workerId")}
    claimed_tasks = {e["payload"].get("taskId") for e in claims}
    completed_tasks = {e["payload"].get("taskId") for e in events if e["kind"] == "task.completed"}
    model_names = {e["payload"].get("model") for e in model_events}
    invocation_keys = {
        (e["payload"].get("taskId"), e["payload"].get("workerId"),
         e["payload"].get("toolCallId")) for e in invocations
    }
    observation_keys = {
        (e["payload"].get("taskId"), e["payload"].get("workerId"),
         e["payload"].get("toolCallId")) for e in observations
    }
    first_finish = next((i for i, event in enumerate(events)
                         if event["kind"] in ("task.completed", "task.failed", "task.blocked")), None)
    both_claimed_before_first_finish = (
        first_finish is not None and
        len({e["payload"].get("taskId") for e in events[:first_finish]
             if e["kind"] == "task.claimed"}) >= 2
    )
    usage_events = [e for e in events if e["kind"] == "budget.usage.recorded"]
    usage_ids = {e["payload"].get("callNumber") for e in usage_events}
    call_events = [e for e in events if e["kind"] == "budget.call.reserved"]
    call_ids = {e["payload"].get("callNumber") for e in call_events}
    end_by_call = {
        e["payload"].get("callNumber"): e["sequence"] for e in usage_events
    }
    intervals = [
        (e["sequence"], end_by_call[e["payload"]["callNumber"]],
         e["payload"].get("workerId"))
        for e in call_events
        if e["payload"].get("callNumber") in end_by_call
    ]
    overlapping_calls = any(
        left[2] != right[2] and left[0] < right[1] and right[0] < left[1]
        for index, left in enumerate(intervals) for right in intervals[index + 1:]
    )
    failures = [e for e in events if e["kind"] in ("task.failed", "run.failed", "engagement.failed")]
    report = {
        "schemaVersion": 1,
        "kind": "warwagon_local_model_validation",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "engagementId": engagement_id,
        "modelExpected": expected_model,
        "modelReported": sorted(str(value) for value in model_names),
        "state": engagement["state"],
        "source": "persisted_local_lab",
        "eventCount": len(events),
        "eventSequenceStart": events[0]["sequence"] if events else None,
        "eventSequenceEnd": cursor if events else None,
        "eventDigests": [{"sequence": e["sequence"], "sha256": e["payloadSha256"]} for e in events],
        "taskStatuses": {row["task_id"]: row["status"] for row in tasks},
        "workersSeen": sorted(worker_ids),
        "eventsByKind": {kind: kinds.count(kind) for kind in sorted(set(kinds))},
        "budget": {
            "modelCallsReserved": budget["used_calls"],
            "maxModelCalls": budget["max_calls"],
            "reportedTokens": budget["used_tokens"],
            "maxReportedTokens": budget["max_tokens"],
            "usageComplete": bool(budget["usage_complete"]),
            "overrunTokens": max(0, budget["used_tokens"] - budget["max_tokens"]),
        },
        "warnings": [],
    }
    checks = {
        "recorded_terminal_success": engagement["state"] == "completed" and not failures,
        "expected_two_distinct_tasks": len(tasks) == 2 and len(claimed_tasks) == 2,
        "two_workers_observed": len(worker_ids) == 2,
        "overlapping_task_claims_observed": both_claimed_before_first_finish,
        "overlapping_model_call_windows_observed": overlapping_calls,
        "all_tasks_completed": len(completed_tasks) == 2 and all(t["status"] == "completed" for t in tasks),
        "model_identity_reported": bool(expected_model) and bool(model_events)
            and model_names == {expected_model} and not TEST_MODEL_RE.search(expected_model),
        "model_calls_observed": len(model_events) >= 2,
        "tool_invocation_observed": len(invocations) >= 1,
        "http_tool_observation_observed": any(
            e["payload"].get("tool") == "lab_http_get"
            and isinstance(e["payload"].get("result"), dict)
            and isinstance(e["payload"]["result"].get("status"), int)
            for e in observations
        ),
        "observation_bound_to_invocation": bool(observation_keys)
            and observation_keys.issubset(invocation_keys),
        "call_reservations_within_budget": 0 < budget["used_calls"] <= budget["max_calls"]
            and len(call_ids) == budget["used_calls"],
        "all_reserved_calls_accounted": usage_ids == call_ids and bool(budget["usage_complete"]),
        "monotonic_event_sequences": all(
            earlier["sequence"] < later["sequence"]
            for earlier, later in zip(events, events[1:])
        ),
        "local_fixture_target_only": urlsplit(engagement["target"]).hostname in ("127.0.0.1", "localhost"),
        "no_verified_vulnerability_event": not any(
            e["kind"] == "finding.verified" for e in events
        ),
    }
    if budget["used_tokens"] > budget["max_tokens"]:
        report["warnings"].append(
            "Provider-reported token ceiling exceeded by in-flight calls; cap is not strict.")
    if "lab.fixture.oracle" in kinds:
        report["warnings"].append(
            "Fixture oracle confirms only controlled lab behavior, not a real-world vulnerability.")
    if "lab.task.heuristics" in kinds:
        report["warnings"].append(
            "Agent discovery scores are narrow heuristic labels, not independent finding verification.")
    report["checks"] = checks
    report["passed"] = all(bool(value) for value in checks.values())
    report["qualification"] = (
        "Pass establishes persisted model/tool evidence and overlapping model-call reservation windows. "
        "A model name in self-reported events does not cryptographically prove endpoint identity "
        "or independently establish security research effectiveness."
    )
    return report


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"output already exists: {path}")
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_validation(model: ChatModel, database: Path, *, workers: int, model_calls: int,
                   tokens: int, seconds: int, steps: int, http_rps: int,
                   output: Path) -> dict:
    """Do not construct a run manifest if the real tool-call preflight fails."""
    if TEST_MODEL_RE.search(model.model):
        raise ValueError("model name resembles a test double; refusing real validation label")
    preflight = preflight_check(model)
    if not preflight["tool_call_correct"]:
        raise ValueError("model tool-calling preflight failed: " + str(preflight["diagnostic"]))
    ledger = EngagementLedger(database)
    result = run_two_worker_lab(
        lambda: ChatModel(model.base_url, model.model, timeout=model.timeout,
                          api_key=model.api_key),
        ledger, workers=workers, max_calls=model_calls, max_tokens=tokens,
        max_seconds=seconds, max_steps=steps, http_rps=http_rps,
    )
    report = audit_run(ledger, result["engagementId"], expected_model=model.model)
    report["preflight"] = {
        "toolCallCorrect": True,
        "responseModel": preflight.get("response_model"),
        "finishReason": preflight.get("finish_reason"),
        "elapsedSeconds": preflight.get("elapsed_seconds"),
        "endpointHost": urlsplit(model.base_url).hostname,
    }
    write_report(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    runner = commands.add_parser("run", help="preflight, run local workers, and audit result")
    auditor = commands.add_parser("audit", help="audit an already persisted engagement")
    for sub in (runner, auditor):
        sub.add_argument("--database", type=Path, default=DEFAULT_PATH)
        sub.add_argument("--model", required=True)
        sub.add_argument("--output", type=Path, required=True)
    runner.add_argument("--base-url", default=os.getenv("WW_MODEL_BASE_URL", "http://127.0.0.1:11434/v1"))
    runner.add_argument("--workers", type=int, choices=(1, 2), default=2)
    runner.add_argument("--model-calls", type=int, default=20)
    runner.add_argument("--tokens", type=int, default=100000)
    runner.add_argument("--seconds", type=int, default=120)
    runner.add_argument("--steps", type=int, default=8)
    runner.add_argument("--http-rps", type=int, default=30)
    auditor.add_argument("--engagement-id", required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            report = run_validation(
                ChatModel(args.base_url, args.model), args.database,
                workers=args.workers, model_calls=args.model_calls,
                tokens=args.tokens, seconds=args.seconds, steps=args.steps,
                http_rps=args.http_rps, output=args.output,
            )
        else:
            report = audit_run(
                EngagementLedger(args.database), args.engagement_id,
                expected_model=args.model,
            )
            write_report(args.output, report)
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"error": type(exc).__name__, "detail": str(exc)}))
        sys.exit(2)
    print(json.dumps({"output": str(args.output), "engagementId": report["engagementId"],
                      "passed": report["passed"], "checks": report["checks"]}, indent=2))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
