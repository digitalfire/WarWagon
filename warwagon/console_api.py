"""Read-only, loopback WarWagon API for existing signed/digest-bound run artifacts.

This is a *recorded artifact replay*, not a live engagement controller.
No target requests, model inference, remote bind or filesystem browsing.
"""
from __future__ import annotations
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from warwagon.engagement_store import DEFAULT_PATH, EngagementLedger
from warwagon.engagement_api import serve_engagement_get

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = REPO_ROOT / "console" / "demo"
RUNS = {
    "confirmation": ("trace.json", "model-verdict.json", "negative-verdict.json"),
    "checkpoint": (
        "runs/checkpoint-trace.json", "runs/checkpoint-model-verdict.json",
        "runs/checkpoint-negative-verdict.json",
    ),
}
HEX = re.compile(r"^[0-9a-f]{64}$")

def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def load_bundle(root: Path, name: str) -> dict:
    if name not in RUNS:
        raise KeyError("run not found")
    paths = RUNS[name]
    raw = [(root / relative).read_bytes() for relative in paths]
    trace = json.loads(raw[0].decode("utf-8"))
    reports = [json.loads(chunk.decode("utf-8")) for chunk in raw[1:]]
    trace_sha = hashlib.sha256(raw[0]).hexdigest()
    if trace.get("kind") != "benign_head_evidence_run" or trace.get("schema_version") != 1:
        raise ValueError("invalid trace kind")
    observation = trace.get("observation")
    if not isinstance(observation, dict):
        raise ValueError("missing observation")
    observation_sha = trace.get("observation_sha256")
    if not isinstance(observation_sha, str) or not HEX.fullmatch(observation_sha):
        raise ValueError("invalid observation digest")
    if canonical_digest(observation) != observation_sha:
        raise ValueError("observation digest mismatch")
    for report in reports:
        if (report.get("kind") != "benign_head_evidence_verification"
            or report.get("schema_version") != 1
            or report.get("trace_sha256") != trace_sha
            or report.get("claim_source") not in ("model", "supplied")
            or type(report.get("verified")) is not bool):
            raise ValueError("verifier trace binding or schema invalid")
    claim = trace.get("claim")
    if not isinstance(claim, dict) or claim.get("observation_sha256") != observation_sha:
        raise ValueError("model claim not bound to observation")
    return {"id": name, "source": "recorded", "schemaVersion": 1,
            "traceSha256": trace_sha, "observationSha256": observation_sha,
            "trace": trace, "verifications": reports}

def events(bundle):
    """Deterministic history based only on fields actually present in the artifact."""
    trace = bundle["trace"]
    obs = trace["observation"]
    base = [
        {"id": "001", "kind": "tool_call", "summary": "Recorded model tool call",
         "tool": trace["tool_call"], "usage": trace.get("tool_invocation", {}).get("usage")},
        {"id": "002", "kind": "observation", "summary": "Recorded HTTP response",
         "observation": obs, "sha256": bundle["observationSha256"]},
        {"id": "003", "kind": "claim", "summary": "Model-reported HTTP status",
         "claim": trace["claim"], "usage": trace.get("claim_invocation", {}).get("usage")},
    ]
    for i, report in enumerate(bundle["verifications"], start=4):
        base.append({"id": f"{i:03}", "kind": "verification",
                     "summary": "Recorded " + report["claim_source"] + " verifier disposition",
                     "verification": report})
    return base

def summarize(bundle):
    trace = bundle["trace"]
    usages = [trace.get("tool_invocation", {}).get("usage"),
              trace.get("claim_invocation", {}).get("usage")]
    tokens = (sum(u["total_tokens"] for u in usages)
              if all(isinstance(u, dict) and type(u.get("total_tokens")) is int for u in usages)
              else None)
    model_reports = [r for r in bundle["verifications"] if r["claim_source"] == "model"]
    status = ("verified" if len(model_reports) == 1 and model_reports[0]["verified"]
              else "rejected" if len(model_reports) == 1 and not model_reports[0]["verified"]
              else "unverified")
    return {"id": bundle["id"], "source": "recorded", "model": trace["model"],
            "target": trace["observation"].get("url"), "observedStatus": trace["observation"].get("status_code"),
            "observedAt": trace["observation"].get("timestamp_utc"),
            "modelCalls": sum(1 for u in usages if u is not None), "tokens": tokens,
            "modelVerdict": status, "traceSha256": bundle["traceSha256"]}

def make_handler(root: Path, engagement_db: Path | None = None, *, stream_seconds: float = 20.0):
    ledger = EngagementLedger(engagement_db) if engagement_db is not None else None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def write_json(self, code, data):
            body = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if ledger is not None and serve_engagement_get(self, ledger, stream_seconds=stream_seconds):
                return
            path = urlsplit(self.path)
            if path.query or path.fragment:
                self.write_json(400, {"error": "query_not_supported"})
                return
            if path.path == "/api/v1/health":
                self.write_json(200, {"ok": True, "mode": "read_only_recorded_replay"})
                return
            if path.path == "/api/v1/runs":
                try:
                    bundles = [load_bundle(root, name) for name in RUNS]
                    self.write_json(200, {"schemaVersion": 1, "source": "recorded",
                                          "runs": [summarize(b) for b in bundles]})
                except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                    self.write_json(422, {"error": "artifact_integrity_failure"})
                return
            match = re.fullmatch(r"/api/v1/runs/(confirmation|checkpoint)(/events)?", path.path)
            if not match:
                self.write_json(404, {"error": "not_found"})
                return
            try:
                bundle = load_bundle(root, match.group(1))
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                self.write_json(422, {"error": "artifact_integrity_failure"})
                return
            if not match.group(2):
                self.write_json(200, {**bundle, "events": events(bundle)})
                return
            # One finite, deterministic replay from disk, not a live stream.
            payload = "".join(
                f"id: {event['id']}\nevent: record\ndata: {json.dumps(event, separators=(',', ':'))}\n\n"
                for event in events(bundle)
            ) + 'event: replay_complete\ndata: {"source":"recorded"}\n\n'
            body = payload.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self.write_json(405, {"error": "read_only"})

    return Handler

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--engagement-db", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    with ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.fixture_dir, engagement_db=args.engagement_db)) as server:
        print(f"Read-only recorded-run API: http://127.0.0.1:{server.server_port}/api/v1/runs", flush=True)
        server.serve_forever()

if __name__ == "__main__":
    main()
