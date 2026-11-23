"""Execute independent first-pass architecture reviews through real model calls.

No hidden multi-agent capability: each review is a separate invocation with isolated
messages. The observed count links configured endpoints to provider-reported
model labels. A system fingerprint can describe backend configuration, while
the underlying model weights remain unverified.
"""
import argparse
import hashlib
import json
import os
import re
import time
from urllib.parse import urlsplit
from pathlib import Path
from warwagon.model import ChatModel

ROLES={
 "agent-intelligence":"Assess cognitive architectures, multi-agent autonomy and planning alternatives.",
 "distributed-systems":"Assess causal ordering, idempotency, replay and crash consistency.",
 "knowledge-data":"Assess source-of-truth, graph ontology, evidence and provenance.",
 "security-research":"Assess realism, scope of local fixtures, evidence and validation.",
 "evaluation-science":"Assess confounders, statistical validity, held-out tests and measurement.",
 "model-inference":"Assess context engineering, routing, provider parity and inference efficiency.",
 "developer-experience":"Assess interface stability, interoperability and contributor experience.",
 "adversarial-review":"Try to falsify key assumptions and reveal dangerous failure modes.",
 "research-skeptic":"Identify unsupported factual claims, absent evidence and alternatives."
}
VERDICTS = {"support", "conditional", "needs-research", "reject"}
REVIEW_LISTS = ("strengths", "blockers", "experiments", "unknowns")


def validate_response(output):
    if not isinstance(output, str):
        raise ValueError("review content must be a JSON string")
    output = output.strip()
    fence = re.fullmatch(
        r"```(?:json)?[^\S\r\n]*\r?\n(.*?)\r?\n```", output, re.DOTALL | re.IGNORECASE
    )
    if fence:
        output = fence.group(1)
    try:
        result = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError("review content is not valid JSON") from exc
    if not isinstance(result, dict) or set(result) != {"verdict", *REVIEW_LISTS}:
        raise ValueError("review must contain exactly the five requested fields")
    verdict = result["verdict"]
    if not isinstance(verdict, str) or verdict not in VERDICTS:
        raise ValueError("unsupported review verdict")
    for field in REVIEW_LISTS:
        items = result[field]
        if not isinstance(items, list) or any(
            not isinstance(item, str) or not item.strip() for item in items
        ):
            raise ValueError(f"{field} must be an array of nonblank strings")
    return result


def reported_label(response, field):
    label = response.get(field)
    if isinstance(label, str):
        return label.strip() or None
    return None


def review(model,role,proposal):
    system=("You are the "+role+" reviewer. "+ROLES[role]+
      " Give a rigorous independent FIRST-PASS critique. Never assume other reviewers agree. "
      "Distinguish evidence from speculation. Return JSON object with keys verdict, strengths, blockers, experiments, unknowns. "
      "Use verdict support, conditional, needs-research or reject.")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": proposal}]
    record = {
        "role": role,
        "model": model.model,
        "provider_host": urlsplit(model.base_url).hostname,
        "endpoint_sha256": hashlib.sha256(model.base_url.encode()).hexdigest(),
        "system_prompt_sha256": hashlib.sha256(system.encode()).hexdigest(),
        "independent_context": True,
        "response_model": None,
        "response_system_fingerprint": None,
    }
    started = time.monotonic()
    try:
        response = model.complete(messages)
    except (OSError, ValueError) as exc:
        record.update(status="request_failed", error_type=type(exc).__name__)
        if hasattr(exc, "code"):
            record["http_status"] = exc.code
    else:
        record.update(
            response_model=reported_label(response, "model"),
            response_system_fingerprint=reported_label(response, "system_fingerprint"),
            response_id=response.get("id"),
            usage=response.get("usage", {}),
        )
        try:
            choice = response["choices"][0]
            record["finish_reason"] = choice.get("finish_reason")
            record["response"] = choice["message"].get("content")
        except (KeyError, IndexError, TypeError, AttributeError):
            record.update(status="invalid_response", error="malformed completion envelope")
        else:
            try:
                if record["finish_reason"] not in (None, "stop"):
                    raise ValueError("completion did not finish normally")
                record["review"] = validate_response(record["response"])
            except ValueError as exc:
                record.update(status="invalid_response", error=str(exc))
            else:
                record["status"] = "valid"
    record["elapsed_seconds"] = round(time.monotonic() - started, 6)
    return record


