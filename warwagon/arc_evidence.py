"""Record a local evidence response to an open ARC challenge."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from warwagon.arc import REVIEW_LISTS, ROLES


def is_digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def read_challenge(path):
    raw = path.read_bytes()
    challenge = json.loads(raw)
    if (
        not isinstance(challenge, dict)
        or challenge.get("kind") != "arc_review_challenge"
        or type(challenge.get("schema_version")) is not int
        or challenge["schema_version"] != 1
        or challenge.get("status") != "open"
        or not is_digest(challenge.get("proposal_sha256"))
        or not is_digest(challenge.get("report_sha256"))
        or challenge.get("challenger_role") not in tuple(ROLES)
        or not nonblank(challenge.get("challenge"))
        or not nonblank(challenge.get("requested_evidence"))
    ):
        raise ValueError("expected an open ARC v1 review challenge")

    target = challenge.get("target")
    if (
        not isinstance(target, dict)
        or target.get("role") not in tuple(ROLES)
        or target["role"] == challenge["challenger_role"]
        or not is_digest(target.get("artifact_sha256"))
        or target.get("field") not in REVIEW_LISTS
        or type(target.get("index")) is not int
        or target["index"] < 0
        or not nonblank(target.get("text"))
    ):
        raise ValueError("invalid ARC challenge target")

    return hashlib.sha256(raw).hexdigest(), challenge


def evidence_reference(path):
    if not path.is_file():
        raise ValueError(f"evidence is not a regular file: {path}")

    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as evidence:
        for chunk in iter(lambda: evidence.read(65536), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"path": str(path), "sha256": digest.hexdigest(), "size_bytes": size}


def build_evidence_response(challenge_path, responder_role, response, evidence_paths):
    if responder_role not in ROLES:
        raise ValueError("unknown ARC responder role")
    if not nonblank(response):
        raise ValueError("response must be nonblank")
    if not evidence_paths:
        raise ValueError("provide at least one evidence file")

    challenge_sha256, challenge = read_challenge(challenge_path)
    return {
        "kind": "arc_challenge_evidence_response",
        "schema_version": 1,
        "proposal_sha256": challenge["proposal_sha256"],
        "challenge_sha256": challenge_sha256,
        "responder_role": responder_role,
        "response": response.strip(),
        "evidence": [evidence_reference(path) for path in evidence_paths],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("challenge", type=Path)
    parser.add_argument("--responder", required=True, choices=ROLES, help="caller-supplied ARC role")
    parser.add_argument("--response", required=True)
    parser.add_argument("--evidence", required=True, type=Path, action="append")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        artifact = build_evidence_response(args.challenge, args.responder, args.response, args.evidence)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(artifact, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
