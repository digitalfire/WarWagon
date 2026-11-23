"""Measure the incident coverage and workload of an offline analyst queue."""

import argparse
import json
from pathlib import Path

from benchmarks.triage.reference import index_records, read_artifact, score


def score_queue(alerts_path, decisions_path, labels_path, queue_path):
    triage = score(alerts_path, decisions_path, labels_path)
    run_digest, run = read_artifact(decisions_path, "triage_decisions")
    queue_digest, queue = read_artifact(queue_path, "triage_analyst_review_queue")
    if (
        triage["decisions_sha256"] != run_digest
        or run["strategy"] != "evidence-aware-guarded"
        or queue.get("alerts_sha256") != triage["alerts_sha256"]
        or queue.get("decisions_sha256") != run_digest
    ):
        raise ValueError("queue must reference the exact guarded decisions and alert input")

    items = queue.get("items")
    if not isinstance(items, list):
        raise ValueError("queue items must be an array")
    queued_ids = list(index_records(items)) if items else []
    decisions = index_records(run["decisions"])
    if any(key not in decisions or decisions[key]["escalate"] for key in queued_ids):
        raise ValueError("queue items must be deferred alerts in the decision artifact")

    missed = set(triage["missed_alert_ids"])
    surfaced = [key for key in queued_ids if key in missed]
    benign = [key for key in queued_ids if key not in missed]
    return {
        "kind": "triage_analyst_queue_score",
        "schema_version": 1,
        "alerts_sha256": triage["alerts_sha256"],
        "decisions_sha256": run_digest,
        "labels_sha256": triage["labels_sha256"],
        "queue_sha256": queue_digest,
        "deferred_alert_count": sum(not item["escalate"] for item in decisions.values()),
        "queue_size": len(queued_ids),
        "missed_incident_count": len(missed),
        "surfaced_miss_ids": surfaced,
        "unsurfaced_miss_ids": sorted(missed - set(surfaced)),
        "benign_review_ids": benign,
        "queue_precision": len(surfaced) / len(queued_ids) if queued_ids else None,
        "miss_coverage": len(surfaced) / len(missed) if missed else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alerts", type=Path)
    parser.add_argument("decisions", type=Path)
    parser.add_argument("labels", type=Path)
    parser.add_argument("queue", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = score_queue(args.alerts, args.decisions, args.labels, args.queue)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
