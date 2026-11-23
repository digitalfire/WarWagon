"""Check ARC evidence integrity offline against explicitly supplied local files.

Use --evidence INDEX PATH for each one-based entry in the response and
--challenge PATH to check the linked challenge and proposal. The report
records byte integrity. Evidence sufficiency and review decisions remain
with the reviewer. Exit codes are 0 for a match, 1 for an incomplete or
mismatched check, and 2 for invalid input.
"""

import argparse
import hashlib
import json
from pathlib import Path

from warwagon.arc import ROLES
from warwagon.arc_disposition import valid_evidence_reference
from warwagon.arc_evidence import evidence_reference, is_digest, nonblank, read_challenge


def read_response(path):
    raw = path.read_bytes()
    response = json.loads(raw)
    if (
        not isinstance(response, dict)
        or response.get("kind") != "arc_challenge_evidence_response"
        or type(response.get("schema_version")) is not int
        or response["schema_version"] != 1
        or not is_digest(response.get("proposal_sha256"))
        or not is_digest(response.get("challenge_sha256"))
        or response.get("responder_role") not in tuple(ROLES)
        or not nonblank(response.get("response"))
        or not isinstance(response.get("evidence"), list)
        or not response["evidence"]
        or not all(valid_evidence_reference(item) for item in response["evidence"])
    ):
        raise ValueError("expected an ARC v1 challenge evidence response")
    return hashlib.sha256(raw).hexdigest(), response


def check_evidence(index, expected, path):
    result = {
        "index": index,
        "expected_sha256": expected["sha256"],
        "expected_size_bytes": expected["size_bytes"],
    }
    if path is None:
        return {**result, "status": "missing"}

    try:
        path.stat()
        actual = evidence_reference(path)
    except FileNotFoundError:
        return {**result, "status": "missing"}
    except (OSError, ValueError):
        return {**result, "status": "unreadable"}

    matches = actual["sha256"] == expected["sha256"] and actual["size_bytes"] == expected["size_bytes"]
    return {
        **result,
        "status": "match" if matches else "mismatch",
        "actual_sha256": actual["sha256"],
        "actual_size_bytes": actual["size_bytes"],
    }


def check_challenge(response, path):
    result = {"expected_sha256": response["challenge_sha256"]}
    if path is None:
        return {**result, "status": "not_checked"}

    try:
        digest, challenge = read_challenge(path)
    except FileNotFoundError:
        return {**result, "status": "missing"}

    proposal_matches = challenge["proposal_sha256"] == response["proposal_sha256"]
    return {
        **result,
        "status": "match" if digest == response["challenge_sha256"] and proposal_matches else "mismatch",
        "actual_sha256": digest,
        "proposal_matches": proposal_matches,
    }


def verify_response(response_path, evidence_paths, challenge_path=None):
    response_digest, response = read_response(response_path)
    entries = response["evidence"]
    if any(index < 1 or index > len(entries) for index in evidence_paths):
        raise ValueError(f"evidence indices must be between 1 and {len(entries)}")

    evidence = [
        check_evidence(index, expected, evidence_paths.get(index))
        for index, expected in enumerate(entries, start=1)
    ]
    challenge = check_challenge(response, challenge_path)
    all_match = all(item["status"] == "match" for item in evidence)
    return {
        "kind": "arc_evidence_integrity_report",
        "schema_version": 1,
        "response_sha256": response_digest,
        "proposal_sha256": response["proposal_sha256"],
        "challenge": challenge,
        "evidence": evidence,
        "verified": all_match and challenge["status"] in ("match", "not_checked"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path)
    parser.add_argument("--challenge", type=Path, help="optional original challenge to verify")
    parser.add_argument(
        "--evidence", action="append", nargs=2, default=[], metavar=("INDEX", "PATH"),
        help="explicit local file for a one-based response entry; may be repeated",
    )
    args = parser.parse_args()
    try:
        evidence_paths = {}
        for raw_index, path in args.evidence:
            index = int(raw_index)
            if index in evidence_paths:
                raise ValueError(f"duplicate evidence index: {index}")
            evidence_paths[index] = Path(path)
        report = verify_response(args.response, evidence_paths, args.challenge)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")

    print(json.dumps(report, indent=2))
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
