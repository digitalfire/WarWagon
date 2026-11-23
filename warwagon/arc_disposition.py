"""Record a caller-supplied disposition for an ARC challenge and its evidence response.

Run python -m warwagon.arc_disposition --help for the required inputs.
The record links exact input bytes. It does not authenticate the maintainer,
verify the underlying evidence files, or approve a proposal.
"""

import argparse
import hashlib
import json
from pathlib import Path

from warwagon.arc import ROLES
from warwagon.arc_evidence import is_digest, nonblank, read_challenge


OUTCOMES = ("addressed", "unresolved", "needs-evidence")


def valid_evidence_reference(reference):
    return (
        isinstance(reference, dict)
        and nonblank(reference.get("path"))
        and is_digest(reference.get("sha256"))
        and type(reference.get("size_bytes")) is int
        and reference["size_bytes"] >= 0
    )


def build_disposition(challenge_path, response_path, maintainer, outcome, rationale):
    if not nonblank(maintainer) or not nonblank(rationale):
        raise ValueError("maintainer and rationale must be nonblank")
    if outcome not in OUTCOMES:
        raise ValueError("unknown ARC challenge disposition outcome")

    challenge_sha256, challenge = read_challenge(challenge_path)
    response_bytes = response_path.read_bytes()
    response = json.loads(response_bytes)
    if (
        not isinstance(response, dict)
        or response.get("kind") != "arc_challenge_evidence_response"
        or type(response.get("schema_version")) is not int
        or response["schema_version"] != 1
        or response.get("responder_role") not in tuple(ROLES)
        or not nonblank(response.get("response"))
        or not isinstance(response.get("evidence"), list)
        or not response["evidence"]
        or not all(valid_evidence_reference(item) for item in response["evidence"])
    ):
        raise ValueError("expected an ARC v1 challenge evidence response")
    if response.get("proposal_sha256") != challenge["proposal_sha256"]:
        raise ValueError("response proposal digest does not match the challenge")
    if response.get("challenge_sha256") != challenge_sha256:
        raise ValueError("response challenge digest does not match the supplied challenge")

    return {
        "kind": "arc_challenge_disposition",
        "schema_version": 1,
        "proposal_sha256": challenge["proposal_sha256"],
        "challenge_sha256": challenge_sha256,
        "evidence_response_sha256": hashlib.sha256(response_bytes).hexdigest(),
        "maintainer": maintainer.strip(),
        "attribution": "caller-supplied",
        "outcome": outcome,
        "rationale": rationale.strip(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("challenge", type=Path, help="original ARC challenge JSON")
    parser.add_argument("evidence_response", type=Path, help="linked ARC evidence response JSON")
    parser.add_argument("--maintainer", required=True, help="caller-supplied maintainer label")
    parser.add_argument("--outcome", required=True, choices=OUTCOMES, help="disposition of this challenge")
    parser.add_argument("--rationale", required=True, help="maintainer's reason for the disposition")
    parser.add_argument("--output", required=True, type=Path, help="path to a new disposition JSON file")
    args = parser.parse_args()

    try:
        artifact = build_disposition(
            args.challenge, args.evidence_response, args.maintainer, args.outcome, args.rationale,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(artifact, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
