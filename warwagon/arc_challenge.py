"""Record a structured challenge to a current ARC review item."""

import argparse
import hashlib
import json
from pathlib import Path

from warwagon.arc import REVIEW_LISTS, ROLES, validate_response


def build_challenge(report_path, challenged_role, field, index, challenger_role, challenge, requested_evidence):
    if challenged_role not in ROLES or challenger_role not in ROLES:
        raise ValueError("both roles must be known ARC roles")
    if challenged_role == challenger_role:
        raise ValueError("the challenger must be a different ARC role")
    if field not in REVIEW_LISTS or index < 0:
        raise ValueError("select a review list and a nonnegative item index")
    if not challenge.strip() or not requested_evidence.strip():
        raise ValueError("challenge and requested evidence must be nonblank")

    raw = report_path.read_bytes()
    report = json.loads(raw)
    if (
        not isinstance(report, dict)
        or report.get("kind") != "arc_first_pass_report"
        or report.get("schema_version") != 1
        or not isinstance(report.get("proposal_sha256"), str)
        or not isinstance(report.get("attempts_by_role"), dict)
    ):
        raise ValueError("expected an ARC v1 first-pass report")

    attempts = report["attempts_by_role"].get(challenged_role)
    if not isinstance(attempts, list) or not attempts or not isinstance(attempts[-1], dict):
        raise ValueError("challenged role has no recorded attempt")
    current = attempts[-1]
    record = current.get("record")
    if (
        not isinstance(current.get("artifact_sha256"), str)
        or not isinstance(record, dict)
        or record.get("role") != challenged_role
        or record.get("status") != "valid"
    ):
        raise ValueError("challenged role has no current valid review")

    items = validate_response(json.dumps(record.get("review")))[field]
    if index >= len(items):
        raise ValueError("review item index is outside the selected list")

    return {
        "kind": "arc_review_challenge",
        "schema_version": 1,
        "status": "open",
        "proposal_sha256": report["proposal_sha256"],
        "report_sha256": hashlib.sha256(raw).hexdigest(),
        "challenger_role": challenger_role,
        "target": {
            "role": challenged_role,
            "artifact_sha256": current["artifact_sha256"],
            "field": field,
            "index": index,
            "text": items[index],
        },
        "challenge": challenge.strip(),
        "requested_evidence": requested_evidence.strip(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--role", required=True, choices=ROLES, help="role whose review is challenged")
    parser.add_argument("--field", required=True, choices=REVIEW_LISTS)
    parser.add_argument("--index", required=True, type=int, help="zero-based index in the selected list")
    parser.add_argument("--challenger", required=True, choices=ROLES)
    parser.add_argument("--challenge", required=True)
    parser.add_argument("--requested-evidence", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        artifact = build_challenge(
            args.report, args.role, args.field, args.index, args.challenger,
            args.challenge, args.requested_evidence,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(artifact, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
