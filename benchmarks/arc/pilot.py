"""Run a serial, local ARC comparison and emit an assessor packet."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import secrets

from warwagon.arc import review
from warwagon.arc_scorecard import read_checklist
from warwagon.model import ChatModel


ENDPOINT = "http://127.0.0.1:11434/v1"


def write_json(path, payload):
    with path.open("x", encoding="utf-8") as output:
        json.dump(payload, output, indent=2)
        output.write("\n")


def run_pilot(case, models, output, seed=None):
    models = [model.strip() for model in models]
    if len(models) < 2 or not all(models) or len(set(models)) != len(models):
        raise ValueError("provide at least two distinct, nonblank model tags")
    raw = (case / "proposal.md").read_bytes()
    proposal_digest = hashlib.sha256(raw).hexdigest()
    checklist_digest, checklist, criteria = read_checklist(case / "checklist.json")
    if checklist["proposal_sha256"] != proposal_digest:
        raise ValueError("proposal digest does not match the frozen checklist")
    proposal = raw.decode("utf-8")
    if len(proposal) > 120000:
        raise ValueError("proposal exceeds the ARC 120k-character limit")

    role = checklist["role"]
    order_seed = seed if seed is not None else secrets.randbits(64)
    random.Random(order_seed).shuffle(models)
    output.mkdir(parents=True, exist_ok=False)

    records = []
    blinded_reviews = []
    for index, model in enumerate(models, start=1):
        candidate_id = f"review-{index}"
        client = ChatModel(ENDPOINT, model, api_key="")
        attempt = review(client, role, proposal)
        records.append({"candidate": candidate_id, "attempt": attempt})
        if attempt["status"] == "valid":
            blinded_reviews.append({"candidate": candidate_id, "review": attempt["review"]})

    common = {
        "schema_version": 1,
        "role": role,
        "proposal_sha256": proposal_digest,
        "checklist_sha256": checklist_digest,
    }
    write_json(output / "operator-run.json", {
        **common,
        "kind": "arc_pilot_operator_run",
        "order_seed": order_seed,
        "records": records,
    })
    write_json(output / "assessment-packet.json", {
        **common,
        "kind": "arc_pilot_assessment_packet",
        "checklist": [{"id": key, "criterion": value} for key, value in criteria.items()],
        "reviews": blinded_reviews,
    })
    return len(blinded_reviews)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path, help="directory with proposal.md and checklist.json")
    parser.add_argument("--model", required=True, action="append", help="installed local tag; repeat at least twice")
    parser.add_argument("--output", required=True, type=Path, help="new output directory")
    parser.add_argument("--seed", type=int, help="optional reproducible call order, recorded privately")
    args = parser.parse_args()
    try:
        valid_count = run_pilot(args.case, args.model, args.output, args.seed)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")
    print(f"{valid_count}/{len(args.model)} valid reviews")
    return 0 if valid_count == len(args.model) else 1


if __name__ == "__main__":
    raise SystemExit(main())
