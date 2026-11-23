"""Record an assessor's checklist judgments for one ARC review."""

import argparse
import hashlib
import json
from pathlib import Path

from warwagon.arc import ROLES, validate_response
from warwagon.arc_evidence import is_digest, nonblank


OUTCOMES = ("met", "not_met", "inconclusive")


def read_json(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return hashlib.sha256(raw).hexdigest(), value


def read_checklist(path):
    digest, checklist = read_json(path)
    if (
        checklist.get("kind") != "arc_review_quality_checklist"
        or checklist.get("schema_version") != 1
        or not is_digest(checklist.get("proposal_sha256"))
        or checklist.get("role") not in tuple(ROLES)
        or not isinstance(checklist.get("items"), list)
        or not checklist["items"]
    ):
        raise ValueError("expected a v1 ARC quality checklist for one proposal and role")
    items = {}
    for item in checklist["items"]:
        if not isinstance(item, dict) or not nonblank(item.get("id")) or not nonblank(item.get("criterion")):
            raise ValueError("each checklist item requires a nonblank id and criterion")
        if item["id"] in items:
            raise ValueError(f"duplicate checklist item: {item['id']}")
        items[item["id"]] = item["criterion"]
    return digest, checklist, items


def build_scorecard(report_path, checklist_path, judgments_path, assessor):
    if not nonblank(assessor):
        raise ValueError("assessor must be nonblank")
    checklist_digest, checklist, items = read_checklist(checklist_path)
    report_digest, report = read_json(report_path)
    if (
        report.get("kind") != "arc_first_pass_report"
        or report.get("schema_version") != 1
        or report.get("proposal_sha256") != checklist["proposal_sha256"]
        or not isinstance(report.get("attempts_by_role"), dict)
    ):
        raise ValueError("expected a v1 ARC report for the checklist proposal")

    role = checklist["role"]
    attempts = report["attempts_by_role"].get(role)
    if not isinstance(attempts, list) or not attempts or not isinstance(attempts[-1], dict):
        raise ValueError("checklist role has no recorded ARC attempt")
    attempt = attempts[-1]
    review = attempt.get("record")
    if (
        not is_digest(attempt.get("artifact_sha256"))
        or not isinstance(review, dict)
        or review.get("role") != role
        or review.get("status") != "valid"
    ):
        raise ValueError("checklist role has no current valid ARC review")
    validate_response(json.dumps(review.get("review")))

    judgments_digest, submission = read_json(judgments_path)
    if submission.get("report_sha256") != report_digest or submission.get("checklist_sha256") != checklist_digest:
        raise ValueError("judgments must reference the exact ARC report and checklist")
    judgments = submission.get("judgments")
    if not isinstance(judgments, dict) or set(judgments) != set(items):
        raise ValueError("judgments must cover exactly the checklist item IDs")
    counts = dict.fromkeys(OUTCOMES, 0)
    results = []
    for item_id, criterion in items.items():
        judgment = judgments[item_id]
        if (
            not isinstance(judgment, dict)
            or judgment.get("outcome") not in OUTCOMES
            or not nonblank(judgment.get("rationale"))
        ):
            raise ValueError(f"{item_id}: expected a valid outcome and nonblank rationale")
        result = judgment["outcome"]
        counts[result] += 1
        results.append({
            "id": item_id,
            "criterion": criterion,
            "outcome": result,
            "rationale": judgment["rationale"].strip(),
        })

    return {
        "kind": "arc_review_quality_scorecard",
        "schema_version": 1,
        "proposal_sha256": checklist["proposal_sha256"],
        "role": role,
        "report_sha256": report_digest,
        "review_artifact_sha256": attempt["artifact_sha256"],
        "checklist_sha256": checklist_digest,
        "judgments_sha256": judgments_digest,
        "assessor": assessor.strip(),
        "attribution": "caller-supplied",
        "outcome_counts": counts,
        "items": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--checklist", required=True, type=Path)
    parser.add_argument("--judgments", required=True, type=Path)
    parser.add_argument("--assessor", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        artifact = build_scorecard(args.report, args.checklist, args.judgments, args.assessor)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(artifact, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
