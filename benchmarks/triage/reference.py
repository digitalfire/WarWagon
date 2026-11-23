"""Run and score offline defensive alert triage candidates."""

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


def severity_decision(record):
    return {"escalate": record["severity"] in ("high", "critical")}


EVIDENCE_KINDS = (
    "unexpected_activity", "approved_activity", "resolved_duplicate", "unconfirmed_signal",
)


def evidence_decision(record):
    evidence = record.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError(f"{record['id']}: evidence must be an array")
    by_kind = {kind: [] for kind in EVIDENCE_KINDS}
    for item in index_records(evidence).values() if evidence else ():
        source, kind = item.get("source"), item.get("kind")
        if not isinstance(source, str) or not source.strip() or kind not in EVIDENCE_KINDS:
            raise ValueError(f"{record['id']}: evidence requires a nonblank source and known kind")
        by_kind[kind].append(item)

    unexpected = by_kind["unexpected_activity"]
    context = by_kind["approved_activity"] + by_kind["resolved_duplicate"]

    def supported(items):
        return len({item["source"].strip().casefold() for item in items}) >= 2

    if supported(unexpected):
        return {
            "escalate": True, "reason": "corroborated_unexpected_activity",
            "evidence_ids": [item["id"] for item in unexpected],
        }
    if unexpected and context:
        return {
            "escalate": True, "reason": "conflicting_evidence",
            "evidence_ids": [item["id"] for item in unexpected + context],
        }
    for kind in ("approved_activity", "resolved_duplicate"):
        if supported(by_kind[kind]):
            return {
                "escalate": False, "reason": f"corroborated_{kind}",
                "evidence_ids": [item["id"] for item in by_kind[kind]],
            }
    return {**severity_decision(record), "reason": "severity_fallback", "evidence_ids": []}


def run_policy(alerts_path, strategy, decide):
    digest, artifact = read_artifact(alerts_path, "triage_alerts")
    decisions = []
    for key, record in index_records(artifact.get("alerts")).items():
        if record.get("severity") not in SEVERITIES:
            raise ValueError(f"{key}: invalid severity")
        decisions.append({"id": key, **decide(record)})
    return {
        "kind": "triage_decisions",
        "schema_version": 1,
        "strategy": strategy,
        "alerts_sha256": digest,
        "decisions": decisions,
    }


def run_baseline(alerts_path):
    return run_policy(alerts_path, "severity-threshold", severity_decision)


def run_candidate(alerts_path):
    return run_policy(alerts_path, "evidence-aware", evidence_decision)


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
    candidate = commands.add_parser("candidate", help="produce evidence-aware decisions from alerts alone")
    candidate.add_argument("alerts", type=Path)
    candidate.add_argument("--output", required=True, type=Path)
    scorer = commands.add_parser("score", help="compare decisions with held-aside labels")
    scorer.add_argument("alerts", type=Path)
    scorer.add_argument("decisions", type=Path)
    scorer.add_argument("labels", type=Path)
    scorer.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "score":
            result = score(args.alerts, args.decisions, args.labels)
        else:
            run = run_baseline if args.command == "baseline" else run_candidate
            result = run(args.alerts)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
