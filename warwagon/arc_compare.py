"""Compare two ARC quality scorecards against their shared frozen checklist.

The comparison preserves both outcomes and rationales for each criterion,
marks inconclusive items explicitly, and retains exact input digests.
Assessor labels come from the scorecards.
"""

import argparse
import json
from pathlib import Path

from warwagon.arc_evidence import is_digest, nonblank
from warwagon.arc_scorecard import OUTCOMES, read_checklist, read_json


SOURCE_DIGESTS = ("report_sha256", "review_artifact_sha256", "judgments_sha256")


def load_scorecard(path, checklist_digest, checklist, criteria):
    scorecard_digest, scorecard = read_json(path)
    if (
        scorecard.get("kind") != "arc_review_quality_scorecard"
        or type(scorecard.get("schema_version")) is not int
        or scorecard["schema_version"] != 1
        or any(not is_digest(scorecard.get(field)) for field in SOURCE_DIGESTS)
        or not nonblank(scorecard.get("assessor"))
        or scorecard.get("attribution") != "caller-supplied"
    ):
        raise ValueError(f"{path}: expected a v1 ARC quality scorecard with provenance")
    if (
        scorecard.get("proposal_sha256") != checklist["proposal_sha256"]
        or scorecard.get("role") != checklist["role"]
        or scorecard.get("checklist_sha256") != checklist_digest
    ):
        raise ValueError(f"{path}: scorecard must reference the exact checklist, proposal, and role")

    rows = scorecard.get("items")
    if not isinstance(rows, list):
        raise ValueError(f"{path}: scorecard items must be an array")
    counts = dict.fromkeys(OUTCOMES, 0)
    items = {}
    for row in rows:
        if (
            not isinstance(row, dict)
            or not nonblank(row.get("id"))
            or row.get("outcome") not in OUTCOMES
            or not nonblank(row.get("rationale"))
        ):
            raise ValueError(f"{path}: invalid scorecard item")
        item_id = row["id"]
        if item_id in items:
            raise ValueError(f"{path}: duplicate scorecard item: {item_id}")
        if item_id not in criteria or row.get("criterion") != criteria[item_id]:
            raise ValueError(f"{path}: criterion differs from the frozen checklist: {item_id}")
        items[item_id] = {"outcome": row["outcome"], "rationale": row["rationale"]}
        counts[row["outcome"]] += 1

    if items.keys() != criteria.keys():
        raise ValueError(f"{path}: scorecard must cover every frozen checklist item")
    recorded_counts = scorecard.get("outcome_counts")
    if (
        not isinstance(recorded_counts, dict)
        or any(type(value) is not int for value in recorded_counts.values())
        or recorded_counts != counts
    ):
        raise ValueError(f"{path}: recorded outcome counts do not match scorecard items")

    source = {
        "scorecard_sha256": scorecard_digest,
        **{field: scorecard[field] for field in SOURCE_DIGESTS},
        "assessor": scorecard["assessor"],
        "attribution": scorecard["attribution"],
        "outcome_counts": counts,
    }
    return source, items


def compare_scorecards(left_path, right_path, checklist_path):
    checklist_digest, checklist, criteria = read_checklist(checklist_path)
    left, left_items = load_scorecard(left_path, checklist_digest, checklist, criteria)
    right, right_items = load_scorecard(right_path, checklist_digest, checklist, criteria)
    if (
        all(left[field] == right[field] for field in (*SOURCE_DIGESTS, "assessor"))
        and left_items == right_items
    ):
        raise ValueError("comparison requires two distinct scorecards")

    items = []
    for item_id, criterion in criteria.items():
        left_item, right_item = left_items[item_id], right_items[item_id]
        left_outcome, right_outcome = left_item["outcome"], right_item["outcome"]
        items.append({
            "id": item_id,
            "criterion": criterion,
            "left": left_item,
            "right": right_item,
            "outcomes_differ": left_outcome != right_outcome,
            "has_inconclusive": "inconclusive" in (left_outcome, right_outcome),
        })
    return {
        "kind": "arc_review_quality_comparison",
        "schema_version": 1,
        "proposal_sha256": checklist["proposal_sha256"],
        "role": checklist["role"],
        "checklist_sha256": checklist_digest,
        "left": left,
        "right": right,
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path, help="first ARC quality scorecard")
    parser.add_argument("right", type=Path, help="second ARC quality scorecard")
    parser.add_argument("--checklist", required=True, type=Path, help="original frozen checklist JSON")
    parser.add_argument("--output", required=True, type=Path, help="new comparison JSON file")
    args = parser.parse_args()
    try:
        result = compare_scorecards(args.left, args.right, args.checklist)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
