"""Run and score an offline severity-only alert triage benchmark."""

import argparse
import hashlib
import json
from pathlib import Path


SEVERITIES = ("low", "medium", "high", "critical")


def read_artifact(path, kind):
    raw = path.read_bytes()
    artifact = json.loads(raw)
    if (
        not isinstance(artifact, dict)
        or artifact.get("kind") != kind
        or type(artifact.get("schema_version")) is not int
        or artifact["schema_version"] != 1
    ):
        raise ValueError(f"{path}: expected a v1 {kind} artifact")
    return hashlib.sha256(raw).hexdigest(), artifact


def index_records(records):
    if not isinstance(records, list) or not records:
        raise ValueError("expected a nonempty record list")
    indexed = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"].strip():
            raise ValueError("each record requires a nonblank string id")
        if record["id"] in indexed:
            raise ValueError(f"duplicate record id: {record['id']}")
        indexed[record["id"]] = record
    return indexed


def run_baseline(alerts_path):
    digest, artifact = read_artifact(alerts_path, "triage_alerts")
    decisions = []
    for key, record in index_records(artifact.get("alerts")).items():
        severity = record.get("severity")
        if severity not in SEVERITIES:
            raise ValueError(f"{key}: invalid severity")
        decisions.append({"id": key, "escalate": severity in ("high", "critical")})
    return {
        "kind": "triage_decisions",
        "schema_version": 1,
        "strategy": "severity-threshold",
        "alerts_sha256": digest,
        "decisions": decisions,
    }


def score(alerts_path, decisions_path, labels_path):
    alerts_digest, alerts = read_artifact(alerts_path, "triage_alerts")
    decisions_digest, run = read_artifact(decisions_path, "triage_decisions")
    labels_digest, labels = read_artifact(labels_path, "triage_labels")
    strategy = run.get("strategy")
    if not isinstance(strategy, str) or not strategy.strip():
        raise ValueError("decisions must name the triage strategy")
    if run.get("alerts_sha256") != alerts_digest or labels.get("alerts_sha256") != alerts_digest:
        raise ValueError("decisions and labels must reference the exact alert input")

    inputs = index_records(alerts.get("alerts"))
    decisions = index_records(run.get("decisions"))
    expected = index_records(labels.get("labels"))
    if inputs.keys() != decisions.keys() or inputs.keys() != expected.keys():
        raise ValueError("decision and label IDs must exactly match the alerts")

    counts = dict.fromkeys(("true_positive", "false_positive", "true_negative", "false_negative"), 0)
    missed = []
    false_alarms = []
    for key, decision in decisions.items():
        predicted, actual = decision.get("escalate"), expected[key].get("escalate")
        if type(predicted) is not bool or type(actual) is not bool:
            raise ValueError(f"{key}: escalate must be a JSON boolean")
        if predicted:
            if not actual:
                false_alarms.append(key)
            counts["true_positive" if actual else "false_positive"] += 1
        else:
            if actual:
                missed.append(key)
            counts["false_negative" if actual else "true_negative"] += 1
    tp = counts["true_positive"]
    predicted_positives = tp + counts["false_positive"]
    actual_positives = tp + counts["false_negative"]
    return {
        "kind": "triage_score",
        "schema_version": 1,
        "strategy": strategy,
        "alerts_sha256": alerts_digest,
        "decisions_sha256": decisions_digest,
        "labels_sha256": labels_digest,
        "counts": counts,
        "precision": tp / predicted_positives if predicted_positives else None,
        "recall": tp / actual_positives if actual_positives else None,
        "missed_alert_ids": missed,
        "false_alarm_ids": false_alarms,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    baseline = commands.add_parser("baseline", help="produce decisions from alerts alone")
    baseline.add_argument("alerts", type=Path)
    baseline.add_argument("--output", required=True, type=Path)
    scorer = commands.add_parser("score", help="compare decisions with held-aside labels")
    scorer.add_argument("alerts", type=Path)
    scorer.add_argument("decisions", type=Path)
    scorer.add_argument("labels", type=Path)
    scorer.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = (
            run_baseline(args.alerts) if args.command == "baseline"
            else score(args.alerts, args.decisions, args.labels)
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
