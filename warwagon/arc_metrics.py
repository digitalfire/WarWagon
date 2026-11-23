"""Summarize recorded ARC attempts offline, including retries and failures.

Run python -m warwagon.arc_metrics <ARC report.json> to write JSON to stdout.
Metric totals cover reported values only. A null total means no attempt
reported a usable value. Timings are summed attempt durations, not wall-clock
runtime. A failed attempt may not have reached the provider.

Use --by-configured-model to break down attempts by recorded configuration
label. A null configured model identifies attempts without a usable label.
A configuration label does not establish provider or model identity.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from warwagon.arc import ROLES
from warwagon.arc_report import FAILURES


STATUSES = ("valid", *FAILURES)
TOKEN_FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")


def report_attempts(report):
    if (
        not isinstance(report, dict)
        or report.get("kind") != "arc_first_pass_report"
        or type(report.get("schema_version")) is not int
        or report["schema_version"] != 1
        or not isinstance(report.get("proposal_sha256"), str)
        or not isinstance(report.get("first_pass_sha256"), str)
        or not isinstance(report.get("attempts_by_role"), dict)
        or set(report["attempts_by_role"]) != set(ROLES)
    ):
        raise ValueError("expected an ARC v1 first-pass report")

    for role in ROLES:
        attempts = report["attempts_by_role"][role]
        if not isinstance(attempts, list) or not attempts:
            raise ValueError(f"{role}: expected at least one recorded attempt")
        previous = None
        seen = set()
        for index, attempt in enumerate(attempts):
            record = attempt.get("record") if isinstance(attempt, dict) else None
            if not isinstance(record, dict) or record.get("role") != role or record.get("status") not in STATUSES:
                raise ValueError(f"{role}: invalid attempt record at index {index}")
            digest = attempt.get("artifact_sha256")
            if not isinstance(digest, str) or not digest or digest in seen:
                raise ValueError(f"{role}: missing or duplicate attempt digest at index {index}")
            if index == 0 and digest != report["first_pass_sha256"]:
                raise ValueError(f"{role}: first attempt does not match the first-pass digest")
            if index and previous not in FAILURES:
                raise ValueError(f"{role}: retry follows a successful attempt")
            previous = record["status"]
            seen.add(digest)
            yield index, record


def token_value(value):
    if type(value) is int and value >= 0:
        return value
    return None


def elapsed_value(value):
    if type(value) not in (int, float):
        return None
    try:
        if math.isfinite(value) and value >= 0:
            return value
    except OverflowError:
        pass
    return None


def summarize(values, attempt_count, *, sum_values=sum):
    try:
        total = sum_values(values) if values else None
    except OverflowError as exc:
        raise ValueError("recorded elapsed durations exceed the numeric range") from exc
    return {
        "observed_total": total,
        "reported_attempt_count": len(values),
        "missing_attempt_count": attempt_count - len(values),
    }


def summarize_attempts(attempts):
    status_counts = dict.fromkeys(STATUSES, 0)
    tokens = {field: [] for field in TOKEN_FIELDS}
    elapsed = []
    retry_count = 0

    for index, record in attempts:
        status_counts[record["status"]] += 1
        retry_count += index > 0
        usage = record.get("usage")
        if isinstance(usage, dict):
            for field, values in tokens.items():
                value = token_value(usage.get(field))
                if value is not None:
                    values.append(value)
        duration = elapsed_value(record.get("elapsed_seconds"))
        if duration is not None:
            elapsed.append(duration)

    attempt_count = sum(status_counts.values())
    return {
        "invocation_attempt_count": attempt_count,
        "retry_attempt_count": retry_count,
        "attempts_by_status": status_counts,
        "tokens": {field: summarize(values, attempt_count) for field, values in tokens.items()},
        "elapsed_seconds": summarize(elapsed, attempt_count, sum_values=math.fsum),
    }


def build_metrics(report_path, *, by_configured_model=False):
    raw = report_path.read_bytes()
    report = json.loads(raw)
    attempts = list(report_attempts(report))
    metrics = {
        "kind": "arc_attempt_metrics",
        "schema_version": 1,
        "report_sha256": hashlib.sha256(raw).hexdigest(),
        "proposal_sha256": report["proposal_sha256"],
        **summarize_attempts(attempts),
    }
    if by_configured_model:
        groups = {}
        for index, record in attempts:
            label = record.get("model")
            model = label if isinstance(label, str) and label.strip() else None
            groups.setdefault(model, []).append((index, record))
        metrics["by_configured_model"] = [
            {"configured_model": model, **summarize_attempts(group)}
            for model, group in groups.items()
        ]
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="ARC v1 first-pass report with attempt history")
    parser.add_argument(
        "--by-configured-model", action="store_true",
        help="include attempt metrics grouped by recorded configured model label",
    )
    args = parser.parse_args()
    try:
        metrics = build_metrics(args.report, by_configured_model=args.by_configured_model)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
