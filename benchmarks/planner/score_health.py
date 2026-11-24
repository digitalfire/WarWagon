"""Score benign loopback service status claims using separate probe traces and labels."""

import argparse
from hashlib import sha256
import json
from pathlib import Path


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _artifact(path, kind):
    raw = path.read_bytes()
    data = json.loads(raw, object_pairs_hook=_unique_object)
    if (
        not isinstance(data, dict)
        or data.get("kind") != kind
        or type(data.get("schema_version")) is not int
        or data["schema_version"] != 1
    ):
        raise ValueError(f"{path}: expected a v1 {kind} artifact")
    return data, sha256(raw).hexdigest()


def _status(value):
    return type(value) is int and 100 <= value <= 599


def _valid_observation(observation, port):
    return not (
        not isinstance(observation, dict)
        or observation.get("kind") != "local_http_connectivity_trace"
        or type(observation.get("schema_version")) is not int
        or observation["schema_version"] != 1
        or observation.get("method") != "HEAD"
        or observation.get("url") != f"http://127.0.0.1:{port}/"
        or observation.get("remote_ip") != "127.0.0.1"
        or observation.get("remote_port") != port
        or type(observation.get("redirects_followed")) is not int
        or observation["redirects_followed"] != 0
        or "error_type" not in observation
        or observation["error_type"] is not None
        or not _status(observation.get("status_code"))
    )


def _verdict(port, claim, observations):
    if claim is None:
        return "missing_claim"
    index = claim.get("observation_index")
    if type(index) is not int or not 0 <= index < len(observations):
        return "missing_observation"

    observation = observations[index]
    if not _valid_observation(observation, port):
        return "invalid_observation"
    if not _status(claim.get("status_code")) or claim["status_code"] != observation["status_code"]:
        return "unsupported_claim"
    return "verified"


def score(case_path, evidence_path, claim_path, label_path):
    case, case_digest = _artifact(case_path, "planner_health_case")
    evidence, evidence_digest = _artifact(evidence_path, "planner_health_evidence")
    submission, claim_digest = _artifact(claim_path, "planner_health_submission")
    labels, label_digest = _artifact(label_path, "planner_health_labels")

    for artifact in (evidence, submission, labels):
        if artifact.get("case_sha256") != case_digest:
            raise ValueError("case digest mismatch")
    if submission.get("evidence_sha256") != evidence_digest:
        raise ValueError("evidence digest mismatch")

    services = case.get("services")
    if not isinstance(services, dict) or not services:
        raise ValueError("case services must be a nonempty object")
    if any(
        not service_id.strip() or type(port) is not int or not 1 <= port <= 65535
        for service_id, port in services.items()
    ) or len(set(services.values())) != len(services):
        raise ValueError("case requires nonblank service IDs with distinct valid ports")

    expected = labels.get("status_by_service")
    if (
        not isinstance(expected, dict)
        or expected.keys() != services.keys()
        or not all(_status(status) for status in expected.values())
    ):
        raise ValueError("labels must give one HTTP status per case service")

    observations = evidence.get("observations")
    claims = submission.get("claims")
    if not isinstance(observations, list) or not isinstance(claims, dict):
        raise ValueError("evidence observations must be a list and claims must be an object")
    if any(not isinstance(claim, dict) for claim in claims.values()):
        raise ValueError("each claim must be an object")

    results = {
        service_id: _verdict(port, claims.get(service_id), observations)
        for service_id, port in services.items()
    }
    for service_id, port in services.items():
        if any(
            _valid_observation(observation, port) and observation["status_code"] != expected[service_id]
            for observation in observations
        ):
            results[service_id] = "fixture_mismatch"
    results.update({service_id: "unexpected_service" for service_id in claims.keys() - services.keys()})
    verified = sum(verdict == "verified" for verdict in results.values())
    scorable = "fixture_mismatch" not in results.values()
    return {
        "kind": "planner_health_score",
        "schema_version": 1,
        "case_sha256": case_digest,
        "evidence_sha256": evidence_digest,
        "submission_sha256": claim_digest,
        "labels_sha256": label_digest,
        "services": dict(sorted(results.items())),
        "verified": verified,
        "precision": verified / len(claims) if scorable and claims else None,
        "recall": verified / len(services) if scorable else None,
        "scorable": scorable,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = score(args.case, args.evidence, args.submission, args.labels)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
