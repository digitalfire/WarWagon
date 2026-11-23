"""Build an evidence-linked ARC report from a first pass and ordered retries."""

import argparse
import hashlib
import json
from pathlib import Path

from warwagon.arc import ROLES, VERDICTS, validate_response


FAILURES = ("request_failed", "invalid_response")


def read_artifact(path):
    raw = path.read_bytes()
    artifact = json.loads(raw)
    if (
        not isinstance(artifact, dict)
        or artifact.get("kind") != "real_model_first_pass_reviews"
        or artifact.get("schema_version") != 1
        or not isinstance(artifact.get("reviews"), list)
        or not isinstance(artifact.get("proposal_sha256"), str)
    ):
        raise ValueError(f"{path}: expected an ARC v1 review artifact")
    return hashlib.sha256(raw).hexdigest(), artifact


def record_attempt(attempts, digest, record):
    status = record.get("status")
    if status == "valid":
        validate_response(json.dumps(record.get("review")))
    elif status not in FAILURES:
        raise ValueError("invalid ARC review status")
    attempts.append({"artifact_sha256": digest, "record": record})


def build_report(first_pass, retries):
    root_digest, root = read_artifact(first_pass)
    proposal_digest = root["proposal_sha256"]
    reviews = root["reviews"]
    if (
        "retry_of" in root
        or len(reviews) != len(ROLES)
        or any(not isinstance(record, dict) or record.get("role") not in tuple(ROLES) for record in reviews)
        or {record["role"] for record in reviews} != set(ROLES)
    ):
        raise ValueError("first pass must contain exactly one review for every ARC role")

    attempts_by_role = {role: [] for role in ROLES}
    for record in reviews:
        record_attempt(attempts_by_role[record["role"]], root_digest, record)

    for path in retries:
        digest, retry = read_artifact(path)
        records = retry["reviews"]
        if retry["proposal_sha256"] != proposal_digest:
            raise ValueError(f"{path}: retry uses different proposal bytes")
        if len(records) != 1 or not isinstance(records[0], dict):
            raise ValueError(f"{path}: retry must contain one review")
        record = records[0]
        role = record.get("role")
        if role not in tuple(ROLES):
            raise ValueError(f"{path}: unknown reviewer role")
        attempts = attempts_by_role[role]
        parent = attempts[-1]
        expected_link = {"artifact_sha256": parent["artifact_sha256"], "review": parent["record"]}
        if retry.get("retry_of") != expected_link or parent["record"]["status"] not in FAILURES:
            raise ValueError(f"{path}: retry must reference the latest unsuccessful attempt for {role}")
        record_attempt(attempts, digest, record)

    verdict_roles = {verdict: [] for verdict in sorted(VERDICTS)}
    unresolved = []
    for role, attempts in attempts_by_role.items():
        record = attempts[-1]["record"]
        if record["status"] == "valid":
            verdict_roles[record["review"]["verdict"]].append(role)
        else:
            unresolved.append(role)

    return {
        "kind": "arc_first_pass_report",
        "schema_version": 1,
        "proposal_sha256": proposal_digest,
        "first_pass_sha256": root_digest,
        "unresolved_roles": unresolved,
        "verdict_roles": verdict_roles,
        "verdicts_differ": sum(bool(roles) for roles in verdict_roles.values()) > 1,
        "attempts_by_role": attempts_by_role,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first_pass", type=Path)
    parser.add_argument("--retry", action="append", type=Path, default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = build_report(args.first_pass, args.retry)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