def retry_source(source, proposal_sha256, role):
    source_bytes = source.read_bytes()
    payload = json.loads(source_bytes)
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 1
        or payload.get("kind") != "real_model_first_pass_reviews"
        or payload.get("proposal_sha256") != proposal_sha256
    ):
        raise ValueError("retry requires an ARC v1 artifact for the same proposal bytes")
    reviews = payload.get("reviews")
    if not isinstance(reviews, list):
        raise ValueError("retry source has no review records")
    matches = [record for record in reviews if isinstance(record, dict) and record.get("role") == role]
    if len(matches) != 1 or matches[0].get("status") not in ("request_failed", "invalid_response"):
        raise ValueError(f"retry source must contain exactly one unsuccessful review for {role}")
    return {
        "artifact_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "review": matches[0],
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--proposal",type=Path,default=Path("docs/rfcs/RFC-0001-planner-research-v2.md"))
    ap.add_argument("--model",default=os.getenv("WW_MODEL",""))
    ap.add_argument("--base-url",default=os.getenv("WW_MODEL_BASE_URL","http://127.0.0.1:11434/v1"))
    ap.add_argument("--output",type=Path,default=Path("artifacts/arc-review.json"))
    ap.add_argument("--reviewers-file",type=Path,help="JSON map of role to {model,base_url}; permits distinct model/provider reviewers")
    ap.add_argument("--retry-from", type=Path, help="prior ARC artifact containing a failed review")
    ap.add_argument("--retry-role", choices=ROLES, help="run only this unsuccessful reviewer")
    args = ap.parse_args()
    if bool(args.retry_from) != bool(args.retry_role):
        ap.error("--retry-from and --retry-role must be used together")
    if args.retry_from and (args.output.resolve() == args.retry_from.resolve() or args.output.exists()):
        ap.error("retry output must be a new artifact; specify an unused --output path")
    if not args.model and not args.reviewers_file: ap.error("provide --model or --reviewers-file")
    try:
        proposal_bytes = args.proposal.read_bytes()
        proposal = proposal_bytes.decode("utf-8")
        proposal_sha256 = hashlib.sha256(proposal_bytes).hexdigest()
        previous = (
            retry_source(args.retry_from, proposal_sha256, args.retry_role)
            if args.retry_from else None
        )
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    if len(proposal) > 120000:
        ap.error("proposal exceeds 120k characters; freeze a smaller packet")
    roles = (args.retry_role,) if previous is not None else tuple(ROLES)
    try:
        if args.reviewers_file:
            profiles = json.loads(args.reviewers_file.read_text(encoding="utf-8"))
            if not isinstance(profiles, dict) or set(profiles) != set(ROLES):
                raise ValueError("reviewers-file must contain all nine known roles")
        else:
            profiles = {role: {"model": args.model, "base_url": args.base_url} for role in ROLES}
        reviewers = {}
        for role in roles:
            profile = profiles[role]
            if not isinstance(profile, dict) or not all(
                isinstance(profile.get(key), str) and profile[key].strip()
                for key in ("base_url", "model")
            ):
                raise ValueError(f"{role} requires nonblank base_url and model strings")
            key_env = profile.get("api_key_env")
            if key_env is not None:
                if not isinstance(key_env, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key_env):
                    raise ValueError(f"{role} api_key_env must be an environment variable name")
                api_key = os.getenv(key_env)
                if not api_key:
                    raise ValueError(f"{role} environment variable {key_env} is unset or empty")
            else:
                api_key = "" if args.reviewers_file else None
            reviewers[role] = ChatModel(profile["base_url"], profile["model"], api_key=api_key)
    except (OSError, ValueError) as exc:
        ap.error(str(exc))

    reviews = []
    for role in roles:
        record = review(reviewers[role], role, proposal)
        reviews.append(record)
        print(role, record["status"], flush=True)

    valid_reviews = [item for item in reviews if item["status"] == "valid"]
    verdict_roles = {verdict: [] for verdict in sorted(VERDICTS)}
    for item in valid_reviews:
        verdict_roles[item["review"]["verdict"]].append(item["role"])
    observed_endpoint_models = {
        (item["endpoint_sha256"], item["response_model"])
        for item in reviews if item["response_model"] is not None
    }
    payload = {
        "kind": "real_model_first_pass_reviews",
        "schema_version": 1,
        "proposal": str(args.proposal),
        "proposal_sha256": proposal_sha256,
        "reviewer_model_count": len({model.model for model in reviewers.values()}),
        "configured_endpoint_model_count": len({(m.base_url, m.model) for m in reviewers.values()}),
        "observed_endpoint_model_count": len(observed_endpoint_models),
        "roles_without_reported_model": [
            item["role"] for item in reviews if item["response_model"] is None
        ],
        "model_weight_identity_verified": False,
        "model": args.model,
        "warning": (
            "First-pass calls use isolated contexts. Configured and provider-reported "
            "identities do not establish model weight independence or maintainer approval."
        ),
        "valid_review_count": len(valid_reviews),
        "verdict_roles": verdict_roles,
        "reviews": reviews,
    }
    if previous is not None:
        payload["retry_of"] = previous
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x" if previous is not None else "w", encoding="utf-8") as output:
        json.dump(payload, output, indent=2)
        output.write("\n")
    print("Saved", args.output)
    return 0 if len(valid_reviews) == len(roles) else 1
if __name__=="__main__":
    raise SystemExit(main())
