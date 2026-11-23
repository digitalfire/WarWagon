"""Check a local analyst evidence update against a frozen triage review queue.

The update's observation uses the existing evidence fields and may be eligible
only within the original alert's 24-hour lookback window. Eligibility records
scope and time checks on caller-supplied metadata. It leaves severity and
escalation decisions unchanged.
"""

import argparse
import json
from pathlib import Path
import re

from benchmarks.triage.reference import (
    evidence_exclusion, evidence_records, index_records, read_artifact, timestamp,
)
from benchmarks.triage.review_queue import build_queue


# Require an explicit date, time and offset for the replacement observation.
UPDATE_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)


def recheck_evidence(alerts_path, decisions_path, queue_path, update_path):
    queue_digest, queue = read_artifact(queue_path, "triage_analyst_review_queue")
    expected_queue = build_queue(alerts_path, decisions_path)
    if any(queue.get(field) != expected_queue[field] for field in (
        "alerts_sha256", "decisions_sha256", "items",
    )):
        raise ValueError("queue must match the alerts, guarded decisions and queued evidence")

    update_digest, update = read_artifact(update_path, "triage_analyst_evidence_update")
    if update.get("queue_sha256") != queue_digest:
        raise ValueError("update must reference the exact review queue")
    alert_id = update.get("alert_id")
    evidence_id = update.get("evidence_id")
    if not any(
        item["id"] == alert_id and any(signal["evidence_id"] == evidence_id for signal in item["signals"])
        for item in expected_queue["items"]
    ):
        raise ValueError("update must reference a queued alert and evidence pair")

    alerts_digest, alerts = read_artifact(alerts_path, "triage_alerts")
    if alerts_digest != expected_queue["alerts_sha256"]:
        raise ValueError("alert input changed during the recheck")
    original = index_records(alerts["alerts"])[alert_id]
    replacement, = evidence_records({"id": alert_id, "evidence": [update.get("observation")]})

    recorded_at = replacement.get("recorded_at")
    if not isinstance(recorded_at, str) or UPDATE_TIMESTAMP.fullmatch(recorded_at) is None:
        reason = "invalid_evidence_timestamp"
    else:
        reason = evidence_exclusion(
            replacement, timestamp(original.get("observed_at")), original.get("scope"),
        )

    return {
        "kind": "triage_analyst_evidence_recheck",
        "schema_version": 1,
        "alerts_sha256": alerts_digest,
        "decisions_sha256": expected_queue["decisions_sha256"],
        "queue_sha256": queue_digest,
        "update_sha256": update_digest,
        "alert_id": alert_id,
        "original_evidence_id": evidence_id,
        "replacement_evidence_id": replacement["id"],
        "status": "eligible" if reason is None else "ineligible",
        "reason": reason,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alerts", type=Path)
    parser.add_argument("decisions", type=Path)
    parser.add_argument("queue", type=Path)
    parser.add_argument(
        "update", type=Path,
        help=("v1 triage_analyst_evidence_update JSON with queue_sha256, alert_id, "
              "evidence_id and an observation using the triage evidence fields"),
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = recheck_evidence(args.alerts, args.decisions, args.queue, args.update)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
