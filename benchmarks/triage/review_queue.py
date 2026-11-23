"""Build an offline analyst review queue from guarded triage decisions."""

import argparse
import json
from pathlib import Path

from benchmarks.triage.reference import (
    SEVERITIES, evidence_exclusion, evidence_records, index_records, read_artifact, timestamp,
)


REVIEW_REASONS = {
    None: "unresolved_unexpected_activity",
    "stale_evidence": "unexpected_activity_needs_fresh_evidence",
    "invalid_evidence_timestamp": "unexpected_activity_needs_timestamp",
    "missing_alert_context": "unexpected_activity_needs_alert_context",
}


def build_queue(alerts_path, decisions_path):
    alerts_digest, alerts = read_artifact(alerts_path, "triage_alerts")
    decisions_digest, run = read_artifact(decisions_path, "triage_decisions")
    if run.get("strategy") != "evidence-aware-guarded" or run.get("alerts_sha256") != alerts_digest:
        raise ValueError("expected guarded decisions for the exact alert input")

    by_id = index_records(alerts.get("alerts"))
    decisions = index_records(run.get("decisions"))
    if by_id.keys() != decisions.keys():
        raise ValueError("decision IDs must exactly match the alerts")

    queue = []
    for key, alert in by_id.items():
        severity = alert.get("severity")
        escalated = decisions[key].get("escalate")
        if severity not in SEVERITIES or type(escalated) is not bool:
            raise ValueError(f"{key}: invalid severity or escalation decision")
        if escalated:
            continue
        if severity == "critical":
            raise ValueError(f"{key}: guarded decision deferred a critical alert")

        observed_at = timestamp(alert.get("observed_at"))
        scope = alert.get("scope")
        signals = []
        for item in evidence_records(alert):
            if item["kind"] != "unexpected_activity":
                continue
            reason = evidence_exclusion(item, observed_at, scope)
            if reason in REVIEW_REASONS:
                signals.append({"evidence_id": item["id"], "reason": REVIEW_REASONS[reason]})
        if signals:
            queue.append({"id": key, "severity": severity, "signals": signals})

    queue.sort(key=lambda item: (-SEVERITIES.index(item["severity"]), item["id"]))
    return {
        "kind": "triage_analyst_review_queue",
        "schema_version": 1,
        "alerts_sha256": alerts_digest,
        "decisions_sha256": decisions_digest,
        "items": queue,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alerts", type=Path)
    parser.add_argument("decisions", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        queue = build_queue(args.alerts, args.decisions)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(queue, stream, indent=2)
            stream.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
